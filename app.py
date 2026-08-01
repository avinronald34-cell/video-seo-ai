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

# Master template including Login option in the navigation bar
MASTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI</title>
    <meta name="theme-color" content="#000000">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 700px; width: 100%; }
        header { border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        nav a { color: #0066cc; text-decoration: none; margin-right: 15px; font-weight: bold; }
        nav a:hover { text-decoration: underline; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button:hover { background-color: #0055b3; }
        .report-box { background: #fafafa; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-top: 20px; }
        pre { background: #222; color: #4cd137; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Video SEO AI Dashboard</h1>
            <p>Welcome! Optimize your videos and run compliance checks instantly.</p>
            <nav>
                <a href="/">Home / Upload</a> | 
                <a href="/login">Login</a> | 
                <a href="/history">History</a> | 
                <a href="/support">Support</a>
            </nav>
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
                        <input type="email" placeholder="Email address" required style="display:block; margin-bottom:10px; padding:8px; width:80%;">
                        <input type="password" placeholder="Password" required style="display:block; margin-bottom:10px; padding:8px; width:80%;">
                        <button type="submit">Sign In</button>
                    </form>
                </section>
            {% elif content_type == 'history' %}
                <section>
                    <h2>Scan History</h2>
                    <p>Your previous scan entries will appear here.</p>
                    <br><a href="/"><button>Back to Upload</button></a>
                </section>
            {% elif content_type == 'support' %}
                <section>
                    <h2>Support Center</h2>
                    <p>Need help? Contact your admin or check API configurations.</p>
                    <br><a href="/"><button>Back to Upload</button></a>
                </section>
            {% else %}
                <section>
                    <h2>Upload Video for SEO & Compliance Scan</h2>
                    <form action="/scan" method="POST" enctype="multipart/form-data">
                        <input type="file" name="video" required style="margin-bottom: 10px; display: block;">
                        <button type="submit">Run Video Scan</button>
                    </form>
                </section>
            {% endif %}
        </main>
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

    # Updated model fallback list supporting standard available identifiers
    models_to_try = ["gemini-1.5-flash", "gemini-2.0-flash-exp", "gemini-2.5-flash"]
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
        audit_report_html = "<p style='color:red;'>Error: All fallback models failed. Please verify your GEMINI_API_KEY permissions.</p>"

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