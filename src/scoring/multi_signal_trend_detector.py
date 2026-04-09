from groq import Groq
from src.config import GROQ_API_KEY
import json
from datetime import datetime


def detect_trending_topics(reels_data):
    """
    Analyze Instagram finance reels to detect trending topics using multiple signals.

    Given:
    - Reel captions
    - Likes
    - Comments
    - Creator name

    Identifies trending topics based on:
    1. Engagement (likes/comments)
    2. Recency
    3. Multiple creators covering topic

    Important:
    - Even if only 2 creators covered a topic, consider it emerging
    - Generate 5-10 trending topics

    Args:
        reels_data (list): List of dicts with keys:
            - caption (str)
            - likes (int)
            - comments (int)
            - creator_name (str)
            - timestamp (datetime or str, optional)

    Returns:
        list: List of trending topic dicts with:
            - topic (str)
            - trend_score (int, 0-100)
            - creators (list of str)
            - reason (str)
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=GROQ_API_KEY)

    # Format reels data for prompt (limit to 50 most engaging reels)
    sorted_reels = sorted(
        reels_data,
        key=lambda x: x.get("likes", 0) + x.get("comments", 0) * 5,
        reverse=True
    )[:50]

    formatted_reels = []
    for i, reel in enumerate(sorted_reels, 1):
        caption = reel.get("caption", "")[:150]  # Truncate long captions
        likes = reel.get("likes", 0)
        comments = reel.get("comments", 0)
        creator = reel.get("creator_name", "Unknown")

        formatted_reels.append(
            f"{i}. @{creator} | {likes} likes, {comments} comments\n   \"{caption}\""
        )

    reels_formatted = "\n\n".join(formatted_reels)

    prompt = f"""You are a JSON API. Return ONLY valid JSON, no explanations or markdown.

Analyze these reels and identify 5-10 trending topics based on engagement and multiple creators.

Data:
{reels_formatted}

Return this exact JSON structure (NO markdown, NO code blocks, NO explanations):

[
    {{
        "topic": "specific topic name",
        "trend_score": 85,
        "creators": ["creator1", "creator2"],
        "reason": "why it's trending"
    }}
]"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=1500
    )

    result_text = response.choices[0].message.content.strip()

    # Parse JSON response
    try:
        # Clean up response - remove common LLM artifacts
        result_text = result_text.strip()

        # Remove markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        # Remove text before first [ or {
        if "[" in result_text:
            result_text = result_text[result_text.find("["):]
        elif "{" in result_text:
            result_text = result_text[result_text.find("{"):]

        # Remove text after last ] or }
        if "]" in result_text:
            result_text = result_text[:result_text.rfind("]")+1]
        elif "}" in result_text:
            result_text = result_text[:result_text.rfind("}")+1]

        trends = json.loads(result_text)

        # Validate structure
        if not isinstance(trends, list):
            return []

        # Clean and validate each trend
        validated_trends = []
        for trend in trends:
            if all(key in trend for key in ["topic", "trend_score", "creators", "reason"]):
                validated_trends.append({
                    "topic": trend["topic"].strip(),
                    "trend_score": max(0, min(100, int(trend["trend_score"]))),
                    "creators": trend["creators"] if isinstance(trend["creators"], list) else [],
                    "reason": trend["reason"].strip()
                })

        # Sort by trend score
        validated_trends.sort(key=lambda x: x["trend_score"], reverse=True)

        return validated_trends

    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ Error parsing JSON response: {e}")
        print(f"Raw response: {result_text[:500]}")
        return []


def calculate_local_trend_score(reels_for_topic):
    """
    Calculate trend score based on engagement, recency, and creator diversity.
    This is a local Python calculation (without LLM).

    Args:
        reels_for_topic (list): Reels about a specific topic

    Returns:
        dict: Trend metrics
    """
    if not reels_for_topic:
        return {
            "trend_score": 0,
            "engagement_score": 0,
            "recency_score": 0,
            "diversity_score": 0,
            "total_engagement": 0,
            "unique_creators": 0
        }

    # 1. Engagement Score (0-40 points)
    total_likes = sum([r.get("likes", 0) for r in reels_for_topic])
    total_comments = sum([r.get("comments", 0) for r in reels_for_topic])
    total_engagement = total_likes + (total_comments * 5)  # Comments worth 5x likes

    avg_engagement = total_engagement / len(reels_for_topic)
    # Normalize: 10K avg engagement = 40 points
    engagement_score = min(40, (avg_engagement / 10000) * 40)

    # 2. Recency Score (0-30 points)
    recency_score = 0
    now = datetime.now()

    for reel in reels_for_topic:
        timestamp = reel.get("timestamp")
        if timestamp:
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                except:
                    continue

            hours_ago = (now - timestamp).total_seconds() / 3600
            if hours_ago < 24:
                recency_score += 10
            elif hours_ago < 72:
                recency_score += 5
            elif hours_ago < 168:  # 1 week
                recency_score += 2

    recency_score = min(30, recency_score)

    # 3. Creator Diversity Score (0-30 points)
    unique_creators = len(set([r.get("creator_name", "unknown") for r in reels_for_topic]))
    # 1 creator = 10 pts, 2 = 20 pts, 3+ = 30 pts
    diversity_score = min(30, unique_creators * 10)

    # Total Score (0-100)
    trend_score = engagement_score + recency_score + diversity_score

    return {
        "trend_score": round(trend_score, 1),
        "engagement_score": round(engagement_score, 1),
        "recency_score": round(recency_score, 1),
        "diversity_score": round(diversity_score, 1),
        "total_engagement": total_engagement,
        "unique_creators": unique_creators
    }


def hybrid_trend_detection(reels_data, use_llm=True):
    """
    Hybrid approach: Use LLM for topic identification, then calculate scores locally.

    Args:
        reels_data (list): List of reel dicts
        use_llm (bool): If True, use LLM for trend detection. If False, use local clustering.

    Returns:
        list: Trending topics with scores
    """
    if use_llm:
        print("🤖 Using LLM for trend detection...")
        return detect_trending_topics(reels_data)
    else:
        print("📊 Using local trend scoring...")

        # Cluster reels by topic first (using existing logic)
        from src.extractors.topic_extractor import cluster_topics

        topics = cluster_topics(reels_data)

        # Calculate scores for each topic
        trending = []
        for topic_name, topic_reels in topics.items():
            score_data = calculate_local_trend_score(topic_reels)

            if score_data["trend_score"] < 10:  # Filter low-score topics
                continue

            trending.append({
                "topic": topic_name,
                "trend_score": score_data["trend_score"],
                "creators": list(set([r.get("creator_name", "unknown") for r in topic_reels])),
                "reason": f"Engagement: {score_data['engagement_score']:.0f}/40, "
                          f"Recency: {score_data['recency_score']:.0f}/30, "
                          f"Diversity: {score_data['diversity_score']:.0f}/30"
            })

        # Sort by trend score
        trending.sort(key=lambda x: x["trend_score"], reverse=True)

        return trending


def format_trending_output(trends):
    """
    Format trending topics for display.

    Args:
        trends (list): List of trending topic dicts

    Returns:
        str: Formatted output
    """
    if not trends:
        return "No trending topics detected."

    output = "🔥 TRENDING TOPICS:\n\n"

    for i, trend in enumerate(trends, 1):
        output += f"{i}. {trend['topic']} (Score: {trend['trend_score']})\n"
        output += f"   Creators: {', '.join(trend['creators'][:5])}"
        if len(trend['creators']) > 5:
            output += f" +{len(trend['creators']) - 5} more"
        output += f"\n   Why: {trend['reason']}\n\n"

    return output
