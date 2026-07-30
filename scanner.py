import os
from google import genai

def analyze_video(title, description):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY is missing from Render Environment Variables."
    
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        Analyze the following YouTube video title and description for SEO optimization. 
        Provide high-ranking keyword suggestions, an optimized title, and actionable SEO improvements.
        
        Video Title: {title}
        Video Description: {description}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Scan error: {str(e)}. Please check your API key configuration in Render."