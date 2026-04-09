# API Key Setup Guide 🔐

To use the Finance Trend AI tool, you need to set up two API keys and add them to your `.env` file.

## 1. Apify API Key (Instagram Scraping)

**Apify** is used to scrape Instagram profiles without getting blocked immediately.

1.  **Create an Account**: Go to [apify.com](https://apify.com) and sign up for a free account.
2.  **Get API Key**: In the Apify Console, go to **Settings** > **Integrations** to find your Personal API Token.
3.  **Budget**: The free tier includes a certain amount of platform usage. Our tool is optimized to stay within $5/month (or even the free tier) by caching data and only scraping recent content.

## 2. Groq API Key (AI Topic Extraction)

**Groq** provides fast and free (within limits) LLM models for text analysis.

1.  **Create an Account**: Go to [console.groq.com](https://console.groq.com) and sign up.
2.  **Get API Key**: In the Groq Console, go to **API Keys** and generate a new key.
3.  **Model**: This tool uses `llama-3.1-8b-instant`, which is highly efficient for topic extraction.

---

## Final Step: Configure `.env`

Once you have your keys, add them to the `.env` file in the root directory:

```bash
# Apify API
APIFY_API_KEY=apify_api_XXXXXXXXXXXXXXX

# Groq API (Free)
GROQ_API_KEY=gsk_XXXXXXXXXXXXXXXXXXXX
```

Your setup is now complete!
