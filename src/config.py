import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "data" / "trends.db"))
LOG_PATH = BASE_DIR / "data" / "app.log"

# Scraping settings
SCRAPE_DAYS_BACK = int(os.getenv("SCRAPE_DAYS_BACK", 5))
MAX_RESULTS_PER_CREATOR = int(os.getenv("MAX_RESULTS_PER_CREATOR", 15))
MIN_VIEWS_THRESHOLD = int(os.getenv("MIN_VIEWS_THRESHOLD", 1000))

# Scoring Weights
ENGAGEMENT_WEIGHT = float(os.getenv("ENGAGEMENT_WEIGHT", 0.40))
CREATOR_DIVERSITY_WEIGHT = float(os.getenv("CREATOR_DIVERSITY_WEIGHT", 0.25))
RECENCY_WEIGHT = float(os.getenv("RECENCY_WEIGHT", 0.20))
FREQUENCY_WEIGHT = float(os.getenv("FREQUENCY_WEIGHT", 0.15))

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
