import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

def _get_initial_config(key, default=None):
    """
    Lookup configuration once at startup. 
    This MUST be called from the main thread on Streamlit Cloud.
    """
    # 1. Try Streamlit Secrets
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
        for s_key in st.secrets.keys():
            if s_key.lower() == key.lower():
                return st.secrets[s_key]
    except:
        pass
    
    # 2. Try Environment Variables
    val = os.getenv(key)
    if val is not None:
        return val
            
    return default

# "Lock in" the values from the main thread at startup
_APIFY_KEY_CACHED = _get_initial_config("APIFY_API_KEY")
_GROQ_KEY_CACHED = _get_initial_config("GROQ_API_KEY")

# Thread-safe accessors
def get_apify_key():
    return _APIFY_KEY_CACHED

def get_groq_key():
    return _GROQ_KEY_CACHED

# Legacy support
APIFY_API_KEY = _APIFY_KEY_CACHED
GROQ_API_KEY = _GROQ_KEY_CACHED

# Database
DATABASE_PATH = _get_initial_config("DATABASE_PATH", str(BASE_DIR / "data" / "trends.db"))
LOG_PATH = str(BASE_DIR / "data" / "app.log")

# Scraping settings
SCRAPE_DAYS_BACK = int(_get_initial_config("SCRAPE_DAYS_BACK", 5))
MAX_RESULTS_PER_CREATOR = int(_get_initial_config("MAX_RESULTS_PER_CREATOR", 15))
MIN_VIEWS_THRESHOLD = int(_get_initial_config("MIN_VIEWS_THRESHOLD", 1000))

# Scoring Weights
ENGAGEMENT_WEIGHT = float(_get_initial_config("ENGAGEMENT_WEIGHT", 0.40))
CREATOR_DIVERSITY_WEIGHT = float(_get_initial_config("CREATOR_DIVERSITY_WEIGHT", 0.25))
RECENCY_WEIGHT = float(_get_initial_config("RECENCY_WEIGHT", 0.20))
FREQUENCY_WEIGHT = float(_get_initial_config("FREQUENCY_WEIGHT", 0.15))

def load_user_config():
    """Load configuration from config.json."""
    config_path = BASE_DIR / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {"creators": []}

def save_user_config(config):
    """Save configuration to config.json."""
    config_path = BASE_DIR / "config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)
