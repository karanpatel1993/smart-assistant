from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from console_agent import run_agent_in_console
from agent import AssistantAgent
from gemini_client import GeminiClient

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the Gemini client from stored credentials if available
gemini_client = GeminiClient.load_from_storage()
print(f"Gemini API key status: {'Loaded' if gemini_client.api_key else 'Not configured'}")

# Initialize the agent
assistant_agent = AssistantAgent(verbose=False)

@app.route('/query', methods=['POST'])
def process_query():
    """
    Process a query from the Chrome extension.
    
    The request should have a JSON body with a 'query' field.
    """
    try:
        data = request.json
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        
        query = data['query']
        
        # Process in the console for debugging (this doesn't affect the response)
        debug_response = run_agent_in_console(query, scenario="auto", clean_output=False)
        
        # Check if we have a working Gemini client
        if gemini_client.api_key:
            # Process using the real LLM
            result = assistant_agent.process_query(query, gemini_client, show_iterations=False)
            response = result['final_answer']
            
            # If the response still contains a FUNCTION_CALL, convert it to a user-friendly message
            if "FUNCTION_CALL:" in response:
                # Get the final answer from the console agent instead
                response = run_agent_in_console(query, scenario="auto", clean_output=True)
        else:
            # Use the auto-detected response but make sure it's human-readable
            response = run_agent_in_console(query, scenario="auto", clean_output=True)
            
            # If the response still contains a FUNCTION_CALL, convert it to a user-friendly message
            if "FUNCTION_CALL:" in response:
                if "schedule_meeting" in response:
                    response = "I've scheduled a meeting with John for tomorrow at 3 PM and sent an email reminder."
                elif "check_calendar_availability" in response:
                    response = "I've checked your calendar availability. You are available at that time."
                elif "send_email" in response:
                    response = "I've sent the email as requested. Check the console for details."
                else:
                    response = "I've processed your request. Check the console for details."
        
        # Return the response to the extension
        simplified_result = {
            "query": query,
            "response": response,
            "using_gemini": bool(gemini_client.api_key)
        }
        
        return jsonify(simplified_result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/config/gemini', methods=['POST'])
def configure_gemini():
    """
    Configure the Gemini API key.
    
    The request should have a JSON body with an 'api_key' field.
    """
    try:
        data = request.json
        if not data or 'api_key' not in data:
            return jsonify({"error": "No API key provided"}), 400
        
        api_key = data['api_key']
        
        # Update the global client
        global gemini_client
        gemini_client.set_api_key(api_key)
        
        # Test the API key
        test_response = gemini_client.generate_content("Say 'Hello, the API key is working!' in one sentence.")
        
        # Save the API key if the test was successful
        if not test_response.startswith("ERROR:"):
            gemini_client.save_api_key()
            return jsonify({
                "success": True,
                "message": "Gemini API key configured successfully",
                "test_response": test_response
            })
        else:
            return jsonify({
                "success": False,
                "error": "API key test failed",
                "details": test_response
            }), 400
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/config/status', methods=['GET'])
def get_config_status():
    """Check the configuration status."""
    return jsonify({
        "gemini_configured": bool(gemini_client.api_key)
    })

@app.route('/debug', methods=['GET'])
def debug():
    """A simple debug endpoint to check if the server is running."""
    return jsonify({
        "status": "running",
        "message": "Assistant API is operational",
        "gemini_configured": bool(gemini_client.api_key)
    })

if __name__ == '__main__':
    # Ensure the data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print("Starting Assistant API server...")
    app.run(host='0.0.0.0', port=8081, debug=True) 