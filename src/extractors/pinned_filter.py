from datetime import datetime, timedelta

def is_truly_recent(post, days=3):
    """Check if post is within the recent threshold (default 3 days)."""
    timestamp = post.get("timestamp")
    if not timestamp:
        return False

    # Handle both ISO format and Unix timestamp
    try:
        if isinstance(timestamp, str):
            post_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
            # Unix timestamp (seconds)
            post_date = datetime.fromtimestamp(timestamp)
    except (ValueError, TypeError):
        return False

    cutoff = datetime.now() - timedelta(days=days)
    return post_date >= cutoff

def detect_and_remove_pinned(posts):
    """
    Heuristic to detect pinned posts:
    - If first 2-3 posts are significantly older than next posts
    - They're likely pinned
    """
    if not posts or len(posts) < 4:
        return posts

    # Ensure they are sorted by their original scraped position
    posts_by_position = sorted(posts, key=lambda x: x.get("position", 0))

    # Establish baseline from 4th post
    baseline_timestamp = posts_by_position[3].get("timestamp")
    if not baseline_timestamp:
        return posts

    try:
        if isinstance(baseline_timestamp, str):
            baseline_date = datetime.fromisoformat(baseline_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
        else:
            baseline_date = datetime.fromtimestamp(baseline_timestamp)
    except (ValueError, TypeError):
        return posts

    filtered = []
    for i, post in enumerate(posts_by_position):
        if i < 3:
            post_timestamp = post.get("timestamp")
            if not post_timestamp:
                continue

            try:
                if isinstance(post_timestamp, str):
                    post_date = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    post_date = datetime.fromtimestamp(post_timestamp)
            except (ValueError, TypeError):
                continue

            # If post is >5 days older than baseline, likely pinned (stricter for 2-3 day window)
            days_diff = (baseline_date - post_date).days
            if days_diff > 5:
                continue # Skip pinned post
        filtered.append(post)

    return filtered

def filter_reels(posts, days_back=3):
    """
    STRICT filter for REELS ONLY - ensures high-quality trend data.
    Filters out: photos, carousels, pinned posts, old posts.
    """
    if not posts:
        return []

    # 1. STRICT: Filter ONLY reels (exclude photos, carousels)
    reel_posts = []
    for post in posts:
        post_type = str(post.get("type", "")).lower()

        # STRICT: Only accept "video" or "reel" types
        # Exclude: "image", "sidecar", "carousel", "photo"
        if "reel" in post_type or post_type == "video":
            # Additional check: must have video indicators
            has_video = (
                post.get("videoViewCount") or
                post.get("videoViews") or
                post.get("views") or
                "video" in post_type.lower()
            )

            if has_video:
                reel_posts.append(post)

    # 2. Filter by date (last N days) - STRICT
    recent_reels = [
        post for post in reel_posts
        if is_truly_recent(post, days=days_back)
    ]

    # 3. Filter out low-engagement reels (noise reduction)
    # Must have at least some minimum engagement
    quality_reels = []
    for reel in recent_reels:
        likes = reel.get("likes", 0) or reel.get("likesCount", 0)
        views = reel.get("views", 0) or reel.get("videoViewCount", 0)

        # Skip reels with no engagement data
        if likes == 0 and views == 0:
            continue

        # Skip reels with suspiciously low engagement (likely spam/test posts)
        if likes < 10:  # At least 10 likes
            continue

        quality_reels.append(reel)

    # 4. Filter explicit pinned posts if flag is available
    non_pinned = [
        p for p in quality_reels
        if not p.get("isPinned", False)
    ]

    # 5. Use heuristic for any remaining pinned
    final_reels = detect_and_remove_pinned(non_pinned)

    return final_reels
