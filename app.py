import os
from flask import Flask, render_template, request, redirect, url_for, session
from scanner import analyze_video

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key")

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Add your login logic here
        return redirect(url_for('index'))
    return render_template('login.txt')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Add your signup logic here
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        video_title = request.form.get('title')
        video_desc = request.form.get('description')
        result = analyze_video(video_title, video_desc)
    return render_template('index.html', result=result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)