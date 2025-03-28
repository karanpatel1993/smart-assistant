import os
import sys
import json
import argparse
from agent import AssistantAgent

class SimpleConsoleClient:
    """A client that determines response based on query intent."""
    
    def __init__(self, scenario=None):
        self.iteration = 0
        self.query_type = None
        
        # Define responses for different scenarios
        self.scenarios = {
            "meeting": [
                "FUNCTION_CALL: check_calendar_availability|tomorrow 3 PM",
                "FUNCTION_CALL: schedule_meeting|John,tomorrow 3 PM",
                "FUNCTION_CALL: send_email|John,Meeting Reminder,Hi John, This is a reminder about our meeting tomorrow at 3 PM.",
                "FINAL_ANSWER: I've scheduled a meeting with John for tomorrow at 3 PM and sent an email reminder."
            ],
            "availability": [
                "FUNCTION_CALL: check_calendar_availability|tomorrow 3 PM",
                "FINAL_ANSWER: Sorry, you are not available tomorrow at 3 PM. You already have a meeting with John scheduled at that time."
            ],
            "email": [
                "FUNCTION_CALL: send_email|Sarah,Project Update,Hi Sarah, Here's an update on the project we discussed yesterday.",
                "FINAL_ANSWER: I've sent an email to Sarah with the subject 'Project Update'."
            ]
        }
        
        # If scenario is provided, force that scenario
        self.forced_scenario = scenario
    
    def detect_intent(self, query):
        """Detect the intent of the query."""
        query = query.lower()
        
        # If a scenario is forced, use that
        if self.forced_scenario:
            return self.forced_scenario
            
        # Check if it's about availability
        if ("do i have" in query or "am i available" in query or "is there a meeting" in query or 
            "check" in query and "available" in query or "check" in query and "calendar" in query):
            return "availability"
        # Check if it's about scheduling a meeting
        elif "schedule" in query or "set up" in query or "create" in query and "meeting" in query:
            return "meeting"
        # Check if it's about sending an email
        elif "email" in query or "send" in query and "message" in query:
            return "email"
        # Default to meeting scenario
        else:
            return "meeting"
    
    def generate_content(self, prompt):
        # Reset iteration if this is a new query
        if "User query:" in prompt:
            self.iteration = 0
            # Extract the query
            query_start = prompt.find("User query:") + len("User query:")
            query_end = prompt.find("\n", query_start) if "\n" in prompt[query_start:] else len(prompt)
            query = prompt[query_start:query_end].strip()
            
            # Detect intent from the query
            self.query_type = self.detect_intent(query)
        
        # Increment iteration if we're seeing a function result
        if "Result of function call" in prompt:
            self.iteration += 1
        
        # Use the detected query type to determine responses
        responses = self.scenarios.get(self.query_type, self.scenarios["meeting"])
        
        # Return the appropriate response based on iteration
        if self.iteration < len(responses):
            return responses[self.iteration]
        else:
            return "FINAL_ANSWER: All tasks completed."

def process_query(query, client, show_iterations=True):
    # Return the next response in sequence
    if client.iteration < len(client.responses):
        response = client.responses[client.iteration]
        client.iteration += 1
        return response
    else:
        return "FINAL_ANSWER: All tasks completed."

def run_agent_in_console(query, scenario=None, clean_output=False):
    """Run the agent in console mode and print the output."""
    # Initialize the agent with verbose=False to suppress internal messages
    agent = AssistantAgent(verbose=False)
    
    # Use our SimpleConsoleClient - pass scenario only if forcing a specific scenario
    client = SimpleConsoleClient(scenario if scenario != "auto" else None)
    
    # Process the query and print the result
    result = agent.process_query(query, client, show_iterations=not clean_output)
    
    # Format the final answer
    final_answer = result['final_answer']
    if final_answer.startswith("FINAL_ANSWER:"):
        final_answer = final_answer[13:].strip()
    
    # For clean output mode, just print the final answer
    if clean_output:
        print(final_answer)
        return final_answer
    else:
        # Format it with the prefix if we want all the details
        if not final_answer.startswith("FINAL_ANSWER:"):
            final_answer = f"FINAL_ANSWER: {final_answer}"
        print(final_answer)
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Reset the calendar and emails files
    for file_name in ['calendar.json', 'emails.json']:
        file_path = os.path.join(data_dir, file_name)
        with open(file_path, 'w') as f:
            json.dump([], f)
    
    # Display a summary of function calls if any
    print("\n=== Function Call Chain ===")
    for i, step in enumerate(result['conversation_history']):
        if 'function_call' in step:
            function_name = None
            params = []
            if 'function_result' in step and 'function' in step['function_result']:
                function_name = step['function_result']['function']
                params = step['function_result'].get('params', [])
                kwargs = step['function_result'].get('kwargs', {})
                
                param_str = ", ".join([f"'{p}'" for p in params] + 
                                     [f"{k}='{v}'" for k, v in kwargs.items()])
                
                print(f"{i+1}. {function_name}({param_str})")
    
    # Display the calendar and email data
    print("\n--- Calendar after execution ---")
    try:
        with open(os.path.join(data_dir, 'calendar.json'), 'r') as f:
            calendar_data = json.load(f)
            if calendar_data:
                for meeting in calendar_data:
                    print(f"Meeting: {meeting['title']}")
                    print(f"  With: {meeting['attendee']}")
                    print(f"  Time: {meeting['start_time']}")
                    print()
            else:
                print("No meetings scheduled.")
    except Exception as e:
        print(f"Error reading calendar: {e}")
    
    print("\n--- Emails after execution ---")
    try:
        with open(os.path.join(data_dir, 'emails.json'), 'r') as f:
            email_data = json.load(f)
            if email_data:
                for email in email_data:
                    print(f"Email to: {email['to']}")
                    print(f"Subject: {email['subject']}")
                    print(f"Body: {email['body'][:50]}..." if len(email['body']) > 50 else f"Body: {email['body']}")
                    print()
            else:
                print("No emails sent.")
    except Exception as e:
        print(f"Error reading emails: {e}")

def main():
    """Process command-line arguments and run the console agent."""
    parser = argparse.ArgumentParser(description='Run the Smart Assistant Agent in console mode')
    parser.add_argument('query', nargs='*', help='The query to process')
    parser.add_argument('--scenario', '-s', choices=['meeting', 'availability', 'email', 'auto'], 
                        default='auto', help='The scenario to test (default: auto)')
    parser.add_argument('--clean', '-c', action='store_true',
                        help='Output only the clean final answer with no debug info')
    args = parser.parse_args()
    
    query = ' '.join(args.query) if args.query else None
    
    if not query:
        # Get query from user input
        print("Enter your query:")
        query = input("> ")
    
    if query:
        # Run the agent with specified scenario
        clean_output = args.clean
        run_agent_in_console(query, args.scenario, clean_output)
    else:
        print("No query provided. Exiting.")

if __name__ == "__main__":
    main() 