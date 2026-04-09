import pytest
from src.scrapers import apify_scraper

def test_detect_and_remove_pinned():
    """Test the pinned post detection logic."""
    # Dummy data
    # Baseline post (4th post in list)
    posts = [
        {"position": 0, "timestamp": "2024-03-01T10:00:00Z"}, # Pinned (old)
        {"position": 1, "timestamp": "2024-04-01T10:00:00Z"}, # Not pinned (recent)
        {"position": 2, "timestamp": "2024-02-01T10:00:00Z"}, # Pinned (very old)
        {"position": 3, "timestamp": "2024-04-01T09:00:00Z"}, # Baseline (recent)
        {"position": 4, "timestamp": "2024-04-01T08:00:00Z"}
    ]
    
    filtered = apify_scraper.detect_and_remove_pinned(posts)
    
    # Position 0 and 2 should be removed because they are older than position 3 (baseline)
    # Position 1 should stay (recent)
    assert len(filtered) == 3
    assert filtered[0]["position"] == 1
    assert filtered[1]["position"] == 3
    assert filtered[2]["position"] == 4
