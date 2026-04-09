# Finance Trend AI - Architecture & Implementation Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Problem Statement](#problem-statement)
3. [Solution Architecture](#solution-architecture)
4. [Cost Optimization Strategy](#cost-optimization-strategy)
5. [Technical Implementation](#technical-implementation)
6. [Database Schema](#database-schema)
7. [Scraping Strategy](#scraping-strategy)
8. [Topic Extraction & Scoring](#topic-extraction--scoring)
9. [User Workflow](#user-workflow)
10. [Deployment](#deployment)

---

## 📌 Project Overview

**Goal**: Build an AI-powered Finance Trend Discovery Tool for Instagram creators that:
- Scrapes recent reels from top finance creators
- Identifies trending topics using AI
- Scores topics by engagement metrics
- Generates content ideas for the user

**Key Constraint**: Must work within $5 Apify budget (should last 20+ months)

---

## 🎯 Problem Statement

### What User Currently Does (Manual)
1. Opens Instagram
2. Visits 5-10 finance creator profiles one by one
3. Scrolls through their recent reels
4. Mentally notes what's performing well
5. Researches each topic
6. Decides what to create

**Time**: 2-3 hours per week

### What We Automate
1. User clicks "Refresh Trends"
2. App scrapes last 3-5 days of reels from followed creators
3. AI extracts topics and groups similar content
4. Shows top 3-4 trending topics with engagement data
5. User picks one → AI generates content script

**Time**: 2 minutes per week

---

## 🏗️ Solution Architecture

```
┌─────────────────────────────────────────────────┐
│           USER INTERFACE                        │
│  (Streamlit Dashboard / CLI)                    │
│  - Show last update time                        │
│  - "Refresh Trends" button                      │
│  - Display top trending topics                  │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         SCRAPER ORCHESTRATOR                    │
│  - Check local cache (SQLite)                   │
│  - Determine which creators need scraping       │
│  - Filter out pinned posts                      │
│  - Only scrape recent reels (3-5 days)          │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         INSTAGRAM SCRAPER                       │
│  Primary: Apify Instagram Scraper (Paid)        │
│  Fallback: Instaloader (Free)                   │
│  - Scrapes profile posts                        │
│  - Filters: Only reels, no pinned posts         │
│  - Date filter: Last 3-5 days only              │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         DATA STORAGE (SQLite)                   │
│  Tables:                                        │
│  - reels (caption, likes, views, date, etc)     │
│  - creators (username, followers, last_scrape)  │
│  - topics (extracted topics with scores)        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         TOPIC EXTRACTION (LLM)                  │
│  - Groq API (Free - Llama 3.1)                  │
│  - Extracts core topic from caption             │
│  - Normalizes different captions to same topic  │
│  Example:                                       │
│    "SIP vs FD explained" → "SIP vs Fixed Deposit"│
│    "FD or SIP - which?" → "SIP vs Fixed Deposit"│
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         TOPIC CLUSTERING                        │
│  - Group reels by extracted topic               │
│  - Calculate aggregate metrics per topic        │
│  - Count creator diversity                      │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         ENGAGEMENT SCORING                      │
│  Score = weighted average of:                   │
│  - Engagement rate (40%)                        │
│  - Creator diversity (25%)                      │
│  - Recency (20%)                                │
│  - Post frequency (15%)                         │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         TREND RANKING                           │
│  - Sort topics by score                         │
│  - Return top 3-4 topics                        │
│  - Include best performing reel for each        │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│         CONTENT GENERATOR (Optional)            │
│  - User selects a topic                         │
│  - AI generates reel script                     │
│  - Provides hook, body, CTA                     │
└─────────────────────────────────────────────────┘
```

---

## 💰 Cost Optimization Strategy

### Why We Need Optimization
- **Problem**: Creators don't post daily
- **Risk**: Scraping all creators weekly = wasted API calls
- **Solution**: Smart caching + incremental updates

### Cost Breakdown

| Approach | Cost per Run | Runs with $5 | Duration |
|----------|--------------|--------------|----------|
| Naive (scrape all weekly) | $0.15 | 33 runs | 8 months |
| Smart (cache + incremental) | $0.05-0.10 | 50-100 runs | 12-24 months |
| On-demand (user triggered) | $0.10 | 50 runs | 20+ months |

### Optimization Techniques

#### 1. **Local Caching (SQLite)**
- Store all scraped reels locally
- Track last scrape timestamp per creator
- Only fetch new content since last scrape

#### 2. **Date Filtering**
- Only scrape last 3-5 days
- Ignore older content
- Most finance trends are time-sensitive

#### 3. **Result Limiting**
```python
scrape_config = {
    "resultsLimit": 10,  # Only last 10 posts per creator
    "resultsType": "posts",
    "addParentData": False  # Don't fetch extra data
}
```

#### 4. **On-Demand Scraping**
- No automatic weekly schedule
- User clicks "Refresh" when needed
- Typically 2-3 times per month

#### 5. **Pinned Post Filtering**
```python
# Apify returns posts in chronological order
# BUT pinned posts appear first
# Solution: Filter by actual post date

def filter_pinned_posts(posts):
    """
    Remove pinned posts that are older than 7 days
    but appear at top of feed
    """
    recent_threshold = datetime.now() - timedelta(days=7)

    filtered = []
    for post in posts:
        # If post is older than 7 days, likely pinned
        if post.timestamp < recent_threshold:
            continue
        filtered.append(post)

    return filtered
```

---

## 🛠️ Technical Implementation

### Tech Stack

```yaml
Backend:
  - Python 3.10+
  - FastAPI (optional, for API endpoints)

Scraping:
  - Primary: Apify Instagram Profile Scraper (Paid)
  - Fallback: Instaloader (Free, rate-limited)

Database:
  - SQLite (local, serverless)
  - Alternative: Supabase (free tier for cloud)

AI/LLM:
  - Groq API (Free tier - Llama 3.1)
  - Alternative: Together AI (Free $25 credit)

Frontend:
  - Option 1: Streamlit (simple, free hosting)
  - Option 2: CLI (fastest, no UI)

Deployment:
  - Render.com (free tier)
  - Streamlit Cloud (free for Streamlit apps)
  - GitHub Actions (for scheduled runs)
```

### Project Structure

```
trend-ai/
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   └── API_KEYS.md              # API key setup guide
│
├── src/
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   ├── database.py              # SQLite operations
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── apify_scraper.py     # Apify integration
│   │   └── instaloader_scraper.py  # Free fallback
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── topic_extractor.py   # LLM-based topic extraction
│   │   └── pinned_filter.py     # Filter pinned posts
│   ├── scoring/
│   │   ├── __init__.py
│   │   ├── engagement_scorer.py # Calculate scores
│   │   └── trend_ranker.py      # Rank topics
│   └── generators/
│       ├── __init__.py
│       └── content_generator.py # Generate scripts (optional)
│
├── app/
│   ├── streamlit_app.py         # Streamlit UI
│   └── cli.py                   # Command-line interface
│
├── tests/
│   ├── test_scraper.py
│   ├── test_extractor.py
│   └── test_scorer.py
│
├── data/
│   └── trends.db                # SQLite database (gitignored)
│
├── config.json                  # User configuration
├── .env                         # API keys (gitignored)
├── requirements.txt
└── README.md
```

---

## 💾 Database Schema

### SQLite Tables

```sql
-- Creators table
CREATE TABLE creators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    display_name TEXT,
    followers INTEGER,
    last_scraped_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reels table
CREATE TABLE reels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER NOT NULL,
    instagram_id TEXT UNIQUE,  -- Instagram post ID
    caption TEXT,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    views INTEGER DEFAULT 0,
    post_date TIMESTAMP NOT NULL,
    post_url TEXT,
    is_pinned BOOLEAN DEFAULT 0,  -- Flag for pinned posts
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (creator_id) REFERENCES creators(id)
);

-- Extracted topics table
CREATE TABLE topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT NOT NULL,
    reel_id INTEGER NOT NULL,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reel_id) REFERENCES reels(id)
);

-- Topic scores (cached for performance)
CREATE TABLE topic_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT UNIQUE NOT NULL,
    score REAL NOT NULL,
    engagement_rate REAL,
    creator_count INTEGER,
    post_count INTEGER,
    avg_likes INTEGER,
    avg_views INTEGER,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_reels_post_date ON reels(post_date);
CREATE INDEX idx_reels_creator_id ON reels(creator_id);
CREATE INDEX idx_topics_topic_name ON topics(topic_name);
```

---

## 🔍 Scraping Strategy

### Challenge: Pinned Posts

**Problem**: Instagram creators often pin their best-performing reels to the top of their profile. These appear first even if they're weeks/months old.

**Example**:
```
@ca_rachanaranade profile:
📌 Pinned: "Tax saving guide" (posted 45 days ago)
📌 Pinned: "Best mutual funds" (posted 30 days ago)
   Recent: "Budget 2024 updates" (posted 1 day ago)
   Recent: "SIP vs FD" (posted 3 days ago)
```

If we scrape without filtering, we'll get:
- Old pinned content mixed with fresh content
- Misleading trend analysis
- False positive topics

### Solution: Multi-Layer Filtering

```python
def scrape_recent_reels(creator_username, days=5):
    """
    Scrape recent reels, excluding pinned posts
    """
    # Step 1: Fetch posts from Apify
    raw_posts = apify_scraper.get_posts(
        username=creator_username,
        results_limit=20,  # Fetch more to account for pinned
        results_type="posts"
    )

    # Step 2: Filter by date (last N days)
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_posts = [
        post for post in raw_posts
        if post.timestamp >= cutoff_date
    ]

    # Step 3: Filter by post type (only reels)
    reels_only = [
        post for post in recent_posts
        if post.type == "Reel" or post.type == "Video"
    ]

    # Step 4: Detect pinned posts
    # Method 1: Check if post has "pinned" flag (if Apify provides)
    # Method 2: Check post position vs date
    # If a post is at position 0-2 but older than position 3+, it's pinned

    filtered_reels = detect_and_remove_pinned(reels_only)

    return filtered_reels


def detect_and_remove_pinned(posts):
    """
    Heuristic to detect pinned posts:
    - If first 2-3 posts are significantly older than next posts
    - They're likely pinned
    """
    if len(posts) < 4:
        return posts

    # Sort by scraped position (order from API)
    posts_by_position = sorted(posts, key=lambda x: x.position)

    # Get date of 4th post (likely first non-pinned)
    if len(posts_by_position) >= 4:
        baseline_date = posts_by_position[3].timestamp

        # Check first 3 posts
        filtered = []
        for i, post in enumerate(posts_by_position):
            if i < 3:
                # If post is >7 days older than baseline, likely pinned
                days_diff = (baseline_date - post.timestamp).days
                if days_diff > 7:
                    continue  # Skip pinned post
            filtered.append(post)

        return filtered

    return posts
```

### Alternative: Use Instagram API Flags

Apify's Instagram scraper sometimes provides metadata:

```python
{
    "id": "abc123",
    "caption": "Tax saving guide",
    "timestamp": "2024-02-15T10:30:00Z",
    "isPinned": true,  # If available
    "position": 0
}
```

Check Apify documentation for latest field names.

---

## 🧠 Topic Extraction & Scoring

### Topic Extraction with LLM

**Goal**: Normalize different captions to the same topic

```python
from groq import Groq

client = Groq(api_key="your_api_key")

def extract_topic(caption):
    """
    Extract core finance topic from Instagram caption
    """
    prompt = f"""You are a finance content analyzer.
Extract the MAIN finance topic from this Instagram reel caption.
Return ONLY the topic name in 2-5 words. No explanations.

Examples:
- Caption: "SIP vs FD - which is better for you? 📊"
  Topic: SIP vs Fixed Deposit

- Caption: "Budget 2024 tax changes explained 💰"
  Topic: Budget 2024 Tax Changes

- Caption: "5 credit card mistakes to avoid! 💳"
  Topic: Credit Card Mistakes

Now extract the topic:
Caption: "{caption}"
Topic:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=20
    )

    topic = response.choices[0].message.content.strip()
    return topic
```

### Topic Clustering

```python
def cluster_topics(reels):
    """
    Group reels by extracted topic
    """
    topics = {}

    for reel in reels:
        topic = extract_topic(reel.caption)

        if topic not in topics:
            topics[topic] = []

        topics[topic].append(reel)

    return topics
```

### Engagement Scoring Formula

```python
def calculate_topic_score(topic_reels):
    """
    Calculate trend score for a topic

    Score components:
    1. Engagement Rate (40%): (likes + comments) / views
    2. Creator Diversity (25%): How many different creators
    3. Recency (20%): How recent are the posts
    4. Post Frequency (15%): How many posts on this topic
    """

    # 1. Calculate average engagement rate
    total_engagement = 0
    total_views = 0

    for reel in topic_reels:
        engagement = reel.likes + (reel.comments * 5)  # Comments weighted higher
        total_engagement += engagement
        total_views += reel.views if reel.views > 0 else reel.likes * 20

    avg_engagement_rate = (total_engagement / total_views) * 100 if total_views > 0 else 0

    # 2. Creator diversity
    unique_creators = len(set([reel.creator_id for reel in topic_reels]))
    creator_diversity_score = min(unique_creators * 20, 100)  # Cap at 100

    # 3. Recency score
    now = datetime.now()
    recency_scores = []

    for reel in topic_reels:
        hours_ago = (now - reel.post_date).total_seconds() / 3600
        # Decay: 100 at 0 hours, 50 at 48 hours, 10 at 120 hours
        recency = max(100 - (hours_ago * 0.75), 0)
        recency_scores.append(recency)

    avg_recency = sum(recency_scores) / len(recency_scores)

    # 4. Post frequency
    post_count = len(topic_reels)
    frequency_score = min(post_count * 25, 100)  # Cap at 100

    # Final weighted score
    final_score = (
        avg_engagement_rate * 0.40 +
        creator_diversity_score * 0.25 +
        avg_recency * 0.20 +
        frequency_score * 0.15
    )

    return {
        "score": min(final_score, 100),  # Cap at 100
        "engagement_rate": avg_engagement_rate,
        "creator_count": unique_creators,
        "post_count": post_count,
        "avg_likes": sum([r.likes for r in topic_reels]) / post_count,
        "avg_views": sum([r.views for r in topic_reels]) / post_count,
        "most_recent": max([r.post_date for r in topic_reels])
    }
```

---

## 👤 User Workflow

### Complete User Journey

```
┌─────────────────────────────────────────┐
│  User opens app                         │
│  Sees: "Last updated 5 days ago"        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  User clicks "🔄 Refresh Trends"        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  System checks local cache              │
│  - Reads last scrape timestamps         │
│  - Identifies stale data                │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Scraping (2-3 minutes)                 │
│  Progress shown:                        │
│  ✓ Finance with Sharan (8 reels)       │
│  ✓ CA Rachana Ranade (5 reels)         │
│  ✓ CA Sarthak Ahuja (12 reels)         │
│  ...                                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Topic extraction (30 seconds)          │
│  "Analyzing 42 reels..."                │
│  "Found 15 unique topics"               │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Display Results:                       │
│                                         │
│  🔥 TOP 4 TRENDING TOPICS               │
│                                         │
│  1. Budget 2024 Tax Changes    [94/100]│
│     👥 3 creators | 📅 1 day ago       │
│     💬 850 avg likes, 45K avg views    │
│     [View Details] [Generate Script]   │
│                                         │
│  2. SIP vs Fixed Deposit       [87/100]│
│     👥 2 creators | 📅 2 days ago      │
│     ...                                │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  User clicks "View Details" on Topic 1  │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  Shows all reels for that topic:        │
│                                         │
│  Budget 2024 Tax Changes                │
│  ────────────────────────────            │
│  1. @ca_rachanaranade                   │
│     45K views | 2.1K likes              │
│     Posted: 1 day ago                   │
│     [Watch Reel]                        │
│                                         │
│  2. @financewithsharan                  │
│     32K views | 1.8K likes              │
│     Posted: 1 day ago                   │
│     [Watch Reel]                        │
│  ...                                    │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  User clicks "Generate Script"          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  AI generates reel script:              │
│                                         │
│  HOOK (3 sec):                          │
│  "Budget 2024 changed EVERYTHING        │
│   for taxpayers!"                       │
│                                         │
│  INTRO (5 sec):                         │
│  "Hey everyone, [Your name] here..."    │
│                                         │
│  BODY (40 sec):                         │
│  - New tax slabs explained              │
│  - Who benefits most                    │
│  - Example calculation                  │
│                                         │
│  CTA (5 sec):                           │
│  "Follow for more tax tips!"            │
│                                         │
│  [Copy Script] [Regenerate] [Edit]     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  User records reel and posts!           │
└─────────────────────────────────────────┘
```

---

## 🚀 Deployment

### Development Environment

```bash
# Clone repo
git clone <your-repo>
cd trend-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Initialize database
python src/database.py init

# Run Streamlit app
streamlit run app/streamlit_app.py

# Or run CLI
python app/cli.py refresh
```

### Production Deployment

#### Option 1: Streamlit Cloud (Recommended)

```yaml
# Deploy to Streamlit Cloud (free)
1. Push code to GitHub
2. Go to share.streamlit.io
3. Connect your repo
4. Add secrets (API keys) in Streamlit dashboard
5. Deploy!

URL: https://your-app.streamlit.app
```

#### Option 2: Render.com

```yaml
# render.yaml
services:
  - type: web
    name: trend-ai
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app/streamlit_app.py --server.port $PORT
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: APIFY_API_KEY
        sync: false
```

#### Option 3: Self-hosted (VPS/Local)

```bash
# Using systemd service
sudo nano /etc/systemd/system/trend-ai.service

[Unit]
Description=Finance Trend AI
After=network.target

[Service]
User=your_user
WorkingDirectory=/path/to/trend-ai
ExecStart=/path/to/venv/bin/streamlit run app/streamlit_app.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable trend-ai
sudo systemctl start trend-ai
```

---

## 🔑 Environment Variables

```bash
# .env file structure

# Apify API
APIFY_API_KEY=your_apify_key_here

# Groq API (Free)
GROQ_API_KEY=your_groq_key_here

# Database
DATABASE_PATH=./data/trends.db

# Scraping settings
SCRAPE_DAYS_BACK=5
MAX_RESULTS_PER_CREATOR=15
MIN_VIEWS_THRESHOLD=1000

# Scoring weights
ENGAGEMENT_WEIGHT=0.40
CREATOR_DIVERSITY_WEIGHT=0.25
RECENCY_WEIGHT=0.20
FREQUENCY_WEIGHT=0.15
```

---

## 📊 Configuration File

```json
// config.json
{
  "creators": [
    {
      "username": "ca_rachanaranade",
      "display_name": "CA Rachana Ranade",
      "is_active": true
    },
    {
      "username": "ca.sakchijain",
      "display_name": "CA Sakshi Jain",
      "is_active": true
    },
    {
      "username": "casarthakahuja",
      "display_name": "CA Sarthak Ahuja",
      "is_active": true
    },
    {
      "username": "financewithsharan",
      "display_name": "Finance with Sharan",
      "is_active": true
    },
    {
      "username": "invest_aaj_for_kal",
      "display_name": "Invest Aaj For Kal",
      "is_active": true
    }
  ],
  "scraping": {
    "days_back": 5,
    "max_results_per_creator": 15,
    "ignore_pinned": true,
    "min_views_threshold": 500
  },
  "scoring": {
    "top_topics_count": 4,
    "min_engagement_rate": 1.0,
    "weights": {
      "engagement": 0.40,
      "creator_diversity": 0.25,
      "recency": 0.20,
      "frequency": 0.15
    }
  }
}
```

---

## 🔄 Data Flow Example

### Example: User Refreshes Trends

```python
# 1. User clicks "Refresh Trends"
click_refresh()

# 2. System checks cache
last_scrape = get_last_scrape_time()  # "2024-04-01 10:00:00"
now = datetime.now()  # "2024-04-06 15:30:00"
days_since = (now - last_scrape).days  # 5 days

# 3. Scraping triggered (>3 days old)
creators = load_creators_from_config()  # 5 creators
scraped_reels = []

for creator in creators:
    reels = scrape_creator(
        username=creator.username,
        days_back=5,
        max_results=15
    )
    # Returns: 8 reels from ca_rachanaranade

    # Filter pinned
    filtered = filter_pinned_posts(reels)
    # Returns: 6 reels (2 pinned removed)

    # Save to DB
    save_reels_to_db(filtered)
    scraped_reels.extend(filtered)

# Total: 42 reels from 5 creators

# 4. Topic extraction
topics = {}
for reel in scraped_reels:
    topic = extract_topic(reel.caption)
    # "Budget 2024 के tax changes explained 💰"
    # → "Budget 2024 Tax Changes"

    if topic not in topics:
        topics[topic] = []
    topics[topic].append(reel)

# Results:
# {
#   "Budget 2024 Tax Changes": [reel1, reel2, reel3],
#   "SIP vs Fixed Deposit": [reel4, reel5],
#   "Credit Card Cashback": [reel6, reel7, reel8, reel9],
#   ...
# }

# 5. Scoring
scored_topics = []
for topic_name, topic_reels in topics.items():
    score_data = calculate_topic_score(topic_reels)
    # Returns: {
    #   "score": 94,
    #   "engagement_rate": 3.2,
    #   "creator_count": 3,
    #   "post_count": 3,
    #   "avg_likes": 1850,
    #   "avg_views": 42000
    # }

    scored_topics.append({
        "topic": topic_name,
        **score_data
    })

# 6. Ranking
top_topics = sorted(scored_topics, key=lambda x: x["score"], reverse=True)[:4]

# 7. Display to user
display_trending_topics(top_topics)
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Pinned Posts Not Filtered

**Symptom**: Old topics showing as trending

**Solution**:
```python
# Add stricter date filtering
def is_truly_recent(post, days=5):
    cutoff = datetime.now() - timedelta(days=days)
    return post.timestamp >= cutoff

# And check post position
def is_likely_pinned(post, all_posts):
    # If post is in top 3 but older than others
    position = all_posts.index(post)
    if position < 3:
        newer_posts = [p for p in all_posts[3:] if p.timestamp > post.timestamp]
        if len(newer_posts) > 2:
            return True  # Likely pinned
    return False
```

### Issue 2: Apify Rate Limits

**Symptom**: Scraping fails with 429 error

**Solution**:
```python
# Add delay between creator scrapes
import time

for creator in creators:
    reels = scrape_creator(creator)
    time.sleep(5)  # 5 second delay
```

### Issue 3: Similar Topics Not Grouped

**Symptom**: "SIP vs FD" and "SIP vs Fixed Deposit" shown as separate

**Solution**:
```python
# Add topic normalization
TOPIC_ALIASES = {
    "FD": "Fixed Deposit",
    "PPF": "Public Provident Fund",
    "GST": "Goods and Services Tax",
    # ...
}

def normalize_topic(topic):
    for alias, full_name in TOPIC_ALIASES.items():
        topic = topic.replace(alias, full_name)
    return topic
```

### Issue 4: Low Engagement Topics Ranked High

**Symptom**: Topics with 1-2 posts ranked above topics with 5+ posts

**Solution**:
```python
# Add minimum threshold
def filter_valid_topics(topics):
    return {
        name: reels
        for name, reels in topics.items()
        if len(reels) >= 2  # At least 2 posts
        and sum([r.views for r in reels]) >= 10000  # At least 10K total views
    }
```

---

## 📈 Performance Optimization

### Caching Strategy

```python
# Cache LLM results to avoid re-extraction
def extract_topic_cached(caption):
    cache_key = hashlib.md5(caption.encode()).hexdigest()

    # Check cache
    cached = get_from_cache(cache_key)
    if cached:
        return cached

    # Extract with LLM
    topic = extract_topic_with_llm(caption)

    # Store in cache
    save_to_cache(cache_key, topic)
    return topic
```

### Batch Processing

```python
# Extract topics in batches instead of one by one
def extract_topics_batch(captions, batch_size=10):
    topics = []

    for i in range(0, len(captions), batch_size):
        batch = captions[i:i+batch_size]

        # Send batch to LLM
        prompt = f"Extract topics from these captions:\n"
        for j, caption in enumerate(batch):
            prompt += f"{j+1}. {caption}\n"

        response = llm_call(prompt)
        batch_topics = parse_batch_response(response)
        topics.extend(batch_topics)

    return topics
```

---

## 🎯 Success Metrics

Track these metrics to measure tool effectiveness:

```python
# metrics.json
{
  "total_scrapes": 15,
  "total_cost": 1.50,
  "avg_cost_per_scrape": 0.10,
  "total_reels_analyzed": 630,
  "unique_topics_found": 85,
  "avg_topics_per_week": 12,
  "user_content_created": 8,
  "time_saved_hours": 24  # vs manual research
}
```

---

## 🔮 Future Enhancements

1. **Video Thumbnail Analysis**
   - Use GPT-4 Vision to analyze thumbnails
   - Identify trending visual styles

2. **Audio Analysis**
   - Extract trending audio tracks
   - Identify viral sounds

3. **Competitor Tracking**
   - Compare your performance vs tracked creators
   - Identify content gaps

4. **Auto-posting**
   - Generate script
   - Create video from template
   - Auto-post to Instagram

5. **Trend Predictions**
   - ML model to predict which topics will trend
   - Based on historical data

---

## 📝 Summary

### Key Points

1. **Cost-effective**: $5 lasts 20+ months with smart caching
2. **Accurate**: Filters pinned posts, only recent content
3. **Intelligent**: LLM normalizes topics across creators
4. **Actionable**: Top 3-4 topics with clear metrics
5. **Fast**: 2-3 minutes vs 2-3 hours manual research

### Next Steps

1. Set up development environment
2. Get API keys (Apify, Groq)
3. Configure creators list
4. Run first scrape
5. Analyze results
6. Create first reel!

---

**Last Updated**: April 6, 2024
**Version**: 1.0
**Author**: Finance Trend AI Team