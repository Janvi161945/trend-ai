import sqlite3
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.config import DATABASE_PATH

def get_connection():
    """Establish a connection to the database."""
    # Ensure directory exists
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Construct database schema."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Creators table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS creators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT,
        followers INTEGER,
        last_scraped_at TIMESTAMP,
        last_post_id TEXT,
        last_post_date TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Reels table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        creator_id INTEGER NOT NULL,
        instagram_id TEXT UNIQUE,
        caption TEXT,
        likes INTEGER DEFAULT 0,
        comments INTEGER DEFAULT 0,
        views INTEGER DEFAULT 0,
        post_date TIMESTAMP NOT NULL,
        post_url TEXT,
        is_pinned BOOLEAN DEFAULT 0,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (creator_id) REFERENCES creators(id)
    )
    ''')
    
    # Extracted topics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_name TEXT NOT NULL,
        reel_id INTEGER NOT NULL,
        extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (reel_id) REFERENCES reels(id)
    )
    ''')
    
    # Topic scores table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS topic_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic_name TEXT UNIQUE NOT NULL,
        score REAL NOT NULL,
        engagement_rate REAL,
        creator_count INTEGER,
        post_count INTEGER,
        avg_likes INTEGER,
        avg_views INTEGER,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reels_post_date ON reels(post_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reels_creator_id ON reels(creator_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_topics_topic_name ON topics(topic_name)')
    
    conn.commit()
    conn.close()

def get_creator_cache_info(username):
    """Get the last scraped post info for incremental scraping."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT last_post_id, last_post_date, last_scraped_at
        FROM creators
        WHERE username = ?
    """, (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            "last_post_id": result["last_post_id"],
            "last_post_date": result["last_post_date"],
            "last_scraped_at": result["last_scraped_at"]
        }
    return None

def update_creator_cache(username, latest_post_id, latest_post_date):
    """Update the creator's cache with the most recent post info."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE creators
        SET last_post_id = ?, last_post_date = ?, last_scraped_at = ?
        WHERE username = ?
    """, (latest_post_id, latest_post_date, datetime.now().isoformat(), username))
    conn.commit()
    conn.close()

def get_recent_reels_for_analysis(days_back=7):
    """Get all reels from the last N days for trend analysis."""
    from datetime import timedelta
    cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, c.username, c.display_name
        FROM reels r
        JOIN creators c ON r.creator_id = c.id
        WHERE r.post_date >= ?
        ORDER BY r.post_date DESC
    """, (cutoff_date,))

    reels = []
    for row in cursor.fetchall():
        reels.append({
            "id": row["instagram_id"],
            "caption": row["caption"],
            "likes": row["likes"],
            "comments": row["comments"],
            "views": row["views"],
            "timestamp": row["post_date"],
            "url": row["post_url"],
            "creator_id": row["creator_id"],
            "username": row["username"]
        })

    conn.close()
    return reels

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        init_db()
        print(f"Database initialized at {DATABASE_PATH}.")
