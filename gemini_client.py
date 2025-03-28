import os
import json
import google.generativeai as genai

class GeminiClient:
    """A client that uses Google's Gemini API to generate responses."""
    
    def __init__(self, api_key=None):
        """Initialize the Gemini client with the provided API key."""
        self.api_key = api_key
        self.model_name = "gemini-pro"  # Using the text-only model
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None
            print("Warning: No API key provided. GeminiClient is not functional.")
    
    def set_api_key(self, api_key):
        """Set or update the API key."""
        self.api_key = api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_content(self, prompt):
        """Generate content using the Gemini model."""
        if not self.model:
            return "ERROR: No API key provided. Please configure your Gemini API key."
        
        try:
            response = self.model.generate_content(prompt)
            
            # Extract and return just the text content
            if hasattr(response, 'text'):
                return response.text
            else:
                # Handle older API versions or unexpected response format
                return str(response)
                
        except Exception as e:
            error_msg = f"Error generating content: {str(e)}"
            print(error_msg)
            return f"ERROR: {error_msg}"
    
    def save_api_key(self, storage_path=None):
        """Save the API key to a local file."""
        if not self.api_key:
            return False
            
        if storage_path is None:
            # Default to storing in the data directory
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            os.makedirs(data_dir, exist_ok=True)
            storage_path = os.path.join(data_dir, 'credentials.json')
        
        try:
            # Check if file exists and has other credentials
            existing_creds = {}
            if os.path.exists(storage_path):
                with open(storage_path, 'r') as f:
                    try:
                        existing_creds = json.load(f)
                    except json.JSONDecodeError:
                        existing_creds = {}
            
            # Update with the new API key
            existing_creds['gemini_api_key'] = self.api_key
            
            # Save back to file
            with open(storage_path, 'w') as f:
                json.dump(existing_creds, f)
                
            return True
        except Exception as e:
            print(f"Error saving API key: {e}")
            return False
    
    @classmethod
    def load_from_storage(cls, storage_path=None):
        """Load an API key from storage and create a new client."""
        if storage_path is None:
            # Default to loading from the data directory
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            storage_path = os.path.join(data_dir, 'credentials.json')
        
        if not os.path.exists(storage_path):
            return cls(None)
            
        try:
            with open(storage_path, 'r') as f:
                creds = json.load(f)
                api_key = creds.get('gemini_api_key')
                return cls(api_key)
        except Exception as e:
            print(f"Error loading API key: {e}")
            return cls(None) 