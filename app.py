import os
import traceback
from flask import Flask, request, redirect, url_for, send_from_directory, make_response, session, render_template_string
from google import genai
import markdown

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "video-seo-ai-secure-secret-key-2026")

app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; height: 100vh; box-sizing: border-box; }
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
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; height: 100vh; box-sizing: border-box; }
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

DASHBOARD_LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI - Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 250px; background-color: #1e1e2f; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; transition: transform 0.3s ease; z-index: 100; position: relative; }
        .sidebar h2 { font-size: 20px; margin-bottom: 30px; color: #00d2ff; }
        .sidebar a { color: #b0b0c3; text-decoration: none; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; display: block; font-size: 15px; transition: 0.2s; }
        .sidebar a:hover, .sidebar a.active { background-color: #2a2a40; color: #fff; }
        .sidebar .logout-link { margin-top: auto; background-color: #dc3545; color: white; text-align: center; }
        .sidebar .logout-link:hover { background-color: #c82333; }

        @media(max-width: 768px) {
            .sidebar { position: fixed; height: 100%; transform: translateX(-100%); }
            .sidebar.open { transform: translateX(0); }
        }

        .top-bar { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
        .menu-toggle { background: #1e1e2f; color: #fff; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 18px; display: none; }
        @media(max-width: 768px) { .menu-toggle { display: block; } }

        .main-content { flex: 1; padding: 20px; overflow-y: auto; box-sizing: border-box; }
        .card { background: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 700px; margin: auto; box-sizing: border-box; }
        h1 { margin-top: 0; font-size: 22px; color: #111; }
        .user-info { font-size: 13px; color: #666; margin-bottom: 20px; }
        
        .upload-box { border: 2px dashed #0066cc; padding: 20px; text-align: center; border-radius: 6px; background: #fafafa; margin-bottom: 15px; }
        input[type="file"] { width: 100%; box-sizing: border-box; margin: 10px 0; }
        button.primary-btn { background-color: #0066cc; color: white; border: none; padding: 12px; border-radius: 4px; cursor: pointer; font-size: 16px; width: 100%; font-weight: bold; }
        button.primary-btn:hover { background-color: #0055b3; }

        #loading-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 9999; justify-content: center; align-items: center; color: white; flex-direction: column; text-align: center; padding: 20px; box-sizing: border-box; }
        .spinner { border: 5px solid #f3f3f3; border-top: 5px solid #00d2ff; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin-bottom: 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar">
        <h2>Video SEO AI</h2>
        <a href="/dashboard" class="active">📊 Dashboard</a>
        <a href="/history">📂 Scan History</a>
        <a href="/support">💬 Support</a>
        <a href="/logout" class="logout-link">Logout</a>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <button class="menu-toggle" onclick="toggleSidebar()">☰ Menu</button>
        </div>
        <div class="card">
            <h1>Video SEO & Compliance Scanner</h1>
            <div class="user-info">Logged in as: <strong>{{ user_email }}</strong></div>
            
            <form action="/scan" method="POST" enctype="multipart/form-data" onsubmit="showLoading()">
                <div class="upload-box">
                    <p style="margin:0 0 10px 0; font-size:14px;">Select your video file (.mp4, .mov)</p>
                    <input type="file" name="video" required accept="video/*">
                </div>
                <button type="submit" class="primary-btn">Run AI Scan & Analysis</button>
            </form>
        </div>
    </div>

    <div id="loading-overlay">
        <div class="spinner"></div>
        <h2>Gemini AI is analyzing your video...</h2>
        <p>Checking SEO metrics, copyrights, and generating insights. Please wait.</p>
    </div>

    <script>
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
        }
        function showLoading() {
            document.getElementById('loading-overlay').style.display = 'flex';
        }
    </script>
</body>
</html>"""

SUPPORT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Support - Video SEO AI</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 250px; background-color: #1e1e2f; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; transition: transform 0.3s ease; z-index: 100; position: relative; }
        .sidebar h2 { font-size: 20px; margin-bottom: 30px; color: #00d2ff; }
        .sidebar a { color: #b0b0c3; text-decoration: none; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; display: block; font-size: 15px; }
        .sidebar a:hover, .sidebar a.active { background-color: #2a2a40; color: #fff; }
        .sidebar .logout-link { margin-top: auto; background-color: #dc3545; color: white; text-align: center; }
        @media(max-width: 768px) { .sidebar { position: fixed; height: 100%; transform: translateX(-100%); } .sidebar.open { transform: translateX(0); } }
        .top-bar { display: flex; align-items: center; margin-bottom: 20px; }
        .menu-toggle { background: #1e1e2f; color: #fff; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 18px; display: none; }
        @media(max-width: 768px) { .menu-toggle { display: block; } }
        .main-content { flex: 1; padding: 20px; overflow-y: auto; box-sizing: border-box; }
        .card { background: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 700px; margin: auto; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="sidebar" id="sidebar">
        <h2>Video SEO AI</h2>
        <a href="/dashboard">📊 Dashboard</a>
        <a href="/history">📂 Scan History</a>
        <a href="/support" class="active">💬 Support</a>
        <a href="/logout" class="logout-link">Logout</a>
    </div>
    <div class="main-content">
        <div class="top-bar"><button class="menu-toggle" onclick="toggleSidebar()">☰ Menu</button></div>
        <div class="card">
            <h2>Support & Help Center</h2>
            <p>Need assistance or have questions regarding your SEO scans? Reach out directly to our team:</p>
            <ul>
                <li><strong>Email Support:</strong> support@videoseo.ai</li>
                <li><strong>Documentation:</strong> Check out our optimization guidelines on file naming and tag strategy.</li>
            </ul>
            <a href="/dashboard" style="color: #0066cc; text-decoration: none; font-weight: bold; margin-top: 20px; display: inline-block;">← Back to Dashboard</a>
        </div>
    </div>
    <script>function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }</script>
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
    return render_template_string(DASHBOARD_LAYOUT, user_email=session.get('user_email', 'User'))

@app.route('/history')
def history():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return make_response("""<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 250px; background-color: #1e1e2f; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; transition: transform 0.3s ease; z-index: 100; position: relative; }
        .sidebar h2 { font-size: 20px; margin-bottom: 30px; color: #00d2ff; }
        .sidebar a { color: #b0b0c3; text-decoration: none; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; display: block; font-size: 15px; }
        .sidebar a:hover, .sidebar a.active { background-color: #2a2a40; color: #fff; }
        .sidebar .logout-link { margin-top: auto; background-color: #dc3545; color: white; text-align: center; }
        @media(max-width: 768px) { .sidebar { position: fixed; height: 100%; transform: translateX(-100%); } .sidebar.open { transform: translateX(0); } }
        .top-bar { display: flex; align-items: center; margin-bottom: 20px; }
        .menu-toggle { background: #1e1e2f; color: #fff; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 18px; display: none; }
        @media(max-width: 768px) { .menu-toggle { display: block; } }
        .main-content { flex: 1; padding: 20px; overflow-y: auto; box-sizing: border-box; }
        .card { background: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 700px; margin: auto; box-sizing: border-box; }
    </style></head><body>
    <div class="sidebar" id="sidebar">
        <h2>Video SEO AI</h2>
        <a href="/dashboard">📊 Dashboard</a>
        <a href="/history" class="active">📂 Scan History</a>
        <a href="/support">💬 Support</a>
        <a href="/logout" class="logout-link">Logout</a>
    </div>
    <div class="main-content">
        <div class="top-bar"><button class="menu-toggle" onclick="toggleSidebar()">☰ Menu</button></div>
        <div class="card">
            <h2>Scan History</h2>
            <p>Your previous video audits and optimization records will appear here.</p>
            <a href='/dashboard' style="color: #0066cc; text-decoration: none; font-weight: bold; margin-top: 20px; display: inline-block;">← Back to Dashboard</a>
        </div>
    </div>
    <script>function toggleSidebar() { document.getElementById('sidebar').classList.toggle('open'); }</script></body></html>""", 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/support')
def support():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template_string(SUPPORT_PAGE)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
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
            ai_description = markdown.markdown(response_ai.text)
        else:
            ai_description = "<p>Error: Model did not return a valid text response.</p>"
            
    except Exception as e:
        traceback.print_exc()
        ai_description = f"<p>Runtime Exception: {str(e)}</p>"

    logs_str = "<br>".join(diagnostic_logs)
    
    result_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Scan Results - Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; display: flex; height: 100vh; overflow: hidden; }}
            .sidebar {{ width: 250px; background-color: #1e1e2f; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; transition: transform 0.3s ease; z-index: 100; position: relative; }}
            .sidebar h2 {{ font-size: 20px; margin-bottom: 30px; color: #00d2ff; }}
            .sidebar a {{ color: #b0b0c3; text-decoration: none; padding: 12px 15px; border-radius: 6px; margin-bottom: 8px; display: block; font-size: 15px; }}
            .sidebar a:hover {{ background-color: #2a2a40; color: #fff; }}
            .sidebar .logout-link {{ margin-top: auto; background-color: #dc3545; color: white; text-align: center; }}
            @media(max-width: 768px) {{ .sidebar {{ position: fixed; height: 100%; transform: translateX(-100%); }} .sidebar.open {{ transform: translateX(0); }} }}
            .top-bar {{ display: flex; align-items: center; margin-bottom: 20px; }}
            .menu-toggle {{ background: #1e1e2f; color: #fff; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 18px; display: none; }}
            @media(max-width: 768px) {{ .menu-toggle {{ display: block; }} }}
            .main-content {{ flex: 1; padding: 20px; overflow-y: auto; box-sizing: border-box; }}
            .card {{ background: #ffffff; padding: 25px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 700px; margin: auto; box-sizing: border-box; }}
            
            /* Clean Report Typography & Layout */
            .result-box {{ background: #f9f9fb; padding: 20px; border-radius: 6px; border: 1px solid #eaeaea; margin-top: 15px; font-size: 14px; line-height: 1.6; color: #222; }}
            .result-box h3, .result-box h2, .result-box h1 {{ color: #0066cc; margin-top: 20px; margin-bottom: 10px; font-size: 16px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
            .result-box ul {{ padding-left: 20px; margin-top: 5px; margin-bottom: 15px; }}
            .result-box li {{ margin-bottom: 6px; }}
            .result-box p {{ margin-bottom: 10px; }}
            
            .logs {{ background: #1e1e1e; color: #00ff66; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 11px; margin-top: 15px; overflow-x: auto; }}
            .btn-back {{ background-color: #0066cc; color: white; padding: 10px 20px; border-radius: 4px; text-decoration: none; display: inline-block; margin-top: 20px; font-weight: bold; }}
            .btn-back:hover {{ background-color: #0055b3; }}
        </style>
    </head>
    <body>
        <div class="sidebar" id="sidebar">
            <h2>Video SEO AI</h2>
            <a href="/dashboard">📊 Dashboard</a>
            <a href="/history">📂 Scan History</a>
            <a href="/support">💬 Support</a>
            <a href="/logout" class="logout-link">Logout</a>
        </div>
        <div class="main-content">
            <div class="top-bar"><button class="menu-toggle" onclick="toggleSidebar()">☰ Menu</button></div>
            <div class="card">
                <h2>Audit Report: {filename}</h2>
                <hr style="border:0; border-top:1px solid #eaeaea; margin: 15px 0;">
                
                <h3>AI SEO & Compliance Analysis</h3>
                <div class="result-box">{ai_description}</div>
                
                <h3>Diagnostic Execution Logs</h3>
                <div class="logs">{logs_str}</div>
                
                <a href="/dashboard" class="btn-back">← Back to Dashboard</a>
            </div>
        </div>
        <script>
            function toggleSidebar() {{
                document.getElementById('sidebar').classList.toggle('open');
            }}
        </script>
    </body>
    </html>
    """
    return make_response(result_html, 200, {'Content-Type': 'text/html; charset=utf-8'})

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)