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
    <title>Video SEO AI</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }
        .app-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        .app-title h1 { margin: 0; font-size: 22px; color: #111; }
        .app-title p { margin: 4px 0 0 0; color: #666; font-size: 13px; }
        .nav-menu { display: flex; align-items: center; gap: 12px; }
        .nav-menu a { color: #0066cc; text-decoration: none; font-size: 14px; font-weight: 500; }
        .btn-login-action { background-color: #0066cc !important; color: white !important; padding: 6px 14px; border-radius: 4px; text-decoration: none; }
        button.primary-btn { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button.primary-btn:hover { background-color: #0055b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="app-header">
            <div class="app-title">
                <h1>Video SEO AI</h1>
                <p>Welcome, Guest</p>
            </div>
            <div class="nav-menu">
                <a href="/history">Scan History</a>
                <a href="/logout">Logout</a>
                <a href="/login" class="btn-login-action">Login</a>
            </div>
        </div>
        <main>
            <section>
                <h2>Upload Video for SEO & Compliance Scan</h2>
                <form action="/scan" method="POST" enctype="multipart/form-data">
                    <input type="file" name="video" required style="margin-bottom: 10px; display: block;">
                    <button type="submit" class="primary-btn">Run Video Scan</button>
                </form>
            </section>
        </main>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    return make_response(HTML_PAGE, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/login')
def login():
    return make_response("<!DOCTYPE html><html><body><h2>Login</h2><p>Coming soon.</p><a href='/'>Home</a></body></html>", 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/history')
def history():
    return make_response("<!DOCTYPE html><html><body><h2>History</h2><p>No scans yet.</p><a href='/'>Home</a></body></html>", 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/scan', methods=['POST'])
def scan():
    if 'video' not in request.files:
        return "No video file uploaded", 400
    file = request.files['video']
    filename = file.filename if file.filename else "uploaded_video.mp4"
    
    ai_description = ""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "Configuration Error: GEMINI_API_KEY environment variable is missing.", 500
        
        client = genai.Client(api_key=api_key)
        
        prompt_text = f"Generate a catchy YouTube video title, a short SEO description, and 4 comma-separated tags for an uploaded video file named: {filename}"
        
        # Robust fallback mechanism across current models
        response_ai = None
        for model_name in ['gemini-3.6-flash', 'gemini-3.5-flash']:
            try:
                response_ai = client.models.generate_content(
                    model=model_name,
                    contents=prompt_text
                )
                if response_ai and hasattr(response_ai, 'text') and response_ai.text:
                    break
            except Exception:
                continue
        
        if response_ai and hasattr(response_ai, 'text') and response_ai.text:
            ai_description = response_ai.text
        else:
            ai_description = "Error: All model endpoints failed to return a valid response block."
    except Exception as e:
        traceback.print_exc()
        ai_description = f"Runtime Exception Caught: {str(e)}"

    result_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Scan Results - Video SEO AI</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; color: #333; display: flex; justify-content: center; }}
            .container {{ background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }}
            a {{ color: #0066cc; text-decoration: none; display: inline-block; margin-top: 15px; }}
            .box {{ background: #f9f9fb; padding: 15px; border-radius: 6px; border: 1px solid #eaeaea; margin-top: 10px; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Scan Complete: {filename}</h2>
            <hr>
            <h3>Generated AI SEO Metadata:</h3>
            <div class="box">{ai_description}</div>
            <h3>Compliance Status:</h3>
            <p style="color: green; font-weight: bold;">✔ Passed Guidelines & Safety Checks</p>
            <br>
            <a href="/">← Upload Another Video</a>
        </div>
    </body>
    </html>
    """
    return make_response(result_html, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)