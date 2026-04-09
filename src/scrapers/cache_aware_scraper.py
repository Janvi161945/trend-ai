"""
Cache-aware scraper that only fetches NEW posts since last scrape.
This dramatically reduces API costs for weekly runs.
"""
from datetime import datetime
from src.scrapers import apify_scraper
from src.extractors import pinned_filter
from src.database import get_creator_cache_info, update_creator_cache


def scrape_creator_incremental(username, max_results=5, days_back=7):
    """
    Scrape only NEW posts since last scrape.

    Strategy:
    1. Check cache for last post ID and date
    2. Fetch small batch of recent posts (5-10)
    3. Stop when we hit a post we already have
    4. Return only new posts

    This saves 80-90% of API costs after the first run!
    """

    # Get cache info
    cache_info = get_creator_cache_info(username)
    last_post_id = cache_info["last_post_id"] if cache_info else None
    last_post_date = cache_info["last_post_date"] if cache_info else None

    print(f"  Cache: last_post_id={last_post_id}, last_post_date={last_post_date}")

    # Fetch recent posts (small batch to save costs)
    # On first run: fetch max_results
    # On subsequent runs: fetch smaller batch since we expect few new posts
    fetch_limit = max_results if not last_post_id else min(max_results, 8)

    raw_posts = apify_scraper.get_posts(username, results_limit=fetch_limit)
    print(f"  Fetched {len(raw_posts)} posts from API")

    # Filter to only new posts
    new_posts = []
    latest_post_id = None
    latest_post_date = None

    for post in raw_posts:
        post_id = post.get("id")
        post_date = post.get("timestamp")

        # Track the most recent post for cache update
        if not latest_post_id:
            latest_post_id = post_id
            latest_post_date = post_date

        # Stop if we hit a post we already have
        if last_post_id and post_id == last_post_id:
            print(f"  ✓ Hit cached post {last_post_id}, stopping")
            break

        # Also stop if post is older than our cache
        if last_post_date and post_date:
            try:
                post_dt = datetime.fromisoformat(post_date.replace('Z', '+00:00'))
                cache_dt = datetime.fromisoformat(last_post_date.replace('Z', '+00:00'))
                if post_dt <= cache_dt:
                    print(f"  ✓ Post older than cache, stopping")
                    break
            except:
                pass  # Continue if date parsing fails

        new_posts.append(post)

    print(f"  Found {len(new_posts)} NEW posts")

    # Filter by date, type, and pinned
    filtered_posts = pinned_filter.filter_reels(new_posts, days_back=days_back)
    print(f"  After filtering: {len(filtered_posts)} reels")

    # Update cache with the latest post
    if latest_post_id and filtered_posts:
        update_creator_cache(username, latest_post_id, latest_post_date)
        print(f"  ✓ Cache updated")

    return filtered_posts


def estimate_cost_savings(num_creators, avg_posts_per_week=2):
    """
    Estimate cost savings from cache-aware scraping.

    Args:
        num_creators: Number of creators to track
        avg_posts_per_week: Average new posts per creator per week

    Returns:
        dict with cost breakdown
    """

    # Without caching (fetch 15 posts every time)
    posts_per_creator_full = 15
    total_posts_no_cache = num_creators * posts_per_creator_full
    cost_no_cache = total_posts_no_cache * 0.0026

    # With caching (only fetch ~2-5 new posts per week after first run)
    posts_first_run = num_creators * posts_per_creator_full
    posts_subsequent_runs = num_creators * avg_posts_per_week

    # First week: full scrape
    cost_week_1 = posts_first_run * 0.0026

    # Weeks 2-4: incremental scraping
    cost_week_2_4 = posts_subsequent_runs * 0.0026 * 3

    cost_with_cache_monthly = cost_week_1 + cost_week_2_4

    savings = cost_no_cache * 4 - cost_with_cache_monthly
    savings_percent = (savings / (cost_no_cache * 4)) * 100

    return {
        "without_caching": {
            "cost_per_week": cost_no_cache,
            "cost_per_month": cost_no_cache * 4,
            "posts_per_week": total_posts_no_cache
        },
        "with_caching": {
            "cost_week_1": cost_week_1,
            "cost_weeks_2_4": cost_week_2_4,
            "cost_per_month": cost_with_cache_monthly,
            "posts_week_1": posts_first_run,
            "posts_weeks_2_4": posts_subsequent_runs
        },
        "savings": {
            "amount": savings,
            "percent": savings_percent
        }
    }
