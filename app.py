import os
from flask import Flask, render_template, send_from_directory

app = Flask(__name__)

# --- Your existing routes go here ---
@app.route('/')
def index():
    return render_template('index.html')

# --- Add this route to explicitly serve the manifest for PWABuilder ---
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('.', 'manifest.json')

if __name__ == '__main__':
    app.run(debug=True)