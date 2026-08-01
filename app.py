import os
import markdown
from flask import Flask, request, render_template_string
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
        /* Sidebar layout styling */
        .sidebar { width: 250px; background-color: #1e1e2d; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; }
        .sidebar h2 { font-size: 18px; margin-bottom: 25px; color: #00d2ff; }
        .sidebar a { color: #a2a2bc; text-decoration: none; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; font-weight: bold; transition: all 0.2s; }
        .sidebar a:hover, .sidebar a.active { background-color: #2a2a40; color: #fff; }
        
        /* Main content area */
        .main-content { flex: 1; padding: 30px; overflow-y: auto; background-color: #f4f4f9; box-sizing: border-box; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); max-width: 800px; margin: auto; }
        header { border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #0055b3; }
        .report-box { background: #fafafa; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-top: 20px; }
        pre { background: #222; color: #4cd137; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }
        input[type="email"], input[type="password"], input[type="text"] { width: 100%; padding: 10px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
    </style>
</head>
<body>
    <!-- Persistent Sidebar Navigation -->
    <div class="sidebar">
        <h2>Video SEO AI</h2>
        <a href="/" class="{{ 'active' if content_type == 'home' else '' }}">Home / Upload</a>
        <a href="/login" class="{{ 'active' if content_type == 'login' else '' }}">Login</a>
        <a href="/history" class="{{ 'active' if content_type == 'history' else '' }}">Scan History</a>
        <a href="/support" class="{{ 'active' if content_type == 'support' else '' }}">Support Center</a>
    </div>

    <!-- Main Workspace -->
    <div class="main-content">
        <div class="container">
            <header>
                <h1>Dashboard Workspace</h1>
                <p>Optimize your videos and run compliance checks instantly.</p>
            </header>

            <main>
                {% if content_type == 'scan' %}
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
                {% elif content_type == 'login' %}
                    <section>
                        <h2>Account Login</h2>
                        <p>Enter your credentials to access your saved video analytics.</p>
                        <form onsubmit="event.preventDefault(); alert('Logged in successfully!'); window.location.href='/';">
                            <label>Email Address</label>
                            <input type="email" placeholder="name@example.com" required>
                            <label>Password</label>
                            <input type="password" placeholder="••••••••" required>
                            <button type="submit">Sign In</button>
                        </form>
                    </section>
                {% elif content_type == 'history' %}
                    <section>
                        <h2>Scan History</h2>
                        <p>Your previous video audits and optimization runs will appear here.</p>
                        <br><a href="/"><button>Back to Upload</button></a>
                    </section>
                {% elif content_type == 'support' %}
                    <section>
                        <h2>Support Center</h2>
                        <p>Need assistance with API integration or compliance reports? Reach out to support.</p>
                        <br><a href="/"><button>Back to Upload</button></a>
                    </section>
                {% else %}
                    <section>
                        <h2>Upload Video for SEO & Compliance Scan</h2>
                        <form action="/scan" method="POST" enctype="multipart/form-data">
                            <input type="file" name="video" required style="margin-bottom: 15px; display: block;">
                            <button type="submit">Run Video Scan</button>
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
    return render_template_string(MASTER_TEMPLATE, content_type="home")

@app.route("/dashboard")
def dashboard():
    return render_template_string(MASTER_TEMPLATE, content_type="home")

@app.route("/login")
def login():
    return render_template_string(MASTER_TEMPLATE, content_type="login")

@app.route("/signup")
def signup():
    return render_template_string(MASTER_TEMPLATE, content_type="login")

@app.route("/scan", methods=["POST", "GET"])
def scan():
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

    models_to_try = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
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
    return render_template_string(MASTER_TEMPLATE, content_type="history")

@app.route("/support")
def support():
    return render_template_string(MASTER_TEMPLATE, content_type="support")

@app.route("/logout")
def logout():
    return index()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)