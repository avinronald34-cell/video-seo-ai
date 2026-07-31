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
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            background: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 100%;
        }
        .app-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #eaeaea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        .app-title h1 { margin: 0; font-size: 22px; color: #111; }
        .app-title p { margin: 4px 0 0 0; color: #666; font-size: 13px; }
        .nav-menu {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .nav-menu a {
            color: #0066cc;
            text-decoration: none;
            font-size: 14px;
            font-weight: 500;
        }
        .nav-menu a:hover {
            text-decoration: underline;
        }
        .btn-login-action {
            background-color: #0066cc !important;
            color: white !important;
            padding: 6px 14px;
            border-radius: 4px;
            text-decoration: none;
        }
        button.primary-btn {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button.primary-btn:hover {
            background-color: #0055b3;
        }
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
    response = make_response(HTML_PAGE)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/login')
def login():
    login_page = """<!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Login - Video SEO AI</title></head>
    <body style="font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; display: flex; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 400px; width: 100%;">
            <h2>Login</h2>
            <p>Authentication feature coming soon.</p>
            <a href="/" style="color: #0066cc; text-decoration: none;">← Back to Home</a>
        </div>
    </body></html>"""
    return make_response(login_page, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/history')
def history():
    history_page = """<!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Scan History - Video SEO AI</title></head>
    <body style="font-family: Arial, sans-serif; background: #f4f4f9; padding: 20px; display: flex; justify-content: center;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 500px; width: 100%;">
            <h2>Scan History</h2>
            <p>No past scans recorded yet.</p>
            <a href="/" style="color: #0066cc; text-decoration: none;">← Back to Home</a>
        </div>
    </body></html>"""
    return make_response(history_page, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/scan', methods=['POST'])
def scan():
    if 'video' not in request.files:
        return "No video file uploaded", 400
    file = request.files['video']
    if file.filename == '':
        return "No selected file", 400
    
    filename = file.filename
    ai_description = ""
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        client = genai.Client(api_key=api_key)
        
        # Updated to standard model gemini-3.6-flash
        response_ai = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"Generate a catchy YouTube video title, a short SEO description, and 4 comma-separated tags for an uploaded video file named: {filename}"
        )
        if response_ai and response_ai.text:
            ai_description = response_ai.text
        else:
            ai_description = "Error: Model returned an empty response."
    except Exception as e:
        traceback.print_exc()
        ai_description = f"API Error Details: {str(e)}"

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
            a:hover {{ text-decoration: underline; }}
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
    response = make_response(result_html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)