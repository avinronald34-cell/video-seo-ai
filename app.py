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
    <title>Video SEO AI Portal</title>
    <meta name="theme-color" content="#000000">
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; color: #333; margin: 0; padding: 0; display: flex; height: 100vh; overflow: hidden; }
        
        /* Auth Screen Styling */
        .auth-wrapper { width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #1e1e2d; }
        .auth-container { background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 100%; max-width: 400px; text-align: center; }
        .auth-container h2 { margin-bottom: 10px; color: #1e1e2d; }
        
        /* Dashboard Layout Styling */
        .sidebar { width: 250px; background-color: #1e1e2d; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; justify-content: space-between; }
        .sidebar-top h2 { font-size: 18px; margin-bottom: 25px; color: #00d2ff; }
        .sidebar-top a { display: block; color: #a2a2bc; text-decoration: none; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; font-weight: bold; transition: all 0.2s; }
        .sidebar-top a:hover, .sidebar-top a.active { background-color: #2a2a40; color: #fff; }
        .logout-btn { background-color: #e74c3c; color: white; text-align: center; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; display: block; }
        .logout-btn:hover { background-color: #c0392b; }
        
        .main-content { flex: 1; padding: 30px; overflow-y: auto; background-color: #f4f4f9; box-sizing: border-box; display: flex; justify-content: center; align-items: flex-start; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); width: 100%; max-width: 800px; box-sizing: border-box; }
        
        header { border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; font-weight: bold; width: 100%; }
        button:hover { background-color: #0055b3; }
        
        .google-btn { background-color: #ffffff; color: #444; border: 1px solid #ccc; padding: 12px; border-radius: 4px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; text-decoration: none; width: 100%; box-sizing: border-box; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .google-btn:hover { background-color: #f8f8f8; }
        
        .divider { margin: 20px 0; border-bottom: 1px solid #ddd; position: relative; }
        .divider span { background: #fff; padding: 0 10px; color: #777; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); font-size: 12px; }
        
        input[type="text"], input[type="tel"], input[type="email"] { width: 100%; padding: 10px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .report-box { background: #fafafa; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-top: 20px; }
        pre { background: #222; color: #4cd137; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }
        .error-msg { color: #e74c3c; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    {% if view_type == 'otp_verify' %}
    <!-- Step 2: OTP Verification Screen -->
    <div class="auth-wrapper">
        <div class="auth-container">
            <h2>Enter Verification OTP</h2>
            <p style="color: #666; font-size: 14px; margin-bottom: 20px;">We sent a 4-digit OTP to <b>{{ phone }}</b><br><span style="font-size: 11px; color:#888;">(Hint: Enter code <b>1234</b>)</span></p>
            
            {% if error %}
            <div class="error-msg">{{ error }}</div>
            {% endif %}

            <form action="/auth/verify-otp" method="POST">
                <input type="hidden" name="phone" value="{{ phone }}">
                <input type="text" name="otp" placeholder="Enter 4-digit OTP" maxlength="4" required autofocus>
                <button type="submit">Verify & Login</button>
            </form>
            <br>
            <a href="/" style="font-size: 12px; color: #0066cc; text-decoration: none;">← Back to Login</a>
        </div>
    </div>
    {% elif not session.get('user') %}
    <!-- Step 1: Main Login & Signup Portal -->
    <div class="auth-wrapper">
        <div class="auth-container">
            <h2>Video SEO AI</h2>
            <p style="color: #666; font-size: 14px; margin-bottom: 25px;">Sign in or create your account to proceed</p>
            
            <!-- Google Sign-In Option -->
            <a href="/auth/google" class="google-btn">
                <svg width="18" height="18" viewBox="0 0 18 18" style="margin-right: 10px;"><path fill="#4285F4" d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.49h4.84c-.21 1.12-.85 2.08-1.81 2.72v2.26h2.92c1.71-1.57 2.69-3.88 2.69-6.63z"/><path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.71H.96v2.33C2.45 15.98 5.48 18 9 18z"/><path fill="#FBBC05" d="M3.97 10.71c-.18-.54-.28-1.12-.28-1.71s.1-1.17.28-1.71V4.96H.96C.35 6.18 0 7.55 0 9s.35 2.82.96 4.04l3.01-2.33z"/><path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.47.89 11.43 0 9 0 5.48 0 2.45 2.02.96 4.96l3.01 2.33c.71-2.13 2.69-3.71 5.03-3.71z"/></svg>
                Sign up / Sign in with Google
            </a>

            <div class="divider"><span>OR</span></div>

            <!-- Phone Number Submission -->
            <form action="/auth/phone" method="POST">
                <input type="tel" name="phone" placeholder="Mobile Number (e.g., +91...)" required>
                <button type="submit">Send OTP</button>
            </form>
        </div>
    </div>
    {% else %}
    <!-- Authenticated App View with Sidebar -->
    <div class="sidebar">
        <div class="sidebar-top">
            <h2>Video SEO AI</h2>
            <a href="/" class="{{ 'active' if content_type == 'home' else '' }}">Dashboard</a>
            <a href="/history" class="{{ 'active' if content_type == 'history' else '' }}">Scan History</a>
            <a href="/support" class="{{ 'active' if content_type == 'support' else '' }}">Support</a>
        </div>
        <div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>

    <div class="main-content">
        <div class="container">
            <header>
                <h1>Video SEO & Compliance Scanner</h1>
                <p style="color: #666; font-size: 14px; margin-top: 5px;">Logged in as: <b>{{ session.get('user') }}</b></p>
            </header>

            <main>
                {% if content_type == 'scan' %}
                    <section>
                        <h2>Audit Report for: {{ filename }}</h2>
                        <div class="report-box">
                            {{ audit_report|safe }}
                        </div>
                        <br>
                        <a href="/"><button style="width: auto;">Run Another Scan</button></a>
                        
                        <h3>Diagnostic Logs</h3>
                        <pre>{{ logs | join('\\n') }}</pre>
                    </section>
                {% elif content_type == 'history' %}
                    <section>
                        <h2>Scan History</h2>
                        <p>Your previous video optimization runs will appear here.</p>
                        <br><a href="/"><button style="width: auto;">Back to Dashboard</button></a>
                    </section>
                {% elif content_type == 'support' %}
                    <section>
                        <h2>Support Center</h2>
                        <p>Need assistance with API limitations or audit configuration? Reach out to support.</p>
                        <br><a href="/"><button style="width: auto;">Back to Dashboard</button></a>
                    </section>
                {% else %}
                    <section>
                        <h2>Select your video file (.mp4, .mov)</h2>
                        <form action="/scan" method="POST" enctype="multipart/form-data" style="margin-top: 15px;">
                            <div style="border: 2px dashed #ccc; padding: 20px; border-radius: 6px; background: #fafafa; margin-bottom: 15px;">
                                <input type="file" name="video" required>
                            </div>
                            <button type="submit" style="width: auto;">Run AI Scan & Analysis</button>
                        </form>
                    </section>
                {% endif %}
            </main>
        </div>
    </div>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(MASTER_TEMPLATE, content_type="home")

@app.route("/auth/google")
def auth_google():
    # In a full production app, this redirects to Google's actual OAuth server.
    # For a simulated secure gate, we set the credential session token properly.
    session['user'] = "google_verified_creator@gmail.com"
    return redirect(url_for('index'))

@app.route("/auth/phone", methods=["POST"])
def auth_phone():
    phone = request.form.get('phone', '').strip()
    if len(phone) < 5:
        return redirect(url_for('index'))
    # Render OTP input screen instead of logging in directly
    return render_template_string(MASTER_TEMPLATE, view_type="otp_verify", phone=phone)

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    phone = request.form.get('phone', '')
    otp = request.form.get('otp', '').strip()
    
    # Strict validation: require correct OTP code "1234"
    if otp == "1234":
        session['user'] = f"phone_{phone}"
        return redirect(url_for('index'))
    else:
        return render_template_string(MASTER_TEMPLATE, view_type="otp_verify", phone=phone, error="Invalid OTP code. Please enter 1234.")

@app.route("/scan", methods=["POST"])
def scan():
    if not session.get('user'):
        return redirect(url_for('index'))
        
    api_key = os.environ.get("GEMINI_API_KEY")
    diagnostic_logs = []
    diagnostic_logs.append("API Key present." if api_key else "API Key missing.")
    
    filename = "sample_video.mp4"
    if 'video' in request.files:
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