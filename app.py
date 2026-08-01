import os
import markdown
from flask import Flask, render_template, request, redirect, url_for, render_template_string
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

# Fallback template if any HTML file is missing
FALLBACK_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }
        header { border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        nav a { color: #0066cc; text-decoration: none; margin-right: 10px; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Video SEO AI</h1>
            <p>Welcome, Guest</p>
            <nav>
                <a href="/scan">Upload Scan</a> | 
                <a href="/history">Scan History</a> | 
                <a href="/support">Support</a> | 
                <a href="/logout">Logout</a>
            </nav>
        </header>
        <main>
            <section>
                <h2>Upload Video for SEO & Compliance Scan</h2>
                <form action="/scan" method="POST" enctype="multipart/form-data">
                    <input type="file" name="video" required>
                    <button type="submit">Run Video Scan</button>
                </form>
            </section>
        </main>
    </div>
</body>
</html>
"""

def safe_render(template_name):
    try:
        return render_template(template_name)
    except Exception:
        return render_template_string(FALLBACK_HTML)

@app.route("/")
def index():
    return safe_render("landing.html")

@app.route("/landing")
def landing():
    return safe_render("landing.html")

@app.route("/dashboard")
def dashboard():
    return safe_render("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return safe_render("landing.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return safe_render("landing.html")

@app.route("/scan", methods=["POST", "GET"])
def scan():
    api_key = os.environ.get("GEMINI_API_KEY")
    diagnostic_logs = ["API Key present." if api_key else "API Key missing."]
    
    if not api_key:
        error_html = "Configuration Error: GEMINI_API_KEY environment variable is missing."
        try:
            return render_template("scan.html", audit_report=error_html, logs=diagnostic_logs, filename="sample_video.mp4")
        except Exception:
            return render_template_string(FALLBACK_HTML)

    client = get_gemini_client()
    if not client:
        diagnostic_logs.append("Failed to initialize GenAI Client.")
        try:
            return render_template("scan.html", audit_report="Error: Could not initialize Gemini client.", logs=diagnostic_logs, filename="sample_video.mp4")
        except Exception:
            return render_template_string(FALLBACK_HTML)
    
    diagnostic_logs.append("GenAI Client created successfully.")

    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]
    raw_response_text = None

    prompt = (
        "Perform a comprehensive YouTube SEO and compliance audit for a sample video file named 'sample_video.mp4'. "
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

    audit_report_html = markdown.markdown(raw_response_text) if raw_response_text else "<p>Error: Model did not return a valid text response.</p>"

    try:
        return render_template("scan.html", audit_report=audit_report_html, logs=diagnostic_logs, filename="sample_video.mp4")
    except Exception:
        return render_template_string(f"<html><body><h1>Audit Complete</h1>{audit_report_html}<br><a href='/'>Back</a></body></html>")

@app.route("/history")
def history():
    try:
        return render_template("history.html")
    except Exception:
        return render_template_string("<html><body><h1>Scan History</h1><p>No history yet.</p><a href='/'>Back</a></body></html>")

@app.route("/support")
def support():
    try:
        return render_template("support.html")
    except Exception:
        return render_template_string("<html><body><h1>Support</h1><p>Contact support here.</p><a href='/'>Back</a></body></html>")

@app.route("/logout")
def logout():
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)