import pytest
from datetime import datetime, timedelta
from src.scoring.engagement_scorer import calculate_topic_score

def test_calculate_topic_score():
    """Test the topic scoring formula."""
    # Dummy reel data
    now = datetime.now()
    reels = [
        {"likes": 100, "comments": 10, "views": 2000, "creator_id": 1, "post_date": now},
        {"likes": 500, "comments": 50, "views": 10000, "creator_id": 2, "post_date": now - timedelta(days=1)}
    ]
    
    score_data = calculate_topic_score(reels)
    
    # Check if keys exist and score is between 0-100
    assert "score" in score_data
    assert "engagement_rate" in score_data
    assert "creator_count" in score_data
    assert score_data["creator_count"] == 2
    assert 0 <= score_data["score"] <= 100
    
    # Engagement Calculation Check:
    # Reel 1: (100 + 10*5) / 2000 = 150 / 2000 = 7.5%
    # Reel 2: (500 + 50*5) / 10000 = 750 / 10000 = 7.5%
    # Total Engagement = 150 + 750 = 900
    # Total Views = 2000 + 10000 = 12000
    # Avg Rate = (900 / 12000) * 100 = 7.5%
    assert score_data["engagement_rate"] == 7.5
