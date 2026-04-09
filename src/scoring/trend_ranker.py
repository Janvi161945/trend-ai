from src.scoring.engagement_scorer import calculate_topic_score

def rank_topics(topics, min_reels=1, min_views=1000, min_creators=1):
    """
    Rank topics by score with quality thresholds for creator recommendations.

    Quality thresholds (relaxed to show emerging trends):
    - min_reels: At least 1 reel (allow single trending posts)
    - min_views: At least 1K total views (shows some engagement)
    - min_creators: At least 1 creator

    topics: { "topic_name": [reel1, reel2, ...] }
    """
    scored_topics = []
    filtered_out = []

    for topic_name, topic_reels in topics.items():
        # Quality Check 1: Minimum number of reels
        if len(topic_reels) < min_reels:
            filtered_out.append(f"{topic_name} (only {len(topic_reels)} reel)")
            continue

        # Quality Check 2: Minimum total views
        total_views = sum([r.get("views", 0) for r in topic_reels])
        if total_views < min_views:
            filtered_out.append(f"{topic_name} (only {total_views} views)")
            continue

        # Quality Check 3: Minimum creator diversity
        unique_creators = len(set([r.get("creator_id") for r in topic_reels]))
        if unique_creators < min_creators:
            filtered_out.append(f"{topic_name} (only {unique_creators} creator)")
            continue

        # Quality Check 4: Minimum average engagement (relaxed)
        total_likes = sum([r.get("likes", 0) for r in topic_reels])
        avg_likes = total_likes / len(topic_reels) if len(topic_reels) > 0 else 0
        if avg_likes < 10:  # At least 10 likes per reel on average (relaxed from 50)
            filtered_out.append(f"{topic_name} (low engagement: {avg_likes:.0f} avg likes)")
            continue

        # Calculate comprehensive score
        score_data = calculate_topic_score(topic_reels)

        # Quality Check 5: Minimum score threshold (relaxed)
        if score_data["score"] < 5:  # Score must be at least 5/100 (relaxed from 20)
            filtered_out.append(f"{topic_name} (low score: {score_data['score']:.1f})")
            continue

        scored_topics.append({
            "topic": topic_name,
            **score_data
        })

    # Show what was filtered out (for debugging/transparency)
    if filtered_out and len(filtered_out) <= 10:
        print(f"  🔍 Filtered out {len(filtered_out)} low-quality topics:")
        for item in filtered_out[:5]:  # Show first 5
            print(f"     - {item}")
        if len(filtered_out) > 5:
            print(f"     ... and {len(filtered_out) - 5} more")

    # Sort topics by score (descending)
    top_topics = sorted(scored_topics, key=lambda x: x["score"], reverse=True)

    return top_topics


def get_topic_insights(topic_data):
    """
    Generate actionable insights for a trending topic.
    Helps creators understand WHY a topic is trending and HOW to approach it.
    """
    insights = []

    # Engagement insight
    if topic_data["engagement_rate"] > 5:
        insights.append(f"🔥 High engagement rate ({topic_data['engagement_rate']:.1f}%) - audience loves this")
    elif topic_data["engagement_rate"] > 2:
        insights.append(f"✅ Good engagement ({topic_data['engagement_rate']:.1f}%)")

    # Creator diversity insight
    if topic_data["creator_count"] >= 3:
        insights.append(f"👥 {topic_data['creator_count']} creators covered this - strong trend signal")
    elif topic_data["creator_count"] == 2:
        insights.append(f"👥 2 creators covered this - emerging trend")

    # Recency insight
    from datetime import datetime
    if isinstance(topic_data.get("most_recent"), datetime):
        hours_ago = (datetime.now() - topic_data["most_recent"]).total_seconds() / 3600
        if hours_ago < 24:
            insights.append(f"⚡ Posted within last 24 hours - very fresh!")
        elif hours_ago < 72:
            insights.append(f"🕐 Posted within last 3 days - still fresh")

    # Views insight
    if topic_data["avg_views"] > 50000:
        insights.append(f"🚀 High reach ({int(topic_data['avg_views']/1000)}K avg views)")
    elif topic_data["avg_views"] > 10000:
        insights.append(f"📈 Good reach ({int(topic_data['avg_views']/1000)}K avg views)")

    return insights
