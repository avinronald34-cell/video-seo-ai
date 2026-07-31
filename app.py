import os
from flask import Flask, request, redirect, url_for, send_from_directory, make_response

app = Flask(__name__)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Video SEO AI</title>
    <meta name="theme-color" content="#000000">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            color: #333;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }
        .container {
            background: #ffffff;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 100%;
        }
        header {
            border-bottom: 2px solid #eaeaea;
            padding-bottom: 15px;
            margin-bottom: 20px;
        }
        nav a {
            color: #0066cc;
            text-decoration: none;
            margin-right: 10px;
        }
        nav a:hover {
            text-decoration: underline;
        }
        button {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background-color: #0055b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Video SEO AI</h1>
            <p>Welcome, Guest</p>
            <nav>
                <a href="/history">Scan History</a> | 
                <a href="/logout">Logout</a>
            </nav>
        </header>

        <main>
            <section>
                <h2>Upload Video for SEO & Compliance Scan</h2>
                <form action="/scan" method="POST" enctype="multipart/form-data">
                    <input type="file" name="video" required>
                    <button type="submit">Run Video Scan</button>
                </form>
            </section>
        </main>
    </div>
</body>
</html>"""

@app.route('/')
def index():
    response = make_response(HTML_PAGE)
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