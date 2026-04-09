from groq import Groq
from src.config import GROQ_API_KEY
import json


def extract_topic_with_confidence(caption):
    """
    Extract the main finance topic from a reel caption with confidence scoring.

    Rules:
    - Keep topics short (2-5 words)
    - Be specific (avoid generic topics like "Finance tips")
    - Group similar topics logically but don't over-merge
    - Focus on content idea, not general theme

    Returns:
        dict: {"topic": str, "confidence": int (0-100)}

    Examples:
        Caption: "3 tax saving tips for salaried employees before March"
        → {"topic": "Tax saving for salaried", "confidence": 95}

        Caption: "SIP vs FD which is better for beginners"
        → {"topic": "SIP vs FD", "confidence": 90}

        Caption: "How I built emergency fund in 6 months"
        → {"topic": "Emergency fund building", "confidence": 85}
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""You are a JSON API. Return ONLY valid JSON, no explanations or markdown.

Extract the main topic from this caption (2-5 words, specific):

Caption: {caption}

Return this exact JSON structure (NO markdown, NO code blocks):

{{
    "topic": "specific topic name",
    "confidence": 85
}}"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=100
    )

    result_text = response.choices[0].message.content.strip()

    # Parse JSON response
    try:
        # Clean up response - remove common LLM artifacts
        result_text = result_text.strip()

        # Remove markdown code blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        # Remove text before first {
        if "{" in result_text:
            result_text = result_text[result_text.find("{"):]

        # Remove text after last }
        if "}" in result_text:
            result_text = result_text[:result_text.rfind("}")+1]

        result = json.loads(result_text)

        # Validate structure
        if "topic" not in result or "confidence" not in result:
            return {"topic": "Unknown Topic", "confidence": 0}

        # Clean up topic
        topic = result["topic"].strip().replace('"', '').replace("'", "")
        confidence = int(result.get("confidence", 50))

        # Validate confidence range
        confidence = max(0, min(100, confidence))

        return {
            "topic": topic,
            "confidence": confidence
        }

    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ Error parsing JSON response: {e}")
        print(f"Raw response: {result_text}")
        return {"topic": "Unknown Topic", "confidence": 0}


def batch_extract_topics(captions):
    """
    Extract topics from multiple captions with confidence scores.

    Args:
        captions (list): List of caption strings

    Returns:
        list: List of dicts with {"caption": str, "topic": str, "confidence": int}
    """
    results = []

    for i, caption in enumerate(captions):
        if not caption or len(caption.strip()) < 10:
            results.append({
                "caption": caption,
                "topic": "Invalid Caption",
                "confidence": 0
            })
            continue

        try:
            extraction = extract_topic_with_confidence(caption)
            results.append({
                "caption": caption,
                "topic": extraction["topic"],
                "confidence": extraction["confidence"]
            })

            # Progress indicator
            if (i + 1) % 5 == 0:
                print(f"  ✓ Processed {i + 1}/{len(captions)} captions")

        except Exception as e:
            print(f"  ⚠️ Error processing caption {i + 1}: {e}")
            results.append({
                "caption": caption,
                "topic": "Error",
                "confidence": 0
            })

    return results
