from groq import Groq
from src.config import get_groq_key
import json


def generate_reel_ideas(captions_list):
    """
    Generate content ideas based on reel captions from finance creators.

    Task:
    1. Identify trending themes
    2. Generate specific reel ideas
    3. Keep ideas practical and viral-friendly

    Rules:
    - Generate 5-10 reel ideas
    - Each idea should be actionable
    - Keep short and catchy
    - Focus on beginner-friendly finance topics

    Args:
        captions_list (list): List of caption strings from finance reels

    Returns:
        list: List of dicts with {"reel_idea": str, "topic": str, "reason": str}

    Examples of Good Ideas:
    - "3 Tax Saving Hacks Before March"
    - "SIP vs FD for Beginners"
    - "Credit Card Mistakes to Avoid"

    Bad (too generic):
    - "Finance tips"
    - "Investment advice"
    """
    api_key = get_groq_key()
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set.")

    client = Groq(api_key=api_key)

    # Format captions for prompt
    captions_formatted = "\n".join([f"{i+1}. {cap[:200]}" for i, cap in enumerate(captions_list[:50])])

    prompt = f"""You are a JSON API. Return ONLY valid JSON, no explanations or markdown.

Based on these reel captions, generate 5-10 content ideas.

Captions:
{captions_formatted}

Return this exact JSON structure (NO markdown, NO code blocks, NO explanations):

[
    {{
        "reel_idea": "short catchy title",
        "topic": "specific topic name",
        "reason": "why it's trending"
    }}
]"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # Updated to current supported flagship model
        messages=[
            {"role": "system", "content": "You are a specialized content strategist. You must output results in valid JSON format."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000,
        response_format={"type": "json_object"}
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

        # Remove text before first [ or {
        if "[" in result_text:
            result_text = result_text[result_text.find("["):]
        elif "{" in result_text:
            result_text = result_text[result_text.find("{"):]

        # Remove text after last ] or }
        if "]" in result_text:
            result_text = result_text[:result_text.rfind("]")+1]
        elif "}" in result_text:
            result_text = result_text[:result_text.rfind("}")+1]

        # Basic JSON repair for truncated responses
        if result_text.count('[') > result_text.count(']'):
            # It's an array that wasn't closed
            result_text = result_text.strip()
            if not result_text.endswith('}'):
                # We're in the middle of an object
                result_text = result_text[:result_text.rfind('{')] # Remove the partial object
                result_text = result_text.strip().rstrip(',')
            result_text += ']'
        elif result_text.count('{') > result_text.count('}'):
            # It's an object that wasn't closed
            result_text += '}'

        try:
            ideas_raw = json.loads(result_text)
            # If it's an object with a key (common in JSON mode), get the array
            if isinstance(ideas_raw, dict):
                # Look for an array inside the dict
                for key in ideas_raw:
                    if isinstance(ideas_raw[key], list):
                        ideas = ideas_raw[key]
                        break
                else:
                    ideas = []
            else:
                ideas = ideas_raw
        except json.JSONDecodeError:
            # Try one more cleanup if it's still broken
            result_text = result_text.strip().rstrip(',')
            if not result_text.endswith(']'): result_text += ']'
            ideas = json.loads(result_text)

        # Validate structure
        if not isinstance(ideas, list):
            return []

        # Clean and validate each idea
        validated_ideas = []
        for idea in ideas:
            if all(key in idea for key in ["reel_idea", "topic", "reason"]):
                validated_ideas.append({
                    "reel_idea": idea["reel_idea"].strip(),
                    "topic": idea["topic"].strip(),
                    "reason": idea["reason"].strip()
                })

        return validated_ideas

    except (json.JSONDecodeError, ValueError) as e:
        print(f"⚠️ Error parsing JSON response: {e}")
        print(f"Raw response: {result_text[:500]}")
        return []


def generate_ideas_from_reels(reels):
    """
    Generate reel ideas from reel objects (with caption, likes, etc.).

    Args:
        reels (list): List of reel dicts with keys: caption, likes, comments, creator_name

    Returns:
        list: List of reel idea dicts
    """
    # Extract captions from reels
    captions = [reel.get("caption", "") for reel in reels if reel.get("caption")]

    if not captions:
        print("⚠️ No valid captions found in reels")
        return []

    print(f"🎬 Generating reel ideas from {len(captions)} captions...")
    ideas = generate_reel_ideas(captions)

    print(f"✨ Generated {len(ideas)} reel ideas")
    return ideas


def format_reel_idea_output(ideas):
    """
    Format reel ideas for display.

    Args:
        ideas (list): List of reel idea dicts

    Returns:
        str: Formatted output string
    """
    if not ideas:
        return "No ideas generated."

    output = "📝 REEL IDEAS:\n\n"

    for i, idea in enumerate(ideas, 1):
        output += f"{i}. {idea['reel_idea']}\n"
        output += f"   Topic: {idea['topic']}\n"
        output += f"   Why: {idea['reason']}\n\n"

    return output
