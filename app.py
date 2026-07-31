import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, make_response

app = Flask(__name__, static_folder='static', template_folder='templates')

@app.route('/')
def index():
    # Render the template and force the browser to read it as HTML
    rendered_html = render_template('index.html')
    response = make_response(rendered_html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response

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
    return f"<h3>Successfully received video: {file.filename}</h3><p>AI SEO & Compliance scan in progress...</p><a href='/'>Upload another</a>"

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True)