# Finance Trend AI 📈

AI-powered Trend Discovery Tool for Instagram Creators. Scrapes recent reels from top finance creators, identifies trending topics using AI, and generates viral content scripts.

## 🚀 Key Features

*   **Smart Scraping**: Fetches recent reels (3-5 days) from tracked creators.
*   **Pinned Post Filtering**: Heuristics to remove old pinned content for accurate trend analysis.
*   **AI Topic Extraction**: Uses LLMs (Groq/Llama 3.1) to normalize captions into clear topics.
*   **Engagement Scoring**: Ranks topics based on engagement rate, creator diversity, recency, and frequency.
*   **Script Generation**: Automatically generates hooks, intros, bodies, and CTAs for trending topics.
*   **Dashboard**: Clean Streamlit interface to view trends and manage creators.

## 📦 Tech Stack

- **Backend**: Python 3.10+, SQLite
- **AI/LLM**: Groq (Llama 3.1)
- **Scraping**: Apify (Primary), Instaloader (Fallback)
- **UI**: Streamlit

## 🛠️ Setup

1.  **Clone the Repository**:
    ```bash
    git clone https://your-repo-url.git
    cd trend-ai
    ```

2.  **Environment Setup**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure API Keys**:
    - Copy `.env.example` to `.env`.
    - Add your `APIFY_API_KEY` and `GROQ_API_KEY`.

4.  **Initialize Database**:
    ```bash
    python src/database.py init
    ```

## 🏃 Running the Application

### Option 1: Streamlit Dashboard (UI)
```bash
streamlit run app/streamlit_app.py
```

### Option 2: CLI (Terminal)
```bash
python app/cli.py refresh
```

## 📁 Project Structure

```text
trend-ai/
├── src/                 # Source code
│   ├── scrapers/        # Instagram scraping logic
│   ├── extractors/      # Topic extraction & filtering
│   ├── scoring/         # Trend ranking algorithms
│   └── generators/      # AI script generation
├── app/                 # Entry points (Streamlit & CLI)
├── data/                # Local SQLite database
└── docs/                # Documentation & Architecture
```

## 🔑 Environment Variables

Check `.env.example` for the full list of configuration options including scraping window and scoring weights.

## 📄 License

MIT
