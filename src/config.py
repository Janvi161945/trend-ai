import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

def get_config_value(key, default=None):
    """
    Highly robust configuration getter that checks:
    1. Streamlit Secrets (Official way for Cloud)
    2. Environment Variables (Local dev)
    3. Case-insensitive versions
    """
    # 1. Try Streamlit Secrets
    try:
        import streamlit as st
        # st.secrets behaves like a nested dict. Check top level first.
        if key in st.secrets:
            return st.secrets[key]
        
        # Check all keys case-insensitively
        for s_key in st.secrets.keys():
            if s_key.lower() == key.lower():
                return st.secrets[s_key]
    except:
        pass
    
    # 2. Try Environment Variables
    val = os.getenv(key)
    if val is not None:
        return val
        
    # Check case-insensitive env vars
    for env_key, env_val in os.environ.items():
        if env_key.lower() == key.lower():
            return env_val
            
    return default

def get_apify_key():
    return get_config_value("APIFY_API_KEY")

def get_groq_key():
    return get_config_value("GROQ_API_KEY")

# For static assignments (legacy support)
APIFY_API_KEY = get_config_value("APIFY_API_KEY")
GROQ_API_KEY = get_config_value("GROQ_API_KEY")

# Database
DATABASE_PATH = get_config_value("DATABASE_PATH", str(BASE_DIR / "data" / "trends.db"))
LOG_PATH = str(BASE_DIR / "data" / "app.log")

# Scraping settings
SCRAPE_DAYS_BACK = int(get_config_value("SCRAPE_DAYS_BACK", 5))
MAX_RESULTS_PER_CREATOR = int(get_config_value("MAX_RESULTS_PER_CREATOR", 15))
MIN_VIEWS_THRESHOLD = int(get_config_value("MIN_VIEWS_THRESHOLD", 1000))

# Scoring Weights
ENGAGEMENT_WEIGHT = float(get_config_value("ENGAGEMENT_WEIGHT", 0.40))
CREATOR_DIVERSITY_WEIGHT = float(get_config_value("CREATOR_DIVERSITY_WEIGHT", 0.25))
RECENCY_WEIGHT = float(get_config_value("RECENCY_WEIGHT", 0.20))
FREQUENCY_WEIGHT = float(get_config_value("FREQUENCY_WEIGHT", 0.15))

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
