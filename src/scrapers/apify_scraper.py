from apify_client import ApifyClient
from src.config import APIFY_API_KEY, MAX_RESULTS_PER_CREATOR
from datetime import datetime, timedelta

def get_posts(username, results_limit=MAX_RESULTS_PER_CREATOR, results_type="posts"):
    """
    Fetch posts from Instagram profile using Apify's instagram-scraper.
    """
    if not APIFY_API_KEY:
        raise ValueError("APIFY_API_KEY is not set.")

    client = ApifyClient(APIFY_API_KEY)

    # Use apify/instagram-scraper as per requirements
    actor_id = 'apify/instagram-scraper'

    # Run the actor
    run_input = {
        "directUrls": [f"https://www.instagram.com/{username}/"],
        "resultsLimit": results_limit,
        "resultsType": "reels",  # Only fetch reels, not all posts
        "searchType": "user",
        "searchLimit": 1
    }
    
    run = client.actor(actor_id).call(run_input=run_input)
    
    # Store the results in a list
    results = []
    dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    print(f"Apify returned {len(dataset_items)} total items.")
    
    for idx, item in enumerate(dataset_items):
        # Map item properties to consistent post object
        # apify/instagram-scraper uses different field names
        post = {
            "id": item.get("id") or item.get("shortCode"),
            "caption": item.get("caption", ""),
            "timestamp": item.get("timestamp") or item.get("ownerTimestamp"),
            "likes": item.get("likesCount") or item.get("likes", 0),
            "comments": item.get("commentsCount") or item.get("comments", 0),
            "views": item.get("videoViewCount") or item.get("videoViews", 0),
            "type": item.get("type") or ("Video" if item.get("isVideo") else "Image"),
            "url": item.get("url") or item.get("displayUrl"),
            "position": idx,  # Use index as position
            "isPinned": item.get("isPinned", False)
        }
        # print(f" - Found item type: {post['type']}, date: {post['timestamp']}")
        results.append(post)
    
    return results

def detect_and_remove_pinned(posts):
    """
    Heuristic to detect pinned posts:
    - If first 2-3 posts are significantly older than next posts
    - They're likely pinned
    """
    if not posts or len(posts) < 4:
        # If very few posts, return as is (but we should still filter by date later)
        return posts
    
    # Filter by position
    posts_by_position = sorted(posts, key=lambda x: x.get("position", 0))
    
    # Heuristic: Find 4th post to establish baseline
    baseline_date_str = posts_by_position[3].get("timestamp")
    if not baseline_date_str:
        return posts
    
    # Timestamp: ISO Format 
    baseline_date = datetime.fromisoformat(baseline_date_str.replace('Z', '+00:00'))
    
    filtered = []
    for i, post in enumerate(posts_by_position):
        if i < 3:
            post_date_str = post.get("timestamp")
            if not post_date_str:
                continue
            post_date = datetime.fromisoformat(post_date_str.replace('Z', '+00:00'))
            # If post is >7 days older than baseline, likely pinned
            days_diff = (baseline_date - post_date).days
            if days_diff > 7:
                continue # Skip pinned post
        filtered.append(post)
    
    return filtered
