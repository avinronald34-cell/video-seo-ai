import os
from google import genai

def analyze_video(title, description):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is not configured in Render. Please add it under Environment settings."
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Analyze this YouTube video title and description for SEO optimization. Provide top keywords, a strong title, and improvements:\nTitle: {title}\nDescription: {description}"
        )
        return response.text
    except Exception as e:
        return f"Scan failed: {str(e)}"