import os
from google import genai

# Securely fetch API key from environment variables
API_KEY = os.environ.get("GEMINI_API_KEY")

def analyze_video(title, description):
    if not API_KEY:
        return "Error: GEMINI_API_KEY environment variable is not set."
    
    client = genai.Client(api_key=API_KEY)
    
    prompt = f"""
    Analyze the following YouTube video details for SEO optimization:
    Title: {title}
    Description: {description}
    
    Provide suggestions for tags, improved title ideas, and SEO optimization tips.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"An error occurred during analysis: {str(e)}"