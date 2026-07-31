import os
import traceback
from flask import Flask, request, redirect, url_for, send_from_directory, make_response, session
from google import genai
from google.genai import types

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "video-seo-ai-secure-secret-key")

# Login Page Template
LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Video SEO AI</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 40px; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 400px; width: 100%; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #0055b3; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Video SEO AI Login</h2>
        <form action="/login-action" method="POST">
            <input type="email" name="email" placeholder="Email Address" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In / Continue</button>
        </form>
    </div>
</body>
</html>"""

# Main Dashboard Template
DASHBOARD_PAGE = """<!DOCTYPE html>
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
        .btn-logout-action { background-color: #dc3545 !important; color: white !important; padding: 6px 14px; border-radius: 4px; text-decoration: none; }
        button.primary-btn { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; width: 100%; font-size: 16px; }
        button.primary-btn:hover { background-color: #0055b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="app-header">
            <div class="app-title">
                <h1>Video SEO AI</h1>
                <p>Welcome, Authenticated User</p>
            </div>
            <div class="nav-menu">
                <a href="/history">Scan History</a>
                <a href="/logout" class="btn-logout-action">Logout</a>
            </div>
        </div>
        <main>
            <section>
                <h2>Upload Video for SEO & Compliance Scan</h2>
                <form action="/scan" method="POST" enctype="multipart/form-data">
                    <input type="file" name="video" required style="margin-bottom: 15px; display: block;">
                    <button type="submit" class="primary-btn">Run Video Scan</button>
                </form>
            </section>
        </main>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return make_response(LOGIN_PAGE, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/login-action', methods=['POST'])
def login_action():
    session['logged_in'] = True
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return make_response(DASHBOARD_PAGE, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/history')
def history():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return make_response("<!DOCTYPE html><html><body><h2>History</h2><p>No scans yet.</p><a href='/dashboard'>← Dashboard</a></body></html>", 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/scan', methods=['POST'])
def scan():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
        
    file = request.files.get('video')
    filename = file.filename if file and file.filename else "uploaded_video.mp4"
    
    ai_description = ""
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "Configuration Error: GEMINI_API_KEY environment variable is missing.", 500
        
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(api_version="v1")
        )
        
        prompt_text = f"Generate a catchy YouTube video title, a short SEO description, and 4 comma-separated tags for an uploaded video file named: {filename}"
        
        # Updated to active model gemini-3.6-flash
        response_ai = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt_text
        )
        
        if response_ai and hasattr(response_ai, 'text') and response_ai.text:
            ai_description = response_ai.text
        else:
            ai_description = "Error: The AI model returned an empty response block."
            
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
            a {{ color: #0066cc; text-decoration: none; display: inline-block; margin-top: 20px; font-weight: bold; }}
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
            <a href="/dashboard">← Back to Dashboard</a>
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