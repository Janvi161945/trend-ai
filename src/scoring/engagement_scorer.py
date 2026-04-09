from datetime import datetime
from src.config import ENGAGEMENT_WEIGHT, CREATOR_DIVERSITY_WEIGHT, RECENCY_WEIGHT, FREQUENCY_WEIGHT

def calculate_topic_score(topic_reels):
    """
    Calculate trend score for a topic.
    
    topic_reels: A list of reel objects (dictionaries) belonging to the same topic.
    Each reel object should have: likes, comments, views, creator_id, post_date.
    """
    if not topic_reels:
        return {
            "score": 0,
            "engagement_rate": 0,
            "creator_count": 0,
            "post_count": 0,
            "avg_likes": 0,
            "avg_views": 0,
            "most_recent": datetime.now()
        }
    
    # 1. Calculate average engagement rate
    total_engagement = 0
    total_views = 0
    
    for reel in topic_reels:
        likes = reel.get("likes", 0)
        comments = reel.get("comments", 0)
        views = reel.get("views", 0)
        
        engagement = likes + (comments * 5)
        total_engagement += engagement
        
        # If views are 0, use heuristic: likes * 20
        post_views = views if views > 0 else likes * 20
        total_views += post_views
    
    avg_engagement_rate = (total_engagement / total_views) * 100 if total_views > 0 else 0
    
    # 2. Creator diversity
    unique_creators = len(set([reel.get("creator_id") for reel in topic_reels]))
    creator_diversity_score = min(unique_creators * 20, 100) # Cap at 100
    
    # 3. Recency score
    now = datetime.now()
    recency_scores = []

    for reel in topic_reels:
        post_date = reel.get("post_date")

        # Skip if no post_date
        if not post_date:
            continue

        # Convert string to datetime if needed
        if isinstance(post_date, str):
             try:
                 # Format could be ISO 8601 with or without Z
                 post_date = datetime.fromisoformat(post_date.replace('Z', '+00:00')).replace(tzinfo=None)
             except (ValueError, AttributeError):
                 continue

        # Calculate recency
        try:
            hours_ago = (now - post_date).total_seconds() / 3600
            # Decay: 100 at 0 hours, 50 at 48 hours, 10 at 120 hours
            recency = max(100 - (hours_ago * 0.75), 0)
            recency_scores.append(recency)
        except (TypeError, AttributeError):
            continue

    avg_recency = sum(recency_scores) / len(recency_scores) if recency_scores else 50
    
    # 4. Post frequency
    post_count = len(topic_reels)
    frequency_score = min(post_count * 25, 100) # Cap at 100
    
    # Final weighted score
    final_score = (
        avg_engagement_rate * ENGAGEMENT_WEIGHT +
        creator_diversity_score * CREATOR_DIVERSITY_WEIGHT +
        avg_recency * RECENCY_WEIGHT +
        frequency_score * FREQUENCY_WEIGHT
    )
    
    # Post dates should be converted back to datetimes for most_recent calculation
    post_dates = []
    for r in topic_reels:
        pd = r.get("post_date")
        if pd:
            try:
                if isinstance(pd, str):
                    pd = datetime.fromisoformat(pd.replace('Z', '+00:00')).replace(tzinfo=None)
                post_dates.append(pd)
            except (ValueError, AttributeError):
                pass

    most_recent = max(post_dates) if post_dates else datetime.now()

    return {
        "score": min(final_score, 100),
        "engagement_rate": avg_engagement_rate,
        "creator_count": unique_creators,
        "post_count": post_count,
        "avg_likes": sum([r.get("likes", 0) for r in topic_reels]) / post_count,
        "avg_views": sum([r.get("views", 0) for r in topic_reels]) / post_count,
        "most_recent": most_recent
    }
