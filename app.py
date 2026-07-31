import os
from flask import Flask, render_template, send_from_directory, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return "<h3>Scan History Page (Coming Soon)</h3><a href='/'>Back to Home</a>"

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/scan', methods=['POST'])
def scan():
    if 'video' not in request.files:
        return "No video file uploaded", 400
    file = request.files['video']
    if file.filename == '':
        return "No selected file", 400
    
    # Placeholder for video processing logic
    return f"<h3>Successfully received video: {file.filename}</h3><p>AI SEO & Compliance scan in progress...</p><a href='/'>Upload another</a>"

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

if __name__ == '__main__':
    app.run(debug=True)