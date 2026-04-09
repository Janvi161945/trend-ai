# Finance Reel Trend Analysis Guide

This guide explains how to use the AI-powered trend analysis tools to identify trending finance topics and generate content ideas.

## Overview

The trend analysis system provides three main capabilities:

1. **Topic Extraction with Confidence** - Extract specific topics from captions with confidence scores
2. **Reel Idea Generation** - Generate viral content ideas based on trending captions
3. **Multi-Signal Trend Detection** - Identify trending topics using engagement, recency, and creator diversity

---

## 1. Topic Extraction with Confidence

### Purpose
Extract the main finance topic from individual reel captions with a confidence score indicating extraction quality.

### Module
`src/extractors/topic_extractor_json.py`

### Functions

#### `extract_topic_with_confidence(caption)`

Extracts a single topic from a caption.

**Input:**
```python
caption = "3 tax saving tips for salaried employees before March"
```

**Output:**
```python
{
    "topic": "Tax saving for salaried",
    "confidence": 95
}
```

**Rules:**
- Topics are 2-5 words
- Specific (not generic like "Finance tips")
- Confidence 0-100 (higher = more certain)

**Example Usage:**
```python
from src.extractors.topic_extractor_json import extract_topic_with_confidence

caption = "SIP vs FD which is better for beginners"
result = extract_topic_with_confidence(caption)

print(f"Topic: {result['topic']}")
print(f"Confidence: {result['confidence']}%")
```

#### `batch_extract_topics(captions)`

Process multiple captions at once.

**Input:**
```python
captions = [
    "3 tax saving tips for salaried employees",
    "How I built emergency fund in 6 months",
    "Credit card mistakes to avoid"
]
```

**Output:**
```python
[
    {"caption": "3 tax saving tips...", "topic": "Tax saving for salaried", "confidence": 95},
    {"caption": "How I built emergency...", "topic": "Emergency fund building", "confidence": 90},
    {"caption": "Credit card mistakes...", "topic": "Credit Card Mistakes", "confidence": 88}
]
```

---

## 2. Reel Idea Generation

### Purpose
Analyze trending captions and generate actionable, viral-friendly reel ideas for creators.

### Module
`src/generators/reel_idea_generator.py`

### Functions

#### `generate_reel_ideas(captions_list)`

Generates 5-10 content ideas from a list of captions.

**Input:**
```python
captions_list = [
    "SIP vs FD comparison for beginners",
    "Tax saving before March deadline",
    "Credit card mistakes that cost money",
    # ... more captions
]
```

**Output:**
```python
[
    {
        "reel_idea": "3 Tax Saving Hacks Before March",
        "topic": "Tax Planning",
        "reason": "Multiple creators covering tax deadlines, high engagement"
    },
    {
        "reel_idea": "SIP vs FD for Beginners",
        "topic": "Investment Comparison",
        "reason": "Common beginner question, viral comparison format"
    },
    # ... 5-10 total ideas
]
```

**Good vs Bad Ideas:**

✅ **Good:**
- "3 Tax Saving Hacks Before March" (Specific, actionable)
- "SIP vs FD for Beginners" (Clear comparison)
- "Credit Card Mistakes to Avoid" (Problem-solution)

❌ **Bad:**
- "Finance tips" (Too generic)
- "Investment advice" (Vague)

#### `generate_ideas_from_reels(reels)`

Generate ideas directly from reel objects (with metadata).

**Input:**
```python
reels = [
    {
        "caption": "Tax saving tips...",
        "likes": 5000,
        "comments": 120,
        "creator_name": "financeguru"
    },
    # ... more reels
]
```

**Example Usage:**
```python
from src.generators.reel_idea_generator import generate_ideas_from_reels, format_reel_idea_output

ideas = generate_ideas_from_reels(reels)
print(format_reel_idea_output(ideas))
```

---

## 3. Multi-Signal Trend Detection

### Purpose
Identify trending topics using multiple signals: engagement, recency, and creator diversity.

### Module
`src/scoring/multi_signal_trend_detector.py`

### Functions

#### `detect_trending_topics(reels_data)`

Uses LLM to analyze reels and detect trending topics.

**Input:**
```python
reels_data = [
    {
        "caption": "Tax saving before March",
        "likes": 10000,
        "comments": 250,
        "creator_name": "financepro",
        "timestamp": "2024-03-01T10:00:00"
    },
    # ... more reels
]
```

**Output:**
```python
[
    {
        "topic": "Tax Saving Before March",
        "trend_score": 85,
        "creators": ["financepro", "moneyguru", "taxexpert"],
        "reason": "High engagement (10K+ likes), covered by 3 creators, very recent"
    },
    # ... 5-10 trending topics
]
```

**Scoring:**
- `trend_score`: 0-100 (higher = stronger trend)
- Even 2 creators covering a topic = emerging trend
- Recency matters (last 24-72 hours)

#### `calculate_local_trend_score(reels_for_topic)`

Calculate trend score without using LLM (faster, offline).

**Scoring Breakdown (0-100):**

1. **Engagement Score (0-40 points)**
   - Based on total likes + (comments × 5)
   - 10K avg engagement = 40 points

2. **Recency Score (0-30 points)**
   - Last 24 hours = 10 pts per reel
   - Last 72 hours = 5 pts per reel
   - Last week = 2 pts per reel

3. **Creator Diversity (0-30 points)**
   - 1 creator = 10 pts
   - 2 creators = 20 pts
   - 3+ creators = 30 pts

