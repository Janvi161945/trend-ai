import instaloader
from datetime import datetime, timedelta
from src.config import MAX_RESULTS_PER_CREATOR

def get_posts_instaloader(username, results_limit=MAX_RESULTS_PER_CREATOR):
    """
    Fetch posts using Instaloader (Free fallback).
    Note: Highly rate-limited and might require login for full data.
    """
    L = instaloader.Instaloader()
    
    try:
        profile = instaloader.Profile.from_username(L.context, username)
        
        results = []
        count = 0
        
        for post in profile.get_posts():
            if count >= results_limit:
                break
            
            # Filter for reels/videos only if possible
            if not post.is_video:
                 continue
                 
            # Map item properties to consistent post object
            post_obj = {
                "id": post.shortcode,
                "caption": post.caption,
                "timestamp": post.date_utc.isoformat(),
                "likes": post.likes,
                "comments": post.comments,
                "views": post.video_view_count if post.video_view_count else 0,
                "type": "Reel" if post.is_video else "Image",
                "url": f"https://www.instagram.com/p/{post.shortcode}/",
                "position": count,
                "isPinned": False # Instaloader doesn't easily expose pinned flag
            }
            results.append(post_obj)
            count += 1
            
        return results
        
    except Exception as e:
        print(f"Instaloader failed for @{username}: {e}")
        return []
