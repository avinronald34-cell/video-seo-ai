import os
import traceback
import markdown
from flask import Flask, render_template_string, render_template, request, redirect, url_for
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_video_seo_key")

@app.route("/")
def index():
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
def dashboard():
    try:
        return render_template("dashboard.html")
    except Exception as e:
        return f"Dashboard Template Error: {str(e)}"

@app.route("/scan", methods=["POST", "GET"])
def scan():
    diagnostic_logs = []
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        diagnostic_logs.append("API Key present." if api_key else "API Key missing.")
        
        if not api_key:
            report_text = "Configuration Error: GEMINI_API_KEY environment variable is missing on Render."
            return render_template("scan.html", audit_report=report_text, logs=diagnostic_logs, filename="sample_video.mp4")

        client = genai.Client(api_key=api_key)
        diagnostic_logs.append("GenAI Client created successfully.")

        # Use the most stable baseline model identifier
        models_to_try = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        raw_response_text = None

        prompt = (
            "Perform a short, high-impact YouTube SEO and compliance audit for 'sample_video.mp4'. "
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

        return render_template("scan.html", audit_report=audit_report_html, logs=diagnostic_logs, filename="sample_video.mp4")

    except Exception as e:
        error_trace = traceback.format_exc()
        diagnostic_logs.append(f"CRITICAL EXCEPTION: {str(e)}")
        
        # Fallback inline display so it never crashes to a blank 500 screen
        fallback_html = f"""
        <html>
        <head><title>Video SEO AI - Recovery View</title></head>
        <body style="font-family: Arial; padding: 30px; background: #111; color: #fff;">
            <h2>Runtime Exception Caught</h2>
            <p style="color: #ff6b6b;"><b>Error Message:</b> {str(e)}</p>
            <h3>Diagnostic Logs:</h3>
            <pre style="background: #222; padding: 15px; border-radius: 5px; color: #4cd137;">{"\\n".join(diagnostic_logs)}</pre>
            <h3>Traceback:</h3>
            <pre style="background: #222; padding: 15px; border-radius: 5px; color: #e84118;">{error_trace}</pre>
        </body>
        </html>
        """
        return render_template_string(fallback_html)

@app.route("/history")
def history():
    try:
        return render_template("history.html")
    except Exception as e:
        return f"History Template Error: {str(e)}"

@app.route("/support")
def support():
    try:
        return render_template("support.html")
    except Exception as e:
        return f"Support Template Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)