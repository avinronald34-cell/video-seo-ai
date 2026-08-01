import os
import markdown
from flask import Flask, render_template, request, redirect, url_for
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

@app.route("/")
def index():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    # Pointing to landing.html since dashboard.html does not exist in templates
    return render_template("landing.html")

@app.route("/scan", methods=["POST", "GET"])
def scan():
    api_key = os.environ.get("GEMINI_API_KEY")
    
    diagnostic_logs = []
    diagnostic_logs.append("API Key present." if api_key else "API Key missing.")
    
    if not api_key:
        error_html = "Configuration Error: GEMINI_API_KEY environment variable is missing."
        return render_template("scan.html", audit_report=error_html, logs=diagnostic_logs, filename="sample_video.mp4")

    client = get_gemini_client()
    if not client:
        diagnostic_logs.append("Failed to initialize GenAI Client.")
        return render_template("scan.html", audit_report="Error: Could not initialize Gemini client.", logs=diagnostic_logs, filename="sample_video.mp4")
    
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
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                raw_response_text = response.text
                diagnostic_logs.append(f"Success with model: {model_name}")
                break
        except Exception as e:
            diagnostic_logs.append(f"Model {model_name} error: {str(e)}")

    if raw_response_text:
        audit_report_html = markdown.markdown(raw_response_text)
    else:
        audit_report_html = "<p>Error: Model did not return a valid text response.</p>"

    return render_template("scan.html", audit_report=audit_report_html, logs=diagnostic_logs, filename="sample_video.mp4")

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/support")
def support():
    return render_template("support.html")

@app.route("/logout")
def logout():
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)