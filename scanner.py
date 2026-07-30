import os
from google import genai

def analyze_video(title, description):
    # Check both potential environment variable naming conventions
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        return "ERROR: No API key found. Please ensure either GEMINI_API_KEY or GOOGLE_API_KEY is set in Render Environment settings."
    
    try:
        # Initialize client with explicit key
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=f"Analyze this YouTube video title and description for SEO optimization. Provide top keywords, a strong title, and improvements:\nTitle: {title}\nDescription: {description}"
        )
        return response.text
    except Exception as e:
        return f"API Exception Encountered: {str(e)}"