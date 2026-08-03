import os
import markdown
from flask import Flask, request, render_template_string, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_video_seo_key")

# Initialize Authlib OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get('GOOGLE_CLIENT_ID'),
    client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

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
        .auth-wrapper { width: 100vw; height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #1e1e2d; }
        .auth-container { background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.2); width: 100%; max-width: 400px; text-align: center; }
        .auth-container h2 { margin-bottom: 10px; color: #1e1e2d; }
        .sidebar { width: 250px; background-color: #1e1e2d; color: #fff; display: flex; flex-direction: column; padding: 20px; box-sizing: border-box; justify-content: space-between; }
        .sidebar-top h2 { font-size: 18px; margin-bottom: 25px; color: #00d2ff; }
        .sidebar-top a { display: block; color: #a2a2bc; text-decoration: none; padding: 10px 15px; border-radius: 6px; margin-bottom: 8px; font-weight: bold; }
        .sidebar-top a:hover, .sidebar-top a.active { background-color: #2a2a40; color: #fff; }
        .logout-btn { background-color: #e74c3c; color: white; text-align: center; padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold; display: block; }
        .main-content { flex: 1; padding: 30px; overflow-y: auto; background-color: #f4f4f9; box-sizing: border-box; display: flex; justify-content: center; align-items: flex-start; }
        .container { background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); width: 100%; max-width: 800px; box-sizing: border-box; }
        header { border-bottom: 2px solid #eaeaea; padding-bottom: 15px; margin-bottom: 20px; }
        button { background-color: #0066cc; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; font-weight: bold; width: 100%; }
        button:hover { background-color: #0055b3; }
        .google-btn { background-color: #ffffff; color: #444; border: 1px solid #ccc; padding: 12px; border-radius: 4px; cursor: pointer; font-weight: bold; display: flex; align-items: center; justify-content: center; text-decoration: none; width: 100%; box-sizing: border-box; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .google-btn:hover { background-color: #f8f8f8; }
        .divider { margin: 20px 0; border-bottom: 1px solid #ddd; position: relative; }
        .divider span { background: #fff; padding: 0 10px; color: #777; position: absolute; top: -10px; left: 50%; transform: translateX(-50%); font-size: 12px; }
        input[type="tel"], input[type="text"] { width: 100%; padding: 10px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .report-box { background: #fafafa; padding: 15px; border: 1px solid #ddd; border-radius: 6px; margin-top: 20px; }
        pre { background: #222; color: #4cd137; padding: 10px; border-radius: 5px; overflow-x: auto; font-size: 12px; }
        .error-msg { color: #e74c3c; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    {% if view_type == 'otp_verify' %}
    <div class="auth-wrapper">
        <div class="auth-container">
            <h2>Verify Mobile OTP</h2>
            <p style="color: #666; font-size: 14px; margin-bottom: 15px;">Enter the code sent to: <b>{{ phone }}</b></p>
            {% if error %}<div class="error-msg">{{ error }}</div>{% endif %}
            <form action="/auth/verify-otp" method="POST">
                <input type="hidden" name="phone" value="{{ phone }}">
                <input type="text" name="otp" placeholder="Enter 4-digit OTP (e.g. 1234)" maxlength="4" required autofocus>
                <button type="submit">Verify & Login</button>
            </form>
        </div>
    </div>
    {% elif not session.get('user') %}
    <div class="auth-wrapper">
        <div class="auth-container">
            <h2>Video SEO AI</h2>
            <p style="color: #666; font-size: 14px; margin-bottom: 25px;">Sign in to your account</p>
            
            <a href="/auth/google" class="google-btn">
                <svg width="18" height="18" viewBox="0 0 18 18" style="margin-right: 10px;"><path fill="#4285F4" d="M17.64 9.2c0-.63-.06-1.25-.16-1.84H9v3.49h4.84c-.21 1.12-.85 2.08-1.81 2.72v2.26h2.92c1.71-1.57 2.69-3.88 2.69-6.63z"/><path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.81.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.71H.96v2.33C2.45 15.98 5.48 18 9 18z"/><path fill="#FBBC05" d="M3.97 10.71c-.18-.54-.28-1.12-.28-1.71s.1-1.17.28-1.71V4.96H.96C.35 6.18 0 7.55 0 9s.35 2.82.96 4.04l3.01-2.33z"/><path fill="#EA4335" d="M9 3.58c1.32 0 2.5.45 3.44 1.35l2.58-2.58C13.47.89 11.43 0 9 0 5.48 0 2.45 2.02.96 4.96l3.01 2.33c.71-2.13 2.69-3.71 5.03-3.71z"/></svg>
                Sign in with Google
            </a>

            <div class="divider"><span>OR</span></div>

            <form action="/auth/phone" method="POST">
                <input type="tel" name="phone" placeholder="Mobile Number (e.g. +91...)" required>
                <button type="submit">Send OTP</button>
            </form>
        </div>
    </div>
    {% else %}
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
                        <div class="report-box">{{ audit_report|safe }}</div>
                        <br><a href="/"><button style="width: auto;">Run Another Scan</button></a>
                        <h3>Diagnostic Logs</h3>
                        <pre>{{ logs | join('\n') }}</pre>
                    </section>
                {% elif content_type == 'history' %}
                    <section><h2>Scan History</h2><p>Your previous optimization logs will appear here.</p><br><a href="/"><button style="width: auto;">Back to Dashboard</button></a></section>
                {% elif content_type == 'support' %}
                    <section><h2>Support Center</h2><p>Reach out to support for configuration questions.</p><br><a href="/"><button style="width: auto;">Back to Dashboard</button></a></section>
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

@app.route('/auth/google')
def auth_google():
    redirect_uri = url_for('auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google_callback():
    token = google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        session['user'] = user_info['email']
    else:
        session['user'] = "google_user@gmail.com"
    return redirect(url_for('index'))

@app.route("/auth/phone", methods=["POST"])
def auth_phone():
    phone = request.form.get('phone', '').strip()
    if len(phone) < 5:
        return redirect(url_for('index'))
    return render_template_string(MASTER_TEMPLATE, view_type="otp_verify", phone=phone)

@app.route("/auth/verify-otp", methods=["POST"])
def verify_otp():
    phone = request.form.get('phone', '')
    otp = request.form.get('otp', '').strip()
    if otp == "1234":
        session['user'] = f"phone_{phone}"
        return redirect(url_for('index'))
    return render_template_string(MASTER_TEMPLATE, view_type="otp_verify", phone=phone, error="Invalid OTP. Enter 1234 to test.")

@app.route("/scan", methods=["POST"])
def scan():
    if not session.get('user'):
        return redirect(url_for('index'))
    api_key = os.environ.get("GEMINI_API_KEY")
    diagnostic_logs = ["API Key present." if api_key else "API Key missing."]
    filename = "sample_video.mp4"
    if 'video' in request.files:
        uploaded_file = request.files['video']
        if uploaded_file.filename != '':
            filename = uploaded_file.filename
            diagnostic_logs.append(f"Received file: {filename}")

    if not api_key:
        error_html = "<p style='color:red;'>Configuration Error: GEMINI_API_KEY missing.</p>"
        return render_template_string(MASTER_TEMPLATE, content_type="scan", audit_report=error_html, logs=diagnostic_logs, filename=filename)

    client = get_gemini_client()
    client_res = client.models.generate_content(model="gemini-2.0-flash", contents=f"Audit YouTube video file named {filename}")
    audit_report_html = markdown.markdown(client_res.text) if client_res and client_res.text else "Error generating report"
    return render_template_string(MASTER_TEMPLATE, content_type="scan", audit_report=audit_report_html, logs=diagnostic_logs, filename=filename)

@app.route("/history")
def history():
    if not session.get('user'): return redirect(url_for('index'))
    return render_template_string(MASTER_TEMPLATE, content_type="history")

@app.route("/support")
def support():
    if not session.get('user'): return redirect(url_for('index'))
    return render_template_string(MASTER_TEMPLATE, content_type="support")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)