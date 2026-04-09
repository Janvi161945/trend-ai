import streamlit as st
import pandas as pd
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from src.config import load_user_config
from src.database import get_connection, init_db
from src.generators import content_generator
from src.generators.reel_idea_generator import generate_ideas_from_reels, format_reel_idea_output
from src.scoring.multi_signal_trend_detector import detect_trending_topics, format_trending_output
from app.cli import refresh_trends
from src.logger import get_recent_logs

# Set page config
st.set_page_config(
    page_title="Finance Trend AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Monzo Wealth Light Theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #ffffff;
    }
    
    .stApp {
        background-color: #f9fafb;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stText, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #111827 !important;
    }
    
    /* Ensure primary buttons stay readable */
    [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] p {
        color: #ffffff !important;
    }
    
    /* Trends Card styling */
    .trend-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 20px;
        border: 1px solid #e5e7eb;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .topic-title {
        color: #111827 !important;
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 12px;
    }
    
    .metric-value {
        color: #059669 !important;
        font-size: 22px;
        font-weight: 700;
    }
    
    .metric-label {
        color: #4b5563 !important;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 700;
    }

    /* Expander text */
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #111827 !important;
    }

    /* Buttons */
    .stButton>button {
        background: #111827;
        color: #ffffff;
        border: none;
        padding: 14px 28px;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton>button:hover {
        background: #000000;
        color: #10b981;
        transform: scale(1.02);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #f0fdf4 !important;
        border-radius: 12px !important;
        border: 1px solid #dcfce7 !important;
        color: #166534 !important;
        font-weight: 600 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
    }
    ::-webkit-scrollbar-track {
        background: #f8fafc;
    }
    ::-webkit-scrollbar-thumb {
        background: #e2e8f0;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #cbd5e1;
    }

    /* Custom Toggle styling */
    div[data-testid="stToggle"] > label > div {
        border-color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_last_refresh_time():
    """Get the last refresh time from the creators' last_scraped_at."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(last_scraped_at) as last_refresh FROM creators")
    result = cursor.fetchone()
    conn.close()
    return result["last_refresh"] if result and result["last_refresh"] else "Never"

def get_trending_topics():
    """Fetch top topics from topic_scores table."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM topic_scores ORDER BY score DESC LIMIT 4", conn)
    conn.close()
    return df

def get_reels_for_topic(topic_name):
    """Fetch reels for a specific topic."""
    conn = get_connection()
    query = """
        SELECT r.instagram_id, r.caption, r.likes, r.comments, r.views, r.post_date, r.post_url, c.username
        FROM reels r
        JOIN topics t ON r.id = t.reel_id
        JOIN creators c ON r.creator_id = c.id
        WHERE t.topic_name = ?
        ORDER BY r.views DESC
    """
    df = pd.read_sql_query(query, conn, params=(topic_name,))
    conn.close()
    return df

def get_all_recent_reels():
    """Fetch all recent reels (last 7 days) for analysis."""
    conn = get_connection()
    query = """
        SELECT r.caption, r.likes, r.comments, r.views, r.post_date, c.username as creator_name
        FROM reels r
        JOIN creators c ON r.creator_id = c.id
        WHERE r.post_date >= datetime('now', '-7 days')
        ORDER BY r.post_date DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df.to_dict('records')

def main():
    # Header
    st.markdown("""
        <div style="padding: 10px 0 20px 0; margin-bottom: 10px;">
            <h1 style="font-size: 48px; font-weight: 800; background: linear-gradient(90deg, #10b981, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px;">
                Finance Trend discovery
            </h1>
            <p style="color: #94a3b8; font-size: 18px; margin: 0;">
                AI-powered insights for viral finance content.
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        last_refresh = get_last_refresh_time()

        if last_refresh and last_refresh != "Never":
            try:
                last_refresh_dt = datetime.fromisoformat(last_refresh)
                time_ago = datetime.now() - last_refresh_dt
                hours_ago = int(time_ago.total_seconds() / 3600)
                if hours_ago < 1:
                    time_str = f"{int(time_ago.total_seconds() / 60)} minutes ago"
                elif hours_ago < 24:
                    time_str = f"{hours_ago} hours ago"
                else:
                    time_str = f"{int(time_ago.days)} days ago"
                st.write(f"**Last Updated:** {time_str}")
            except:
                st.write(f"**Last Updated:** {last_refresh}")
        else:
            st.write("**Last Updated:** Never")

        st.markdown("""
            <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                        padding: 12px;
                        border-radius: 12px;
                        margin-bottom: 16px;
                        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                        text-align: center;">
                <p style="color: white; font-weight: 700; font-size: 14px; margin: 0;">
                    💡 Click below to scrape latest reels & update trends
                </p>
            </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 Refresh Trends", use_container_width=True, type="primary"):
            with st.spinner("Scraping last 2-3 days of reels... (takes 2-3 mins)"):
                refresh_trends()
                st.success("✅ Trends refreshed successfully!")
                st.rerun()

        st.divider()
        st.subheader("📊 Tracked Creators")
        st.caption("Toggle creators ON/OFF for scraping to control costs")

        config = load_user_config()

        # Get creator stats from database
        conn = get_connection()
        cursor = conn.cursor()

        # Track if any changes were made
        config_changed = False
        
        # Creators list

        for idx, creator in enumerate(config.get("creators", [])):
            username = creator['username']
            display_name = creator.get('display_name', username)
            is_currently_active = creator.get("is_active", True)

            # Get reel count for this creator (last 3 days)
            cursor.execute("""
                SELECT COUNT(*) as reel_count
                FROM reels r
                JOIN creators c ON r.creator_id = c.id
                WHERE c.username = ?
                AND r.post_date >= datetime('now', '-3 days')
            """, (username,))
            result = cursor.fetchone()
            reel_count = result['reel_count'] if result else 0

            # Create toggle switch layout
            col1, col2 = st.columns([4, 1])

            with col1:
                st.write(f"**{display_name}**")
                if reel_count > 0:
                    st.caption(f"{reel_count} reels (3 days)")

            with col2:
                # Use native Streamlit toggle
                is_active = st.toggle(" ", value=is_currently_active, key=f"toggle_{username}")
                
                if is_active != is_currently_active:
                    creator['is_active'] = is_active
                    config_changed = True
                    
                    # Save immediately
                    import json
                    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
                    with open(config_path, 'w') as f:
                        json.dump(config, f, indent=2)
                    st.rerun()

        conn.close()

        # Save config if changes were made
        if config_changed:
            import json
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            st.success("✅ Creator settings saved!")

        # Removed active creator count metric as requested

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🔥 Trending Topics", "💡 Content Ideas", "📑 Activity Logs"])

    with tab1:
        # Main Content - Trending Topics
        st.markdown("""
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
                        padding: 16px;
                        border-radius: 12px;
                        border-left: 4px solid #3b82f6;
                        margin-bottom: 24px;">
                <p style="margin: 0; color: #1e40af; font-size: 15px; font-weight: 600; line-height: 1.6;">
                    📊 <strong>What you get here:</strong> Discover trending topics ranked by engagement scores, creator participation, and recent activity.
                    View detailed metrics including trending scores, average views, post counts, and top-performing content from tracked creators.
                </p>
            </div>
        """, unsafe_allow_html=True)

        trends_df = get_trending_topics()

        if trends_df.empty:
            st.warning("No trends found. Click 'Refresh Trends' in the sidebar to discover topics.")
        else:
            st.header("🔥 Top Trending Topics")

            for index, row in trends_df.iterrows():
                with st.container():
                    # Determine suggestion based on score
                    score = row['score']
                    if score >= 70:
                        suggestion = "🔥 Hot trend! Create content NOW for maximum reach."
                        badge_color = "#10b981"
                    elif score >= 50:
                        suggestion = "📈 Rising trend. Good opportunity to create content."
                        badge_color = "#f59e0b"
                    elif score >= 30:
                        suggestion = "⚡ Emerging topic. Early mover advantage possible."
                        badge_color = "#3b82f6"
                    else:
                        suggestion = "📊 Growing interest. Monitor for future opportunities."
                        badge_color = "#6b7280"

                    st.markdown(f"""
                    <div class="trend-card">
                        <div class="topic-title">{row['topic_name']}</div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 15px; gap: 20px;">
                            <div>
                                <div class="metric-label">Trending Score</div>
                                <div class="metric-value">{row['score']:.1f}/100</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="metric-label">Creators</div>
                                <div style="color: #3b82f6; font-size: 20px; font-weight: 700;">{row['creator_count']}</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="metric-label">Avg Views</div>
                                <div style="color: #8b5cf6; font-size: 20px; font-weight: 700;">{int(row['avg_views']):,}</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="metric-label">Post Count</div>
                                <div style="color: #ec4899; font-size: 20px; font-weight: 700;">{int(row['post_count'])}</div>
                            </div>
                        </div>
                        <div style="margin-top: 16px; padding: 12px; background-color: {badge_color}15; border-left: 4px solid {badge_color}; border-radius: 8px;">
                            <p style="margin: 0; color: {badge_color}; font-weight: 600; font-size: 14px;">{suggestion}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Get reels for analysis
                    reels_df = get_reels_for_topic(row['topic_name'])

                    if not reels_df.empty:
                        # Calculate reel analysis metrics
                        total_engagement = reels_df['likes'].sum() + reels_df['comments'].sum()
                        avg_engagement_rate = (total_engagement / reels_df['views'].sum() * 100) if reels_df['views'].sum() > 0 else 0
                        top_creator = reels_df.iloc[0]['username'] if len(reels_df) > 0 else "N/A"

                        st.markdown(f"""
                        <div style="background-color: #f0fdf4; padding: 16px; border-radius: 12px; margin-top: 16px; border: 1px solid #dcfce7;">
                            <h4 style="color: #166534; margin: 0 0 12px 0; font-size: 16px;">📊 Reel Analysis</h4>
                            <div style="display: flex; gap: 24px; flex-wrap: wrap;">
                                <div>
                                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Total Reels</span>
                                    <p style="color: #059669; font-size: 18px; font-weight: 700; margin: 4px 0 0 0;">{len(reels_df)}</p>
                                </div>
                                <div>
                                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Avg Engagement</span>
                                    <p style="color: #059669; font-size: 18px; font-weight: 700; margin: 4px 0 0 0;">{avg_engagement_rate:.1f}%</p>
                                </div>
                                <div>
                                    <span style="color: #6b7280; font-size: 12px; text-transform: uppercase; font-weight: 600;">Top Creator</span>
                                    <p style="color: #059669; font-size: 18px; font-weight: 700; margin: 4px 0 0 0;">@{top_creator}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with st.expander(f"👀 View {len(reels_df)} Reels"):
                        for i, reel in reels_df.iterrows():
                            st.write(f"**@{reel['username']}** - {int(reel['views']):,} views")
                            st.caption(f"{reel['caption'][:100]}...")
                            st.write(f"[Watch Reel]({reel['post_url']})")
                            st.divider()

                    st.divider()

    with tab2:
        # Content Ideas Tab
        st.markdown("""
            <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                        padding: 16px;
                        border-radius: 12px;
                        border-left: 4px solid #f59e0b;
                        margin-bottom: 24px;">
                <p style="margin: 0; color: #92400e; font-size: 15px; font-weight: 600; line-height: 1.6;">
                    💡 <strong>What you get here:</strong> AI-powered content suggestions generated by analyzing recent reel captions from all your tracked creators.
                    Get actionable ideas with topic themes, viral angles, and reasoning behind each suggestion. Click "Generate Ideas" to create fresh content recommendations.
                </p>
            </div>
        """, unsafe_allow_html=True)
        st.header("💡 AI-Generated Content Ideas")

        if st.button("🎬 Generate Ideas", use_container_width=True):
            with st.spinner("Analyzing trending captions and generating ideas..."):
                recent_reels = get_all_recent_reels()

                if not recent_reels:
                    st.warning("No recent reels found. Refresh trends first.")
                else:
                    ideas = generate_ideas_from_reels(recent_reels)

                    if ideas:
                        st.success(f"Generated {len(ideas)} content ideas!")

                        for i, idea in enumerate(ideas, 1):
                            with st.expander(f"💡 Idea {i}: {idea['reel_idea']}", expanded=(i <= 3)):
                                st.markdown(f"**Topic:** {idea['topic']}")
                                st.markdown(f"**Why it's trending:** {idea['reason']}")
                    else:
                        st.warning("Could not generate ideas. Try again.")

    with tab3:
        # Activity Logs Tab
        st.markdown("""
            <div style="background-color: #f8fafc; padding: 16px; border-radius: 12px; border-left: 4px solid #64748b; margin-bottom: 24px;">
                <p style="margin: 0; color: #475569; font-size: 15px; font-weight: 600;">
                    📑 <strong>System Activity:</strong> View the detailed execution logs of the scraping and analysis process.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.header("📑 Recent Activity Logs")
        
        logs = get_recent_logs(100)
        log_text = "".join(logs)
        
        st.code(log_text if log_text.strip() else "No recent activity recorded. Click 'Refresh Trends' in the sidebar to start.", language="text")
        
        if st.button("🔄 Refresh Log View"):
            st.rerun()


if __name__ == "__main__":
    main()
