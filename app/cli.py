import argparse
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import load_user_config, SCRAPE_DAYS_BACK, MAX_RESULTS_PER_CREATOR, get_secrets_count
from src.database import get_connection, init_db, get_recent_reels_for_analysis
from src.scrapers import apify_scraper
from src.scrapers.cache_aware_scraper import scrape_creator_incremental, estimate_cost_savings
from src.extractors import topic_extractor, pinned_filter
from src.scoring import trend_ranker
from src.logger import log_event, clear_logs

def refresh_trends():
    """Execute the full trend discovery pipeline with cache-aware scraping."""
    # 1. Initialize Database
    init_db()

    config = load_user_config()
    creators = [c for c in config.get("creators", []) if c.get("is_active", True)]

    if not creators:
        print("No active creators found in config.json.")
        return

    clear_logs()
    s_count = get_secrets_count()
    log_event(f"Starting Trend Discovery ({s_count} secrets found in system)")

    # Show cost estimate
    cost_info = estimate_cost_savings(len(creators), avg_posts_per_week=2)
    print(f"💰 COST ESTIMATE:")
    print(f"   Without caching: ${cost_info['without_caching']['cost_per_month']:.2f}/month")
    print(f"   With caching:    ${cost_info['with_caching']['cost_per_month']:.2f}/month")
    print(f"   💚 Savings:      ${cost_info['savings']['amount']:.2f} ({cost_info['savings']['percent']:.0f}%)\n")

    conn = get_connection()
    cursor = conn.cursor()

    new_posts_count = 0

    # 2. Scrape Each Creator (PARALLEL + CACHE-AWARE)
    log_event("Starting Parallel + Incremental Scraping...")

    def scrape_single_creator(creator):
        """Scrape a single creator (for parallel execution)"""
        username = creator["username"]
        try:
            # 🚀 Use cache-aware scraping (saves 80-90% API costs!)
            filtered_reels = scrape_creator_incremental(
                username,
                max_results=MAX_RESULTS_PER_CREATOR,
                days_back=SCRAPE_DAYS_BACK
            )
            return {
                "username": username,
                "display_name": creator.get("display_name"),
                "reels": filtered_reels,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "username": username,
                "display_name": creator.get("display_name"),
                "reels": [],
                "success": False,
                "error": str(e)
            }

    # Scrape creators in parallel (max 3 at a time to avoid rate limits)
    results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_creator = {executor.submit(scrape_single_creator, creator): creator for creator in creators}

        for future in as_completed(future_to_creator):
            result = future.result()
            results.append(result)

            # Log result
            if result["success"]:
                log_event(f"✅ @{result['username']}: {len(result['reels'])} new reels")
            else:
                log_event(f"❌ @{result['username']}: {result['error']}", level="ERROR")

    # Save all results to database
    print(f"\n💾 Saving to database...")
    for result in results:
        if not result["success"]:
            continue

        username = result["username"]

        # Check if creator exists in DB
        cursor.execute("SELECT id FROM creators WHERE username = ?", (username,))
        db_result = cursor.fetchone()

        if db_result:
            creator_id = db_result["id"]
        else:
            # Add creator to DB
            cursor.execute("INSERT INTO creators (username, display_name) VALUES (?, ?)",
                           (username, result["display_name"]))
            creator_id = cursor.lastrowid
            conn.commit()

        # Save new reels to DB
        for reel in result["reels"]:
            reel["creator_id"] = creator_id
            new_posts_count += 1

            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO reels
                    (creator_id, instagram_id, caption, likes, comments, views, post_date, post_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    creator_id,
                    reel.get("id"),
                    reel.get("caption"),
                    reel.get("likes", 0),
                    reel.get("comments", 0),
                    reel.get("views", 0),
                    reel.get("timestamp"),
                    reel.get("url")
                ))
            except Exception as e:
                print(f"  ⚠️  Error saving reel: {e}")

        conn.commit()

    log_event(f"Scraped {new_posts_count} NEW posts. Estimated cost: ${new_posts_count * 0.0026:.3f}")

    # 3. Get all recent reels from cache for analysis (last 7 days)
    print(f"{'='*60}")
    print(f"🧠 ANALYZING TRENDS (from cache)")
    print(f"{'='*60}\n")

    all_reels = get_recent_reels_for_analysis(days_back=7)
    
    log_event(f"Analyzing {len(all_reels)} reels for topics...")
    topic_map = topic_extractor.cluster_topics(all_reels)
    log_event(f"Found {len(topic_map.keys())} unique topics.")
    
    # Save topics to DB
    for topic_name, reels in topic_map.items():
        for reel in reels:
            # Need to get reel ID from database
            cursor.execute("SELECT id FROM reels WHERE instagram_id = ?", (reel.get("id"),))
            reel_row = cursor.fetchone()
            if reel_row:
                cursor.execute("INSERT INTO topics (topic_name, reel_id) VALUES (?, ?)", 
                               (topic_name, reel_row["id"]))
    conn.commit()
    
    # 4. Scoring and Ranking
    print("\n--- Ranking Trends ---")
    top_trends = trend_ranker.rank_topics(topic_map)
    
    # Save Scores to DB
    for trend in top_trends:
        try:
             cursor.execute("""
                INSERT OR REPLACE INTO topic_scores 
                (topic_name, score, engagement_rate, creator_count, post_count, avg_likes, avg_views)
                VALUES (?, ?, ?, ?, ?, ?, ?)
             """, (
                 trend["topic"], trend["score"], trend["engagement_rate"],
                 trend["creator_count"], trend["post_count"], 
                 trend["avg_likes"], trend["avg_views"]
             ))
        except Exception as e:
             print(f"Error saving scores: {e}")
    conn.commit()
    conn.close()
    
    # 5. Display Results with Insights
    print(f"\n{'='*60}")
    print(f"🔥 TOP TRENDING TOPICS FOR YOUR NEXT REEL")
    print(f"{'='*60}\n")

    if not top_trends:
        print("❌ No trending topics found.")
        return

    for i, trend in enumerate(top_trends[:5], 1):  # Show top 5
        print(f"{i}. {trend['topic']}")
        print(f"   📊 Score: {trend['score']:.1f}/100")
        print(f"   👥 {trend['creator_count']} creators | 🎬 {trend['post_count']} reels")
        print(f"   💬 {int(trend['avg_likes']):,} avg likes | 👁️ {int(trend['avg_views']):,} avg views")

    print(f"\n💡 RECOMMENDATION:")
    if top_trends:
        best_topic = top_trends[0]
        print(f"   Create a reel about '{best_topic['topic']}'")
    print()

def list_creators():
    """List all creators in config.json."""
    config = load_user_config()
    print("Creators List:")
    for c in config.get("creators", []):
        status = "Active" if c.get("is_active", True) else "Inactive"
        print(f"- @{c['username']} ({c.get('display_name')}) [{status}]")

def main():
    parser = argparse.ArgumentParser(description="Finance Trend discovery tool CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    subparsers.add_parser("refresh", help="Discovery new trends (scrape, extract, rank)")
    subparsers.add_parser("creators", help="List all tracked creators")
    
    args = parser.parse_args()
    
    if args.command == "refresh":
        refresh_trends()
    elif args.command == "creators":
        list_creators()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
