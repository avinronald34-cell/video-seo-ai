import os
import traceback
import markdown
from flask import Flask, render_template_string, render_template, request, redirect, url_for
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_video_seo_key")

@app.route("/")
def index():
    return render_template("landing.html")

@app.route("/dashboard")
def dashboard():
    return render_template("landing.html")

@app.route("/landing")
def landing():
    return render_template("landing.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    return render_template("index.html")

@app.route("/logout")
def logout():
    return redirect(url_for("landing"))

@app.route("/history")
def history():
    return render_template("index.html", audit_report="<p>No past history available yet. Run a scan to see records here.</p>", logs=[], filename="None")

@app.route("/scan", methods=["POST", "GET"])
def scan():
    diagnostic_logs = []
    filename = "sample_video.mp4"
    
    try:
        # Check if user uploaded a file through index.html form
        if request.method == "POST" and 'video' in request.files:
            uploaded_file = request.files['video']
            if uploaded_file.filename != '':
                filename = uploaded_file.filename
                diagnostic_logs.append(f"Received uploaded file: {filename}")

        api_key = os.environ.get("GEMINI_API_KEY")
        diagnostic_logs.append("API Key present." if api_key else "API Key missing.")
        
        if not api_key:
            report_text = "Configuration Error: GEMINI_API_KEY environment variable is missing on Render."
            return render_template("index.html", audit_report=report_text, logs=diagnostic_logs, filename=filename)

        client = genai.Client(api_key=api_key)
        diagnostic_logs.append("GenAI Client created successfully.")

        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        raw_response_text = None

        prompt = (
            f"Perform a short, high-impact YouTube SEO and compliance audit for video file '{filename}'. "
            "Keep the output extremely crisp and scannable using Markdown formatting: "
            "1. **SEO Score** (X/100) "
            "2. **Key Fixes Needed** (Bullet points only) "
            "3. **Copyright & Safety** (Short status) "
            "4. **Quick Action Plan** (Top 3 steps)"
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
            except Exception as model_err:
                diagnostic_logs.append(f"Model {model_name} error: {str(model_err)}")

        if raw_response_text:
            audit_report_html = markdown.markdown(raw_response_text)
        else:
            audit_report_html = "<p>Error: All models failed to generate content. Check logs below.</p>"

        # Check if index.html has a section to render the audit report, otherwise fallback gracefully
        try:
            return render_template("index.html", audit_report=audit_report_html, logs=diagnostic_logs, filename=filename)
        except Exception:
            # Fallback if index.html doesn't accept audit_report variable yet
            return render_template_string(f"""
            <html>
            <head><title>Scan Results - Video SEO AI</title></head>
            <body style="font-family: Arial; padding: 30px; background: #f4f4f9; color: #333;">
                <h1>Scan Results for: {filename}</h1>
                <div style="background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    {audit_report_html}
                </div>
                <br><a href="/login">Back to App</a>
            </body>
            </html>
            """)

    except Exception as e:
        error_trace = traceback.format_exc()
        diagnostic_logs.append(f"CRITICAL EXCEPTION: {str(e)}")
        return render_template_string(f"""
        <html>
        <head><title>Recovery View</title></head>
        <body style="font-family: Arial; padding: 30px; background: #111; color: #fff;">
            <h2>Runtime Exception Caught</h2>
            <p style="color: #ff6b6b;"><b>Error:</b> {str(e)}</p>
            <pre style="background: #222; padding: 15px; color: #4cd137;">{"\\n".join(diagnostic_logs)}</pre>
            <pre style="color: #888;">{error_trace}</pre>
        </body>
        </html>
        """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)