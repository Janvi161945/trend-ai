from groq import Groq
from src.config import GROQ_API_KEY

def extract_topic(caption):
    """
    Extract core finance topic from Instagram caption using Groq's LLM.
    Enhanced for actionable, creator-friendly topic extraction.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""You are an expert finance content strategist helping creators identify trending topics.

Extract the CORE ACTIONABLE topic from this Instagram reel caption.
The topic should be:
- Specific enough for a creator to make a reel about
- Finance/money related
- 2-5 words maximum
- No emojis or special characters

IMPORTANT: Group similar topics together using consistent naming:
- "SIP vs FD", "FD vs SIP", "SIP या FD" → "SIP vs Fixed Deposit"
- "Tax saving tips", "How to save tax" → "Tax Saving Tips"
- "Credit card tips", "Best credit cards" → "Credit Card Strategy"
- "Stock market crash", "Market crash explained" → "Stock Market Crash"

Examples:
Caption: "SIP vs FD - which is better for you? 📊 #investment"
Topic: SIP vs Fixed Deposit

Caption: "Budget 2024 के tax changes explained in Hindi 💰"
Topic: Budget 2024 Tax Changes

Caption: "5 credit card mistakes that are costing you money! 💳"
Topic: Credit Card Mistakes

Caption: "How to buy your first stock? Step by step guide 📈"
Topic: How to Buy Stocks

Caption: "Mutual fund SIP returns after 10 years 🚀"
Topic: SIP Long-term Returns

Caption: "Why the stock market crashed today? Real reason 📉"
Topic: Stock Market Crash

Caption: "GST on online gaming - what it means for you"
Topic: GST on Online Gaming

Now extract the topic:
Caption: "{caption}"
Topic:"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,  # Lower for more consistent grouping
        max_tokens=30
    )

    topic = response.choices[0].message.content.strip()

    # Clean up the topic
    topic = topic.replace('"', '').replace("'", "").strip()

    # If topic is too long or invalid, return a generic placeholder
    if len(topic) > 50 or len(topic.split()) > 6:
        return "Finance Topic"

    return topic

def normalize_topic(topic):
    """
    Normalize topic names for better clustering.
    Handles common abbreviations and variations.
    """
    # Common finance term normalizations
    normalizations = {
        "FD": "Fixed Deposit",
        "PPF": "Public Provident Fund",
        "EPF": "Employees Provident Fund",
        "NPS": "National Pension Scheme",
        "ELSS": "ELSS Mutual Fund",
        "GST": "GST",  # Keep as is
        "ITR": "Income Tax Return",
        "PAN": "PAN Card",
        "KYC": "KYC",  # Keep as is
        "SIP": "SIP",  # Keep as is (well known)
        "IPO": "IPO",  # Keep as is
        "Demat": "Demat Account",
        "MF": "Mutual Fund",
        "LIC": "LIC",
    }

    # Apply normalizations
    words = topic.split()
    normalized_words = []

    for word in words:
        # Check if word is in normalization dict
        if word in normalizations:
            normalized_words.append(normalizations[word])
        else:
            normalized_words.append(word)

    return " ".join(normalized_words)


def is_valid_finance_topic(topic):
    """
    Validate if topic is relevant and actionable for finance creators.
    Filters out generic/spam topics.
    """
    topic_lower = topic.lower()

    # Reject generic/spam topics
    reject_keywords = [
        "follow", "like", "subscribe", "share", "comment",
        "link in bio", "dm me", "check out",
        "giveaway", "contest", "winner",
        "finance topic",  # Our placeholder for invalid extractions
    ]

    for keyword in reject_keywords:
        if keyword in topic_lower:
            return False

    # Topic should have at least 2 words for specificity
    if len(topic.split()) < 2:
        return False

    # Reject topics that are too long (likely extraction error)
    if len(topic.split()) > 7:
        return False

    return True


def cluster_topics(reels):
    """
    Group reels by extracted topic with quality validation.
    Only returns high-quality, actionable topics for creators.
    """
    topics = {}
    skipped_count = 0

    for reel in reels:
        # Check if reel has caption
        caption = reel.get("caption", "")
        if not caption or len(caption.strip()) < 10:
            skipped_count += 1
            continue

        try:
            # Extract topic
            topic = extract_topic(caption)

            # Normalize topic
            topic = normalize_topic(topic)

            # Validate topic quality
            if not is_valid_finance_topic(topic):
                skipped_count += 1
                continue

            # Add to topics dict
            if topic not in topics:
                topics[topic] = []

            topics[topic].append(reel)

        except Exception as e:
            print(f"  ⚠️  Error extracting topic: {e}")
            skipped_count += 1
            continue

    if skipped_count > 0:
        print(f"  ℹ️  Skipped {skipped_count} reels (invalid caption/topic)")

    return topics
