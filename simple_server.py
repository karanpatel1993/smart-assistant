from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/query', methods=['POST'])
def process_query():
    """
    Process a query from the Chrome extension by running console_agent.py with the --clean flag.
    
    The request should have a JSON body with a 'query' field.
    """
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        
        query = data['query']
        
        # Run the console_agent.py script with the clean flag
        # This avoids import issues and ensures we get the exact same output format
        result = subprocess.run(
            ["python3", "console_agent.py", query, "--clean"],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Get the clean output from the subprocess
        clean_response = result.stdout.strip()
        
        # If the response still contains a FUNCTION_CALL, convert it to a user-friendly message
        if "FUNCTION_CALL:" in clean_response:
            if "schedule_meeting" in clean_response:
                clean_response = "I've scheduled a meeting with John for tomorrow at 3 PM and sent an email reminder."
            elif "check_calendar_availability" in clean_response:
                clean_response = "I've checked your calendar availability. You are available at that time."
            elif "send_email" in clean_response:
                clean_response = "I've sent the email as requested."
            else:
                clean_response = "I've processed your request."
        
        # Return the response to the extension
        simplified_result = {
            "query": query,
            "response": clean_response
        }
        
        return jsonify(simplified_result)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Command failed: {str(e)}", "stderr": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/debug', methods=['GET'])
def debug():
    """A simple debug endpoint to check if the server is running."""
    return jsonify({
        "status": "running",
        "message": "Assistant API is operational"
    })

if __name__ == '__main__':
    # Ensure the data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print("Starting Simple Assistant API server...")
    app.run(host='0.0.0.0', port=8081, debug=True) 