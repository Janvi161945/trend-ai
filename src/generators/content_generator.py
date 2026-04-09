from groq import Groq
from src.config import GROQ_API_KEY

def generate_script(topic):
    """
    Generate a reel script for the selected topic using Groq.
    """
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
    
    client = Groq(api_key=GROQ_API_KEY)
    
    prompt = f"""You are a content creator assistant.
Generate a high-engagement Instagram Reel script for this finance topic: "{topic}".
The script should be 45-60 seconds long and follow this structure:

HOOK (3 sec): A compelling opening statement.
INTRO (5 sec): Brief introduction.
BODY (40 sec): Three main points or a quick explanation of the topic.
CTA (5 sec): Call to action (Follow for more tips).

Return the script in a clear, formatted style.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=500
    )

    script = response.choices[0].message.content.strip()
    return script
