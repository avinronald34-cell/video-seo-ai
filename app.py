import os
import markdown
from flask import Flask, request, render_template_string, session, redirect, url_for
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_video_seo_key")

def get_gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None

MASTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI Dashboard</title>
    <meta name="theme-color" content="#000000">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
        .sidebar { width: 250px; background-color: #1e1e2d; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; justify-content: space-between; }
        .sidebar-top h2 { font-size: 18px; margin-bottom: 25px; color: #00d2ff; }
        .sidebar-top a { display: block; color: #a2a2bc; text-decoration: none; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; font-weight: bold; transition: all 0.2s; }
        .sidebar-top a:hover, .sidebar-top a.active { background-color: #2a2a40; color: #fff; }
        .logout-btn { background-color: #e74c3c; color: white; text-align: center; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; display: block; }
        .logout-btn:hover { background-color: #c0392b; }
        
        .main-content { flex: 1; padding: 30px; overflow-y: auto; background-color: #f4f4f9; box-sizing: border-box; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); max-width: 800px; margin: auto; }
        header { border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #0055b3; }
        .report-box { background: #fafafa; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-top: 20px; }
        pre { background: #222; color: #4cd137; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }
        .google-btn { background-color: #ffffff; color: #444; border: 1px solid #ddd; padding: 12px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; display: inline-flex; align-items: center; text-decoration: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .google-btn:hover { background-color: #f8f8f8; }
    </style>
</head>
<body>
    <div class="sidebar">
        <div class="sidebar-top">
            <h2>Video SEO AI</h2>
            <a href="/" class="{{ 'active' if content_type == 'home' else '' }}">Dashboard</a>
            <a href="/history" class="{{ 'active' if content_type == 'history' else '' }}">Scan History</a>
            <a href="/support" class="{{ 'active' if content_type == 'support' else '' }}">Support</a>
        </div>
        {% if session.get('user') %}
        <div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
        {% endif %}
    </div>

    <div class="main-content">
        <div class="container">
            <header>
                <h1>Video SEO & Compliance Scanner</h1>
                {% if session.get('user') %}
                    <p style="color: #666; font-size: 14px; margin-top: 5px;">Logged in as: <b>{{ session.get('user') }}</b></p>
                {% endif %}
            </header>

            <main>
                {% if not session.get('user') %}
                    <section style="text-align: center; padding: 40px 0;">
                        <h2>Authentication Required</h2>
                        <p style="color: #666; margin-bottom: 25px;">Please sign in with your Google account to access the video optimization dashboard.</p>
                        <a href="/login" class="google-btn">
                            <svg width="18" height="18" viewBox="0 0 18 18" style="margin-right: 10px;"><path fill="#4285F4" d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.49h4.84c-.21 1.12-.85 2.08-1.81 2.72v2.26h2.92c1.71-1.57 2.69-3.88 2.69-6.63z"/><path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.71H.96v2.33C2.45 15.98 5.48 18 9 18z"/><path fill="#FBBC05" d="M3.97 10.71c-.18-.54-.28-1.12-.28-1.71s.1-1.17.28-1.71V4.96H.96C.35 6.18 0 7.55 0 9s.35 2.82.96 4.04l3.01-2.33z"/><path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.47.89 11.43 0 9 0 5.48 0 2.45 2.02.96 4.96l3.01 2.33c.71-2.13 2.69-3.71 5.03-3.71z"/></svg>
                            Sign in with Google
                        </a>
                    </section>
                {% elif content_type == 'scan' %}
                    <section>
                        <h2>Audit Report for: {{ filename }}</h2>
                        <div class="report-box">
                            {{ audit_report|safe }}
                        </div>
                        <br>
                        <a href="/"><button>Run Another Scan</button></a>
                        
                        <h3>Diagnostic Logs</h3>
                        <pre>{{ logs | join('\\n') }}</pre>
                    </section>
                {% elif content_type == 'history' %}
                    <section>
                        <h2>Scan History</h2>
                        <p>Your previous video optimization logs will appear here.</p>
                        <br><a href="/"><button>Back to Dashboard</button></a>
                    </section>
                {% elif content_type == 'support' %}
                    <section>
                        <h2>Support Center</h2>
                        <p>For assistance with API limits or audit configuration, reach out to support.</p>
                        <br><a href="/"><button>Back to Dashboard</button></a>
                    </section>
                {% else %}
                    <section>
                        <h2>Select your video file (.mp4, .mov)</h2>
                        <form action="/scan" method="POST" enctype="multipart/form-data" style="margin-top: 15px;">
                            <div style="border: 2px dashed #ccc; padding: 20px; border-radius: 6px; background: #fafafa; margin-bottom: 15px;">
                                <input type="file" name="video" required>
                            </div>
                            <button type="submit">Run AI Scan & Analysis</button>
                        </form>
                    </section>
                {% endif %}
            </main>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    if not session.get('user'):
        return render_template_string(MASTER_TEMPLATE, content_type="home")
    return render_template_string(MASTER_TEMPLATE, content_type="home")

@app.route("/dashboard")
def dashboard():
    return redirect(url_for('index'))

@app.route("/login")
def login():
    # Simulate a successful Google OAuth callback login session
    session['user'] = "creator@videoseo.ai"
    return redirect(url_for('index'))

@app.route("/scan", methods=["POST", "GET"])
def scan():
    if not session.get('user'):
        return redirect(url_for('index'))
        
    api_key = os.environ.get("GEMINI_API_KEY")
    diagnostic_logs = []
    diagnostic_logs.append("API Key present." if api_key else "API Key missing.")
    
    filename = "sample_video.mp4"
    if request.method == "POST" and 'video' in request.files:
        uploaded_file = request.files['video']
        if uploaded_file.filename != '':
            filename = uploaded_file.filename
            diagnostic_logs.append(f"Received file: {filename}")

    if not api_key:
        error_html = "<p style='color:red;'>Configuration Error: GEMINI_API_KEY environment variable is missing on Render.</p>"
        return render_template_string(MASTER_TEMPLATE, content_type="scan", audit_report=error_html, logs=diagnostic_logs, filename=filename)

    client = get_gemini_client()
    if not client:
        diagnostic_logs.append("Failed to initialize GenAI Client.")
        return render_template_string(MASTER_TEMPLATE, content_type="scan", audit_report="Error: Could not initialize Gemini client.", logs=diagnostic_logs, filename=filename)
    
    diagnostic_logs.append("GenAI Client created successfully.")

    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash-lite"]
    raw_response_text = None

    prompt = (
        f"Perform a comprehensive YouTube SEO and compliance audit for a video file named '{filename}'. "
        "Provide your analysis structured strictly using Markdown headers and bullet points covering: "
        "1. Score (out of 100 with explanation) "
        "2. Copyrights Details (Audio and Visual asset risks) "
        "3. Observation & Actionable Optimization Recommendations."
    )

    for model_name in models_to_try:
        diagnostic_logs.append(f"Attempting model: {model_name}")
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            if response and response.text:
                raw_response_text = response.text
                diagnostic_logs.append(f"Success with model: {model_name}")
                break
        except Exception as e:
            diagnostic_logs.append(f"Model {model_name} error: {str(e)}")

    if raw_response_text:
        audit_report_html = markdown.markdown(raw_response_text)
    else:
        audit_report_html = "<p style='color:red;'>Error: Model request failed. Please check diagnostic logs above.</p>"

    return render_template_string(MASTER_TEMPLATE, content_type="scan", audit_report=audit_report_html, logs=diagnostic_logs, filename=filename)

@app.route("/history")
def history():
    if not session.get('user'):
        return redirect(url_for('index'))
    return render_template_string(MASTER_TEMPLATE, content_type="history")

@app.route("/support")
def support():
    if not session.get('user'):
        return redirect(url_for('index'))
    return render_template_string(MASTER_TEMPLATE, content_type="support")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)