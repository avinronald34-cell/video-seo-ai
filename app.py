import os
import markdown
from flask import Flask, request, render_template, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from google import genai

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_video_seo_key")

# Required for Authlib behind proxy / cloud hosting environments
os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

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

@app.route("/")
def index():
    return render_template("index.html", content_type="home")

@app.route('/auth/google')
def auth_google():
    redirect_uri = url_for('auth_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if user_info:
            session['user'] = user_info['email']
        else:
            session['user'] = "google_user@gmail.com"
    except Exception as e:
        print(f"OAuth Callback Error: {e}")
        return f"Authentication failed: {str(e)}", 500
    return redirect(url_for('index'))

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
        return render_template("index.html", content_type="scan", audit_report=error_html, logs=diagnostic_logs, filename=filename)

    client = get_gemini_client()
    client_res = client.models.generate_content(model="gemini-2.0-flash", contents=f"Audit YouTube video file named {filename}")
    audit_report_html = markdown.markdown(client_res.text) if client_res and client_res.text else "Error generating report"
    return render_template("index.html", content_type="scan", audit_report=audit_report_html, logs=diagnostic_logs, filename=filename)

@app.route("/history")
def history():
    if not session.get('user'): return redirect(url_for('index'))
    return render_template("index.html", content_type="history")

@app.route("/support")
def support():
    if not session.get('user'): return redirect(url_for('index'))
    return render_template("index.html", content_type="support")

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)