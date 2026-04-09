# Deploying Finance Trend AI for FREE 🚀

The easiest and best way to deploy your Streamlit app for free is using **Streamlit Community Cloud**.

## Step 1: Push your code to GitHub
1. Create a new repository on [GitHub](https://github.com).
2. Initialize git in your local folder (if not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
3. Link to your GitHub repo and push:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git branch -M main
   git push -u origin main
   ```
   *Note: Make sure your `.env` and `data/trends.db` are in `.gitignore` so you don't leak your keys!*

## Step 2: Deploy to Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io).
2. Click **"New app"**.
3. Select your repository, the `main` branch, and set the main file path to:
   `app/streamlit_app.py`
4. Click **"Deploy!"**.

## Step 3: Configure API Keys (Secrets)
Your app will fail initially because it won't have your API keys. 
1. In your Streamlit Cloud dashboard, go to **Settings** -> **Secrets**.
2. Copy and paste the contents of your `.env` file into the secrets box in this format:
   ```toml
   APIFY_API_KEY = "your_apify_key"
   GROQ_API_KEY = "your_groq_key"
   DATABASE_PATH = "./data/trends.db"
   SCRAPE_DAYS_BACK = 3
   MAX_RESULTS_PER_CREATOR = 15
   MIN_VIEWS_THRESHOLD = 500
   ENGAGEMENT_WEIGHT = 0.40
   CREATOR_DIVERSITY_WEIGHT = 0.25
   RECENCY_WEIGHT = 0.20
   FREQUENCY_WEIGHT = 0.15
   ```
3. Click **Save**. The app will automatically reboot and work!

## ⚠️ Important Note on Data
Streamlit Community Cloud uses a **volatile filesystem**. This means:
* Your `data/trends.db` file will be created when you first run the app.
* If the app "goes to sleep" or the server reboots (which happens occasionally), your database might reset.
* **The fix**: Since your app is a tracker, you can simply click "Refresh Trends" to fetch the latest data whenever you need it. 

If you want a permanent database that never resets, you can use **Turso** (a free cloud SQLite database) and update the `DATABASE_PATH` in your secrets to the Turso URL.
