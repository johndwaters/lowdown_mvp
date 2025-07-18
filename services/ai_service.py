# services/ai_service.py
import os
import openai
from dotenv import load_dotenv
from typing import Dict
import re

load_dotenv()

def get_ai_summary(title: str, content: str, url: str) -> Dict[str, str]:
    """
    Generates a newsletter-style summary and title for an article.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {
            "title": "AI Service Disabled",
            "summary_body": "🎯 **AI Service Disabled**\n\nOpenAI API key not configured. Please set the OPENAI_API_KEY environment variable. ([more](#))",
        }

    client = openai.OpenAI(api_key=api_key)
    truncated_content = content[:15000]

    prompt = f"""
    You are writing for *The Lowdown*, a defense and aviation-focused newsletter. Your task is to analyze the following article and produce two distinct components: a new headline and a fully formatted newsletter summary.

    **Article Title:** {title}
    **Article URL:** {url}
    **Full Content:**
    ---
    {truncated_content}
    ---

    ### 📝 Output Format:
    Your final output must be structured *exactly* as follows, with each section on a new line and nothing else.

    **HEADLINE:** [A concise, engaging headline. It should be creative and distinct from the original article title, with a touch of dry, witty humor. This should be plain text without any markdown or emojis.]
    **SUMMARY_BODY:** [A fully formatted, single markdown block. It must start *exactly* with a 🎯 emoji, followed by the headline in bold. The body should be a compact paragraph (3-5 sentences) summarizing the article with natural hyperlinks. It must end with `(more)` hyperlinked to the original article URL: {url}]

    ### ✅ Tone and Style Guidelines (for SUMMARY_BODY):
    - **Direct, factual, and context-rich.**
    - Provide **critical operational context** (e.g., delays, strategic impact).
    - Include **specific stats** and program names.
    - For technical topics, link to a **Wikipedia or authoritative reference**.
    - **DO NOT use em-dashes** (—).

    ### Example SUMMARY_BODY:
    🎯 **A-10s Head to the Boneyard Early**

    The U.S. Air Force is looking to send its entire A-10 Warthog fleet to retirement sooner than planned and is also axing the E-7 Wedgetail program, citing cost and delays. This is part of a major fleet shakeup in the 2026 budget proposal that also shuffles F-16s and F-15s, while boosting funds for the B-21 Raider and Sentinel ICBM. The whole plan depends on a budget bill passing, otherwise the Space Force might have to tighten its belt. ([more]({url}))
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a specialized assistant for a defense and aviation newsletter, outputting structured data."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7, # Increased for more creativity
            max_tokens=400,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        raw_output = response.choices[0].message.content.strip()

        # Parse the structured output
        headline_match = re.search(r"HEADLINE:\s*(.*)", raw_output)
        summary_body_match = re.search(r"SUMMARY_BODY:\s*([\s\S]*)", raw_output)

        headline = headline_match.group(1).strip() if headline_match else "No headline found"
        summary_body = summary_body_match.group(1).strip() if summary_body_match else "Could not generate summary body."

        # Clean up any extra markdown that the AI might add before the emoji
        summary_body = re.sub(r'^\s*\**\s*🎯', '🎯', summary_body)

        return {
            "title": headline,
            "summary_body": summary_body,
        }
    except Exception as e:
        return {
            "title": "Error",
            "summary_body": f"🎯 **Error**\n\nError generating summary: {e} ([more](#))",
        }
