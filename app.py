import os
from flask import Flask, redirect, url_for, session, request, render_template, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google import genai

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super-secret-key-change-this")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

@app.route('/')
def index():
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/auth/google')
def google_login():
    base_url = request.host_url.rstrip('/')
    redirect_uri = f"{base_url}/auth/google/callback"
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile"
    )
    return redirect(google_auth_url)

@app.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    if not code:
        return "Authentication failed: No code provided.", 400

    base_url = request.host_url.rstrip('/')
    redirect_uri = f"{base_url}/auth/google/callback"

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    import requests
    token_response = requests.post(token_url, data=data)
    token_json = token_response.json()

    if 'id_token' not in token_json:
        return f"Authentication failed: {token_json}", 400

    try:
        idinfo = id_token.verify_oauth2_token(
            token_json['id_token'], 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        session['user'] = {
            'name': idinfo.get('name'),
            'email': idinfo.get('email'),
            'picture': idinfo.get('picture')
        }
    except ValueError as e:
        return f"Invalid Token: {str(e)}", 400

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Example Gemini Video SEO Audit endpoint (if your app uses it)
@app.route('/analyze', methods=['POST'])
def analyze_video():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Add your video audit / Gemini logic here if needed
    return jsonify({'message': 'Analysis placeholder working!'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=True)