@app.route('/scan', methods=['POST'])
def scan():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
        
    file = request.files.get('video')
    filename = file.filename if file and file.filename else "uploaded_video.mp4"
    
    diagnostic_logs = []
    ai_description = ""
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return "Configuration Error: GEMINI_API_KEY environment variable is missing on Render.", 500
        
        diagnostic_logs.append("API Key present.")
        
        # Initialize the official Google GenAI client
        client = genai.Client(api_key=api_key)
        diagnostic_logs.append("GenAI Client created successfully.")
        
        prompt_text = (
            f"Generate a professional YouTube video title, an SEO-optimized description, "
            f"and 4 relevant tags for a video file named: {filename}"
        )
        
        response_ai = None
        # Use the precise modern production model IDs
        for m_name in ['gemini-2.5-flash', 'gemini-2.0-flash']:
            try:
                diagnostic_logs.append(f"Attempting model: {m_name}")
                response_ai = client.models.generate_content(
                    model=m_name,
                    contents=prompt_text
                )
                if response_ai and response_ai.text:
                    diagnostic_logs.append(f"Success with model: {m_name}")
                    break
            except Exception as model_err:
                diagnostic_logs.append(f"Model {m_name} error: {str(model_err)}")
                continue
                
        if response_ai and hasattr(response_ai, 'text') and response_ai.text:
            ai_description = response_ai.text
        else:
            ai_description = "Error: Models did not return a valid text response. Check logs below."
            
    except Exception as e:
        traceback.print_exc()
        ai_description = f"Runtime Exception: {str(e)}"

    logs_str = "<br>".join(diagnostic_logs)
    
    result_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Scan Results & Diagnostics</title>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #f4f4f9; padding: 20px; color: #333; display: flex; justify-content: center; }}
            .container {{ background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 650px; width: 100%; }}
            .box {{ background: #f9f9fb; padding: 15px; border-radius: 6px; border: 1px solid #eaeaea; margin-top: 10px; white-space: pre-wrap; font-size: 14px; }}
            .logs {{ background: #1e1e1e; color: #00ff66; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; margin-top: 10px; }}
            a {{ color: #0066cc; text-decoration: none; display: inline-block; margin-top: 20px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Scan Report: {filename}</h2>
            <hr>
            <h3>Generated AI SEO Metadata:</h3>
            <div class="box">{ai_description}</div>
            
            <h3>Execution & Diagnostic Logs:</h3>
            <div class="logs">{logs_str}</div>
            
            <a href="/dashboard">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """
    return make_response(result_html, 200, {'Content-Type': 'text/html; charset=utf-8'})