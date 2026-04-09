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
    Get a configuration value from:
    1. Streamlit Secrets (for Cloud deployment)
    2. Environment Variables (for local development)
    3. Default value
    """
    # 1. Try Streamlit Secrets first
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except (ImportError, RuntimeError):
        pass
    
    # 2. Try Environment Variables
    val = os.getenv(key)
    if val is not None:
        return val
        
    return default

# API Keys
APIFY_API_KEY = get_config_value("APIFY_API_KEY")
GROQ_API_KEY = get_config_value("GROQ_API_KEY")

# Database
DATABASE_PATH = get_config_value("DATABASE_PATH", str(BASE_DIR / "data" / "trends.db"))
LOG_PATH = BASE_DIR / "data" / "app.log"

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
