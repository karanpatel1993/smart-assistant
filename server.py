from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from console_agent import run_agent_in_console

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# No need to initialize the agent as we're using process_query_simple directly

# No need for MockLLMClient class as the simple_agent handles this internally

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
        
        # Process the query using our console agent with clean output mode
        # Use "auto" scenario to automatically detect the intent
        clean_response = run_agent_in_console(query, scenario="auto", clean_output=True)
        
        # Return just the clean response to the extension
        simplified_result = {
            "query": query,
            "response": clean_response
        }
        
        return jsonify(simplified_result)
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
    
    print("Starting Assistant API server...")
    app.run(host='0.0.0.0', port=8080, debug=True) 