**Example:**
```python
from src.scoring.multi_signal_trend_detector import calculate_local_trend_score

topic_reels = [
    {"likes": 5000, "comments": 100, "timestamp": "2024-03-10T12:00:00", "creator_name": "user1"},
    {"likes": 8000, "comments": 150, "timestamp": "2024-03-10T15:00:00", "creator_name": "user2"},
]

score_data = calculate_local_trend_score(topic_reels)
print(f"Trend Score: {score_data['trend_score']}/100")
```

#### `hybrid_trend_detection(reels_data, use_llm=True)`

Best of both worlds: LLM for topic identification + local scoring.

**Parameters:**
- `use_llm=True`: Use AI for trend detection (slower, more accurate)
- `use_llm=False`: Use local clustering and scoring (faster, offline)

**Example Usage:**
```python
from src.scoring.multi_signal_trend_detector import hybrid_trend_detection, format_trending_output

# With LLM (recommended)
trends = hybrid_trend_detection(reels_data, use_llm=True)

# Without LLM (faster)
trends = hybrid_trend_detection(reels_data, use_llm=False)

print(format_trending_output(trends))
```

---

## Complete Workflow Example

Here's how to use all three tools together:

```python
from src.scrapers.cache_aware_scraper import scrape_all_creators
from src.extractors.topic_extractor_json import batch_extract_topics
from src.generators.reel_idea_generator import generate_ideas_from_reels
from src.scoring.multi_signal_trend_detector import detect_trending_topics, format_trending_output

# 1. Scrape recent reels
print("📥 Scraping reels...")
reels = scrape_all_creators(days_back=3)

# 2. Extract topics with confidence
print("\n🎯 Extracting topics...")
captions = [r["caption"] for r in reels if r.get("caption")]
topics = batch_extract_topics(captions[:20])

for t in topics[:5]:
    print(f"  - {t['topic']} (confidence: {t['confidence']}%)")

# 3. Generate reel ideas
print("\n💡 Generating content ideas...")
ideas = generate_ideas_from_reels(reels)

print("\nTop 5 Ideas:")
for i, idea in enumerate(ideas[:5], 1):
    print(f"{i}. {idea['reel_idea']}")
    print(f"   Why: {idea['reason']}\n")

# 4. Detect trending topics
print("\n🔥 Detecting trends...")
trends = detect_trending_topics(reels)

print(format_trending_output(trends))
```

---

## Integration with Existing Code

These new modules integrate seamlessly with existing trend-ai components:

### Existing Modules
- `src/extractors/topic_extractor.py` - Original topic extraction
- `src/scoring/engagement_scorer.py` - Engagement calculations
- `src/generators/content_generator.py` - Script generation

### New Modules
- `src/extractors/topic_extractor_json.py` - JSON-based extraction with confidence
- `src/generators/reel_idea_generator.py` - Idea generation
- `src/scoring/multi_signal_trend_detector.py` - Multi-signal trend detection

### When to Use Which

| Task | Module | Best For |
|------|--------|----------|
| Extract single topic | `topic_extractor.py` | Existing pipeline |
| Extract topic with confidence | `topic_extractor_json.py` | Quality validation |
| Generate content ideas | `reel_idea_generator.py` | Creator inspiration |
| Detect trends (LLM) | `multi_signal_trend_detector.py` | Comprehensive analysis |
| Calculate scores locally | `engagement_scorer.py` | Fast offline scoring |

---

## API Configuration

All modules require the Groq API key:

```bash
# .env file
GROQ_API_KEY=your_api_key_here
```

**Models Used:**
- `llama-3.1-8b-instant` - Fast, efficient for structured outputs

---

## Best Practices

### 1. Topic Extraction
- Filter out captions < 10 characters
- Validate confidence scores (use only 70+% for critical decisions)
- Batch process for efficiency

### 2. Idea Generation
- Feed diverse captions (different creators, topics)
- Use 20-50 captions for best results
- Regenerate weekly to stay current

### 3. Trend Detection
- Scrape recent reels (3-5 days)
- Include timestamp data for recency scoring
- Set minimum thresholds (e.g., 2+ creators, 1K+ views)

### 4. Performance
- Use `use_llm=False` for fast local scoring
- Cache API results to avoid redundant calls
- Batch process when possible

---

## Troubleshooting

### Issue: Low confidence scores
**Solution:** Check caption quality. Short or unclear captions get low scores.

### Issue: No trending topics detected
**Solution:** Ensure reels have recent timestamps and engagement data.

### Issue: Generic topic extraction
**Solution:** Add more context in captions or use stricter validation.

### Issue: JSON parsing errors
**Solution:** The code handles this gracefully, returns default values. Check API response.

---

## Output Examples

### Topic Extraction Output
```json
[
  {
    "topic": "Tax Saving for Salaried",
    "confidence": 95
  },
  {
    "topic": "SIP vs FD",
    "confidence": 90
  }
]
```

### Reel Ideas Output
```json
[
  {
    "reel_idea": "3 Tax Saving Hacks Before March",
    "topic": "Tax Planning",
    "reason": "Multiple creators covering tax deadlines, high engagement"
  }
]
```

### Trending Topics Output
```json
[
  {
    "topic": "Tax Saving Before March",
    "trend_score": 85,
    "creators": ["financepro", "moneyguru"],
    "reason": "High engagement, 2 creators, very recent"
  }
]
```

---

## Next Steps

1. Integrate with Streamlit dashboard (src/scoring/multi_signal_trend_detector.py:180)
2. Add trend history tracking
3. Implement topic clustering for similar trends
4. Create automated weekly trend reports

---

## Support

For questions or issues:
- Check existing code in `src/` directory
- Review test cases in `tests/` directory
- See `README.md` for general setup
