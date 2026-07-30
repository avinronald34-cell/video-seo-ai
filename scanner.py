import os
import requests

def analyze_video(title, description):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Config Error: GEMINI_API_KEY is not set in Render environment settings."
    
    # Using the standard v1 endpoint which is stable across all cloud hosts
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": f"Provide an SEO optimized title, top 5 tags, and description improvements for a YouTube video with this title: '{title}' and description: '{description}'."
            }]
        }]
    }
    
    try:
        # 15-second explicit timeout safeguard for cloud servers
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"API Error [{response.status_code}]: {response.text}"
            
    except requests.exceptions.Timeout:
        return "Error: The request to Gemini timed out on Render's network. Please try again."
    except Exception as e:
        return f"Connection Exception: {str(e)}"