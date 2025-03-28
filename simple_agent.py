import os
import sys
import json
import argparse
from agent import AssistantAgent

class SimpleResponseClient:
    """A simple client that returns predefined responses for testing."""
    
    def __init__(self, scenario="meeting"):
        self.iteration = 0
        
        # Define responses for different scenarios
        self.scenarios = {
            "meeting": [
                "FUNCTION_CALL: check_calendar_availability|tomorrow 3 PM",
                "FUNCTION_CALL: schedule_meeting|John,tomorrow 3 PM",
                "FUNCTION_CALL: send_email|John,Meeting Reminder,Hi John, This is a reminder about our meeting tomorrow at 3 PM.",
                "FINAL_ANSWER: I've scheduled a meeting with John for tomorrow at 3 PM and sent an email reminder."
            ],
            "availability": [
                "FUNCTION_CALL: check_calendar_availability|tomorrow 2 PM",
                "FINAL_ANSWER: Yes, you are available tomorrow at 2 PM. Would you like me to schedule a meeting?"
            ],
            "email": [
                "FUNCTION_CALL: send_email|Sarah,Project Update,Hi Sarah, Here's an update on the project we discussed yesterday.",
                "FINAL_ANSWER: I've sent an email to Sarah with the subject 'Project Update'."
            ]
        }
        
        # Select the appropriate responses
        self.responses = self.scenarios.get(scenario, self.scenarios["meeting"])
    
    def generate_content(self, prompt):
        # Return the next response in sequence
        if self.iteration < len(self.responses):
            response = self.responses[self.iteration]
            self.iteration += 1
            return response
        else:
            return "FINAL_ANSWER: All tasks completed."

def process_query_simple(query, scenario="meeting"):
    """Process a query and return just the final answer without debug output."""
    # Initialize the agent and client (with verbose=False to suppress console output)
    agent = AssistantAgent(verbose=False)
    client = SimpleResponseClient(scenario)
    
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Process the query silently
    result = agent.process_query(query, client, show_iterations=False)
    
    # Extract the final answer without the FINAL_ANSWER prefix
    final_answer = result['final_answer']
    if final_answer.startswith("FINAL_ANSWER:"):
        final_answer = final_answer[13:].strip()
    
    # Return just the clean final answer
    return final_answer

def main():
    """Process command-line arguments and run the simple agent."""
    parser = argparse.ArgumentParser(description='Run the Smart Assistant Agent in simplified mode')
    parser.add_argument('query', nargs='*', help='The query to process')
    parser.add_argument('--scenario', '-s', choices=['meeting', 'availability', 'email'], 
                        default='meeting', help='The scenario to test (default: meeting)')
    parser.add_argument('--debug', '-d', action='store_true', 
                        help='Show debug information in console')
    args = parser.parse_args()
    
    query = ' '.join(args.query) if args.query else None
    
    if not query:
        # Get query from user input
        print("Enter your query:")
        query = input("> ")
    
    if query:
        # Process the query
        final_answer = process_query_simple(query, args.scenario)
        
        # Just print the clean final answer
        print(final_answer)
        
        # If debug flag is set, also show the data changes
        if args.debug:
            print("\n--- Debug Information ---")
            # Display the calendar and email data
            data_dir = os.path.join(os.path.dirname(__file__), 'data')
            try:
                with open(os.path.join(data_dir, 'calendar.json'), 'r') as f:
                    calendar_data = json.load(f)
                    if calendar_data:
                        print("\nCalendar:")
                        for meeting in calendar_data:
                            print(f"- Meeting with {meeting['attendee']} at {meeting['start_time']}")
            except Exception:
                pass
            
            try:
                with open(os.path.join(data_dir, 'emails.json'), 'r') as f:
                    email_data = json.load(f)
                    if email_data:
                        print("\nEmails:")
                        for email in email_data:
                            print(f"- Email to {email['to']} with subject '{email['subject']}'")
            except Exception:
                pass
    else:
        print("No query provided. Exiting.")

if __name__ == "__main__":
    main() 