import argparse
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config import load_user_config, SCRAPE_DAYS_BACK, MAX_RESULTS_PER_CREATOR, get_apify_key
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
    
    # DEBUG LOGS FOR UI
    log_event(f"Starting Trend Discovery...")
    
    api_key = get_apify_key()
    log_event(f"[DEBUG] APIFY Key Object exists: {api_key is not None}")
    log_event(f"[DEBUG] APIFY Key Length: {len(str(api_key)) if api_key else 0}")
    
    try:
        import streamlit as st
        log_event(f"[DEBUG] Streamlit Secrets Available: {hasattr(st, 'secrets')}")
        log_event(f"[DEBUG] Keys in Secrets: {list(st.secrets.keys()) if hasattr(st, 'secrets') else 'None'}")
    except:
        log_event(f"[DEBUG] Streamlit import failed in thread")

    # Show cost estimate
    cost_info = estimate_cost_savings(len(creators), avg_posts_per_week=2)
    log_event(f"💰 Cost Estimate: ${cost_info['with_caching']['cost_per_month']:.2f}/month")

    conn = get_connection()
    cursor = conn.cursor()

    new_posts_count = 0

    # 2. Scrape Each Creator (PARALLEL + CACHE-AWARE)
    log_event("Starting Parallel + Incremental Scraping...")

    def scrape_single_creator(creator):
        """Scrape a single creator (for parallel execution)"""
        username = creator["username"]
        try:
            # 🚀 Use cache-aware scraping
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
    for result in results:
        if not result["success"]:
            continue

        username = result["username"]
        cursor.execute("SELECT id FROM creators WHERE username = ?", (username,))
        db_result = cursor.fetchone()

        if db_result:
            creator_id = db_result["id"]
        else:
            cursor.execute("INSERT INTO creators (username, display_name) VALUES (?, ?)",
                           (username, result["display_name"]))
            creator_id = cursor.lastrowid
            conn.commit()

        for reel in result["reels"]:
            reel["creator_id"] = creator_id
            new_posts_count += 1
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO reels
                    (creator_id, instagram_id, caption, likes, comments, views, post_date, post_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    creator_id, reel.get("id"), reel.get("caption"), reel.get("likes", 0),
                    reel.get("comments", 0), reel.get("views", 0), reel.get("timestamp"), reel.get("url")
                ))
            except: pass

        conn.commit()

    log_event(f"✅ Scraped {new_posts_count} NEW posts")

    # 3. Get all recent reels from cache for analysis
    all_reels = get_recent_reels_for_analysis(days_back=7)
    
    log_event(f"Analyzing {len(all_reels)} reels for topics...")
    topic_map = topic_extractor.cluster_topics(all_reels)
    log_event(f"Found {len(topic_map.keys())} unique topics.")
    
    # Save topics to DB
    for topic_name, reels in topic_map.items():
        for reel in reels:
            cursor.execute("SELECT id FROM reels WHERE instagram_id = ?", (reel.get("id"),))
            reel_row = cursor.fetchone()
            if reel_row:
                cursor.execute("INSERT INTO topics (topic_name, reel_id) VALUES (?, ?)", 
                               (topic_name, reel_row["id"]))
    conn.commit()
    
    # 4. Scoring and Ranking
    top_trends = trend_ranker.rank_topics(topic_map)
    
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
        except: pass
    conn.commit()
    conn.close()
    
    log_event(f"🔥 Successfully discovered {len(top_trends)} trending topics!")

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
    subparsers.add_parser("refresh", help="Discovery new trends")
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
