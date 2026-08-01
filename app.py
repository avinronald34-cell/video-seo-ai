import os
import traceback
from flask import Flask, request, redirect, url_for, send_from_directory, make_response, session, render_template_string
from google import genai

# CRITICAL: Initialize Flask app FIRST before any route decorators
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "video-seo-ai-secure-secret-key-2026")

# Configure session cookie settings for reliable cross-device mobile/desktop access
app.config['SESSION_COOKIE_SECURE'] = True  # Required for HTTPS on Render
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# In-memory user database simulation (email -> password)
USERS_DB = {
    "admin@videoseo.ai": "securepassword123"
}

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
        button { background-color: #0066cc; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 5px; }
        button:hover { background-color: #0055b3; }
        .error { color: #dc3545; font-size: 13px; margin-bottom: 10px; }
        .link-text { margin-top: 15px; font-size: 13px; display: block; color: #666; }
        .link-text a { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Video SEO AI Login</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form action="/login-action" method="POST">
            <input type="email" name="email" placeholder="Email Address" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Sign In</button>
        </form>
        <span class="link-text">New user? <a href="/signup">Create an Account</a></span>
    </div>
</body>
</html>"""

SIGNUP_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Up - Video SEO AI</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 40px; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 400px; width: 100%; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background-color: #28a745; color: white; border: none; padding: 10px; width: 100%; border-radius: 4px; cursor: pointer; font-size: 16px; margin-top: 5px; }
        button:hover { background-color: #218838; }
        .error { color: #dc3545; font-size: 13px; margin-bottom: 10px; }
        .link-text { margin-top: 15px; font-size: 13px; display: block; color: #666; }
        .link-text a { color: #0066cc; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Create New Account</h2>
        {% if error %}
            <div class="error">{{ error }}</div>
        {% endif %}
        <form action="/signup-action" method="POST">
            <input type="email" name="email" placeholder="Email Address" required>
            <input type="password" name="password" placeholder="Create Password" required>
            <button type="submit">Register Account</button>
        </form>
        <span class="link-text">Already have an account? <a href="/">Sign In</a></span>
    </div>
</body>
</html>"""

DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI - Dashboard</title>
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
                <p>Welcome, {{ user_email }}</p>
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
                    <button type="submit" class="primary-btn">Run Video Scan & Diagnostics</button>
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
    return render_template_string(LOGIN_PAGE, error=None)

@app.route('/signup')
def signup():
    if session.get('logged_in'):
        return redirect(url_for('dashboard'))
    return render_template_string(SIGNUP_PAGE, error=None)

@app.route('/signup-action', methods=['POST'])
def signup_action():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        return render_template_string(SIGNUP_PAGE, error="All fields are required.")
    
    if email in USERS_DB:
        return render_template_string(SIGNUP_PAGE, error="Email already registered. Please sign in.")
    
    USERS_DB[email] = password
    session['logged_in'] = True
    session['user_email'] = email
    return redirect(url_for('dashboard'))

@app.route('/login-action', methods=['POST'])
def login_action():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if email in USERS_DB and USERS_DB[email] == password:
        session['logged_in'] = True
        session['user_email'] = email
        return redirect(url_for('dashboard'))
    else:
        return render_template_string(LOGIN_PAGE, error="Invalid email or password.")

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template_string(DASHBOARD_PAGE, user_email=session.get('user_email', 'User'))

@app.route('/history')
def history():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return make_response("<!DOCTYPE html><html><body><h2>Scan History</h2><p>No past scans recorded yet.</p><a href='/dashboard'>← Back to Dashboard</a></body></html>", 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
        
    # If someone tries to open /scan directly via GET instead of form submission, redirect them safely back
    if request.method == 'GET':
        return redirect(url_for('dashboard'))
        
    file = request.files.get('video')
    filename = file.filename if file and file.filename else "uploaded_video.mp4"
    
    diagnostic_logs = []
    ai_description = ""
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "Configuration Error: GEMINI_API_KEY environment variable is missing on Render.", 500
        
        diagnostic_logs.append("API Key present.")
        
        client = genai.Client(api_key=api_key)
        diagnostic_logs.append("GenAI Client created successfully.")
        
        prompt_text = (
            f"Analyze the video file named '{filename}' for a comprehensive YouTube SEO and compliance check. "
            f"Provide the output strictly using the following headings and structure:\n\n"
            f"1. **Score**: (Give an overall SEO score out of 100)\n"
            f"2. **Copyrights Details**: (Analyze compliance, risk of copyright flags, or safe usage notes based on filename/topic)\n"
            f"3. **Observation**: (Detailed key observations about the video content theme)\n"
            f"4. **Suggestions**: (Actionable improvements to boost engagement and watch time)\n"
            f"5. **Optimized Title**: (A catchy, high-CTR YouTube title)\n"
            f"6. **Optimized Description**: (A well-structured YouTube description with timestamps placeholder)\n"
            f"7. **Tags**: (10-15 relevant comma-separated SEO tags)"
        )
        
        response_ai = None
        for m_name in ['gemini-3.6-flash', 'gemini-3.5-flash']:
            try:
                diagnostic_logs.append(f"Attempting model: {m_name}")
                response_ai = client.models.generate_content(
                    model=m_name,
                    contents=prompt_text
                )
                if response_ai and response_ai.text:
                    diagnostic_logs.append(f"Success with model: {m_name}")
                    break
            except Exception as model_err:
                diagnostic_logs.append(f"Model {m_name} error: {str(model_err)}")
                continue
                
        if response_ai and hasattr(response_ai, 'text') and response_ai.text:
            ai_description = response_ai.text
        else:
            ai_description = "Error: Model did not return a valid text response."
            
    except Exception as e:
        traceback.print_exc()
        ai_description = f"Runtime Exception: {str(e)}"

    logs_str = "<br>".join(diagnostic_logs)
    
    result_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Scan Results & Diagnostics</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; color: #333; display: flex; justify-content: center; }}
            .container {{ background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 700px; width: 100%; }}
            .box {{ background: #f9f9fb; padding: 20px; border-radius: 6px; border: 1px solid #eaeaea; margin-top: 10px; white-space: pre-wrap; font-size: 14px; line-height: 1.5; }}
            .logs {{ background: #1e1e1e; color: #00ff66; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; margin-top: 10px; }}
            a {{ color: #0066cc; text-decoration: none; display: inline-block; margin-top: 20px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Scan Report: {filename}</h2>
            <hr>
            <h3>Generated AI SEO & Compliance Report:</h3>
            <div class="box">{ai_description}</div>
            
            <h3>Execution & Diagnostic Logs:</h3>
            <div class="logs">{logs_str}</div>
            
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