import os
import traceback
from flask import Flask, request, redirect, url_for, send_from_directory, make_response
from google import genai

app = Flask(__name__)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI - Debug Mode</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }
        .app-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        .app-title h1 { margin: 0; font-size: 22px; color: #111; }
        button.primary-btn { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; width: 100%; font-size: 16px; }
        button.primary-btn:hover { background-color: #0055b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="app-header">
            <div class="app-title">
                <h1>Video SEO AI</h1>
                <p>System Diagnostics Active</p>
            </div>
        </div>
        <main>
            <section>
                <h2>Upload Video for SEO Scan</h2>
                <form action="/scan" method="POST" enctype="multipart/form-data">
                    <input type="file" name="video" required style="margin-bottom: 15px; display: block;">
                    <button type="submit" class="primary-btn">Run Diagnostic & Scan</button>
                </form>
            </section>
        </main>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    return make_response(HTML_PAGE, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/scan', methods=['POST'])
def scan():
    file = request.files.get('video')
    filename = file.filename if file and file.filename else "uploaded_video.mp4"
    
    diagnostic_logs = []
    ai_description = ""
    
    try:
        # 1. Check both possible environment variables used across SDK versions
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "CRITICAL CONFIG ERROR: Neither GEMINI_API_KEY nor GOOGLE_API_KEY is set in Render Environment variables!", 500
        
        diagnostic_logs.append("API Key detected successfully.")

        # 2. Initialize Client with explicit parameters
        client = genai.Client(api_key=api_key)
        diagnostic_logs.append("GenAI Client initialized.")

        # 3. Model Fallback Sequence targeting valid production models
        prompt_text = f"Generate a catchy YouTube video title, a short SEO description, and 4 comma-separated tags for an uploaded video file named: {filename}"
        
        models_to_try = ['gemini-3.5-flash', 'gemini-1.5-flash']
        response_ai = None
        last_exception = None

        for m_name in models_to_try:
            try:
                diagnostic_logs.append(f"Attempting model connection: {m_name}")
                response_ai = client.models.generate_content(
                    model=m_name,
                    contents=prompt_text
                )
                if response_ai and hasattr(response_ai, 'text') and response_ai.text:
                    diagnostic_logs.append(f"Success with model: {m_name}")
                    break
            except Exception as model_err:
                last_exception = str(model_err)
                diagnostic_logs.append(f"Model {m_name} failed: {model_err}")
                continue

        if response_ai and hasattr(response_ai, 'text') and response_ai.text:
            ai_description = response_ai.text
        else:
            ai_description = f"All models failed. Last error: {last_exception}"

    except Exception as e:
        traceback.print_exc()
        ai_description = f"Fatal Exception: {str(e)}"

    logs_str = "<br>".join(diagnostic_logs)
    
    result_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Diagnostic Results</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; color: #333; display: flex; justify-content: center; }}
            .container {{ background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 650px; width: 100%; }}
            .box {{ background: #f9f9fb; padding: 15px; border-radius: 6px; border: 1px solid #eaeaea; margin-top: 10px; white-space: pre-wrap; font-size: 14px; }}
            .logs {{ background: #1e1e1e; color: #00ff66; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; margin-top: 10px; }}
            a {{ color: #0066cc; text-decoration: none; display: inline-block; margin-top: 20px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Scan & Diagnostic Report</h2>
            <hr>
            <h3>Generated AI Metadata:</h3>
            <div class="box">{ai_description}</div>
            
            <h3>Execution Trace Logs:</h3>
            <div class="logs">{logs_str}</div>
            
            <a href="/">← Back to Upload</a>
        </div>
    </body>
    </html>
    """
    return make_response(result_html, 200, {'Content-Type': 'text/html; charset=utf-8'})

if __name__ == '__main__':
    app.run(debug=True)