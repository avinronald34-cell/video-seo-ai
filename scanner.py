import os
import requests

def analyze_video(title, description):
    # Retrieve the API key from environment variables on Render
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY environment variable is missing on Render."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Analyze this YouTube video title and description for SEO optimization. Provide top keywords, a strong title, and improvements:\nTitle: {title}\nDescription: {description}"
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()
        
        if response.status_code == 200:
            # Extract text safely from the standard Gemini REST JSON response schema
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            error_message = data.get("error", {}).get("message", "Unknown API error")
            return f"Gemini API Error ({response.status_code}): {error_message}"
            
    except Exception as e:
        return f"Network or request failed: {str(e)}"