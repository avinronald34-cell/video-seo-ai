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
        
        client = genai.Client(api_key=api_key)
        diagnostic_logs.append("GenAI Client created successfully.")
        
        # Enhanced prompt specifying the exact fields required
        prompt_text = (
            f"Analyze the video file named '{filename}' for a comprehensive YouTube SEO and compliance check. "
            f"Provide the output strictly using the following headings and structure:\n\n"
            f"1. **Score**: (Give an overall SEO score out of 100)\n"
            f"2. **Copyrights Details**: (Analyze compliance, risk of copyright flags, or safe usage notes based on filename/topic)\n"
            f"3. **Observation**: (Detailed key observations about the video content theme)\n"
            f"4. **Suggestions**: (Actionable improvements to boost engagement and watch time)\n"
            f"5. **Optimized Title**: (A catchy, high-CTR YouTube title)\n"
            f"6. **Optimized Description**: (A well-structured YouTube description with timestamps placeholder)\n"
            f"7. **Tags**: (10-15 relevant comma-separated SEO tags)"
        )
        
        response_ai = None
        for m_name in ['gemini-3.6-flash', 'gemini-3.5-flash']:
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
            ai_description = "Error: Model did not return a valid text response."
            
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
            .container {{ background: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); max-width: 700px; width: 100%; }}
            .box {{ background: #f9f9fb; padding: 20px; border-radius: 6px; border: 1px solid #eaeaea; margin-top: 10px; white-space: pre-wrap; font-size: 14px; line-height: 1.5; }}
            .logs {{ background: #1e1e1e; color: #00ff66; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; margin-top: 10px; }}
            a {{ color: #0066cc; text-decoration: none; display: inline-block; margin-top: 20px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Scan Report: {filename}</h2>
            <hr>
            <h3>Generated AI SEO & Compliance Report:</h3>
            <div class="box">{ai_description}</div>
            
            <h3>Execution & Diagnostic Logs:</h3>
            <div class="logs">{logs_str}</div>
            
            <a href="/dashboard">← Back to Dashboard</a>
        </div>
    </body>
    </html>
    """
    return make_response(result_html, 200, {'Content-Type': 'text/html; charset=utf-8'})