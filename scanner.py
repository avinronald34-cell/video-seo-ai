import os
from google import genai

def analyze_video(title, description):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "CRITICAL: GEMINI_API_KEY is missing from Render Environment variables."
    
    try:
        # Explicitly passing the key to the client constructor
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"Analyze this YouTube video title and description for SEO optimization. Provide top keywords, a strong title, and improvements:\nTitle: {title}\nDescription: {description}"
        )
        return response.text
    except Exception as e:
        return f"API Error Details: {str(e)}"