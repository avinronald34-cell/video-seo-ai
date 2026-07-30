import os
from flask import Flask, render_template, request, session, redirect, url_for
from scanner import analyze_video

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_key_999")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form.get('email', 'user')
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        session['user'] = request.form.get('email', 'user')
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/auth/google')
def auth_google():
    session['user'] = 'google_user'
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        video_title = request.form.get('title', '')
        video_desc = request.form.get('description', '')
        # Calls our instant fallback/scanner engine
        result = analyze_video(video_title, video_desc)
    return render_template('index.html', result=result)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)