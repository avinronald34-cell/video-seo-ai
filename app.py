import os
from flask import Flask, render_template, request, redirect, url_for
from scanner import analyze_video

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/auth/google', methods=['GET', 'POST'])
def auth_google():
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        video_title = request.form.get('title')
        video_desc = request.form.get('description')
        if video_title or video_desc:
            result = analyze_video(video_title, video_desc)
        else:
            result = "Please enter a video title or description to run the scan."
    return render_template('index.html', result=result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)