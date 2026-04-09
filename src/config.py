import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Try to load from Streamlit Secrets (Cloud)
# Fallback to os.getenv (Local)
try:
    import streamlit as st
    APIFY_API_KEY = st.secrets.get("APIFY_API_KEY")
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    DATABASE_PATH = st.secrets.get("DATABASE_PATH")
    SCRAPE_DAYS_BACK = st.secrets.get("SCRAPE_DAYS_BACK")
    MAX_RESULTS_PER_CREATOR = st.secrets.get("MAX_RESULTS_PER_CREATOR")
    MIN_VIEWS_THRESHOLD = st.secrets.get("MIN_VIEWS_THRESHOLD")
    ENGAGEMENT_WEIGHT = st.secrets.get("ENGAGEMENT_WEIGHT")
    CREATOR_DIVERSITY_WEIGHT = st.secrets.get("CREATOR_DIVERSITY_WEIGHT")
    RECENCY_WEIGHT = st.secrets.get("RECENCY_WEIGHT")
    FREQUENCY_WEIGHT = st.secrets.get("FREQUENCY_WEIGHT")
except Exception:
    APIFY_API_KEY = None
    GROQ_API_KEY = None
    DATABASE_PATH = None
    SCRAPE_DAYS_BACK = None
    MAX_RESULTS_PER_CREATOR = None
    MIN_VIEWS_THRESHOLD = None
    ENGAGEMENT_WEIGHT = None
    CREATOR_DIVERSITY_WEIGHT = None
    RECENCY_WEIGHT = None
    FREQUENCY_WEIGHT = None

# Apply defaults if values are still None (from os.getenv fallback)
APIFY_API_KEY = APIFY_API_KEY or os.getenv("APIFY_API_KEY")
GROQ_API_KEY = GROQ_API_KEY or os.getenv("GROQ_API_KEY")
DATABASE_PATH = DATABASE_PATH or os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "trends.db"))
LOG_PATH = str(BASE_DIR / "data" / "app.log")

# Settings with defaults
SCRAPE_DAYS_BACK = int(SCRAPE_DAYS_BACK or os.getenv("SCRAPE_DAYS_BACK", 5))
MAX_RESULTS_PER_CREATOR = int(MAX_RESULTS_PER_CREATOR or os.getenv("MAX_RESULTS_PER_CREATOR", 15))
MIN_VIEWS_THRESHOLD = int(MIN_VIEWS_THRESHOLD or os.getenv("MIN_VIEWS_THRESHOLD", 1000))

# Scoring Weights
ENGAGEMENT_WEIGHT = float(ENGAGEMENT_WEIGHT or os.getenv("ENGAGEMENT_WEIGHT", 0.40))
CREATOR_DIVERSITY_WEIGHT = float(CREATOR_DIVERSITY_WEIGHT or os.getenv("CREATOR_DIVERSITY_WEIGHT", 0.25))
RECENCY_WEIGHT = float(RECENCY_WEIGHT or os.getenv("RECENCY_WEIGHT", 0.20))
FREQUENCY_WEIGHT = float(FREQUENCY_WEIGHT or os.getenv("FREQUENCY_WEIGHT", 0.15))

# Dynamic Getters for Thread-safety
def get_apify_key():
    return APIFY_API_KEY

def get_groq_key():
    return GROQ_API_KEY

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
