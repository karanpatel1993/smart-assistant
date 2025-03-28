import os
import sys
import time
import json
import re
import argparse
from agent import AssistantAgent

# Enhanced mock LLM client for testing with more realistic responses
class MockLLMClient:
    def __init__(self):
        self.state = {"iteration": 0, "person": None, "time_str": None, "day": None, "time_short": None}
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.responses = {
            "meeting_query": {
                "initial": "FUNCTION_CALL: check_calendar_availability|{time}",
                "after_check": "FUNCTION_CALL: schedule_meeting|{person},{time}",
                "after_schedule": "FUNCTION_CALL: send_email|{person},Meeting Reminder,Hi {person}, This is a reminder about our meeting {day} at {time_short}.",
                "final": "FINAL_ANSWER: I've scheduled a meeting with {person} for {day} at {time_short} and sent an email reminder."
            },
            "check_availability": {
                "initial": "FUNCTION_CALL: check_calendar_availability|{time}",
                "after_check_available": "FINAL_ANSWER: Yes, you are available {day} at {time_short}. Would you like me to schedule a meeting?",
                "after_check_unavailable": "FINAL_ANSWER: Sorry, you are not available {day} at {time_short}. You already have a meeting scheduled at that time: {conflict}."
            },
            "default": "I don't know how to handle that request yet."
        }
        
    def extract_info_from_query(self, query):
        """Extract person and time information from the query"""
        person_match = re.search(r"with\s+(\w+)", query)
        time_match = re.search(r"(tomorrow|today)\s+at\s+([\w\s:.]+?)(?:\s+and|$|\?|\.)", query)
        
        if person_match:
            self.state["person"] = person_match.group(1)
        
        if time_match:
            self.state["day"] = time_match.group(1)
            self.state["time_short"] = time_match.group(2).strip()
            self.state["time_str"] = f"{self.state['day']} {self.state['time_short']}"
        
        return self.state
    
    def check_calendar_for_conflict(self, time_str):
        """Check if there's a conflict in the calendar for the specified time"""
        try:
            # Read the calendar file
            calendar_path = os.path.join(self.data_dir, 'calendar.json')
            if not os.path.exists(calendar_path):
                return None
                
            with open(calendar_path, 'r') as f:
                meetings = json.load(f)
                
            if not meetings:
                return None
                
            # Check for meetings at the specified time
            for meeting in meetings:
                # Simple string match for the time (this is a mock implementation)
                if time_str in meeting['start_time']:
                    return {
                        "conflict": True,
                        "meeting": meeting
                    }
                    
            return None
        except Exception as e:
            print(f"Error checking calendar: {e}")
            return None
        
    def generate_content(self, prompt):
        user_query = None
        
        # Extract the user query if this is the first call
        if "User query:" in prompt:
            query_match = re.search(r"User query: (.*?)(?:\n|$)", prompt)
            if query_match:
                user_query = query_match.group(1)
                self.extract_info_from_query(user_query)
                
                # Determine query type
                if "check" in user_query.lower() and "available" in user_query.lower():
                    self.state["query_type"] = "check_availability"
                elif "schedule" in user_query.lower() or "meeting" in user_query.lower():
                    self.state["query_type"] = "meeting_query"
                else:
                    self.state["query_type"] = "default"
        
        # Handle meeting scheduling flow
        if self.state.get("query_type") == "meeting_query":
            # Default values if not set
            if not self.state["person"]:
                self.state["person"] = "John"
            if not self.state["time_str"]:
                self.state["day"] = "tomorrow"
                self.state["time_short"] = "3 PM"
                self.state["time_str"] = "tomorrow 3 PM"
                
            # Increment the iteration counter if we see a result of function call
            if "Result of function call" in prompt:
                self.state["iteration"] += 1
                
            # Check for conflicts directly in the calendar
            conflict = None
            if self.state["iteration"] == 1:
                conflict = self.check_calendar_for_conflict(self.state["time_short"])
                
            # Determine which response to give based on the iteration and conflict status
            if self.state["iteration"] == 0:
                return self.responses["meeting_query"]["initial"].format(time=self.state["time_str"])
            elif self.state["iteration"] == 1:
                if conflict:
                    return f"FINAL_ANSWER: Sorry, you already have a meeting with {conflict['meeting']['attendee']} at that time. Would you like to choose a different time?"
                else:
                    return self.responses["meeting_query"]["after_check"].format(
                        person=self.state["person"], 
                        time=self.state["time_str"]
                    )
            elif self.state["iteration"] == 2:
                return self.responses["meeting_query"]["after_schedule"].format(
                    person=self.state["person"], 
                    time=self.state["time_str"],
                    time_short=self.state["time_short"],
                    day=self.state["day"]
                )
            else:
                # Return final answer for 3+ iterations
                return self.responses["meeting_query"]["final"].format(
                    person=self.state["person"],
                    time_short=self.state["time_short"],
                    day=self.state["day"]
                )
        
        # Handle availability check flow
        elif self.state.get("query_type") == "check_availability":
            # Default values if not set
            if not self.state["time_str"]:
                self.state["day"] = "tomorrow"
                self.state["time_short"] = "3 PM" 
                self.state["time_str"] = "tomorrow 3 PM"
                
            # Increment the iteration counter if we see a result of function call
            if "Result of function call" in prompt:
                self.state["iteration"] += 1
                
            # Initial availability check
            if self.state["iteration"] == 0:
                return self.responses["check_availability"]["initial"].format(time=self.state["time_str"])
            else:
                # Check for conflicts directly in the calendar
                conflict = self.check_calendar_for_conflict(self.state["time_short"])
                
                if not conflict:
                    return self.responses["check_availability"]["after_check_available"].format(
                        day=self.state["day"],
                        time_short=self.state["time_short"]
                    )
                else:
                    # Extract meeting information from the conflict
                    meeting = conflict['meeting']
                    meeting_title = meeting.get('title', 'Unknown meeting')
                    
                    return self.responses["check_availability"]["after_check_unavailable"].format(
                        day=self.state["day"],
                        time_short=self.state["time_short"],
                        conflict=meeting_title
                    )
        
        # Default response
        return self.responses["default"]

def run_query_with_display(query, preserve_data=False):
    """Run a query with the agent and display each step of execution."""
    agent = AssistantAgent(verbose=True)
    client = MockLLMClient()
    
    # Extract person and time information from the query
    client.extract_info_from_query(query)
    
    # Ensure the data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Only reset calendar data if not preserving state
    if not preserve_data:
        # Reset the calendar and emails files to empty arrays
        for file_name in ['calendar.json', 'emails.json']:
            file_path = os.path.join(data_dir, file_name)
            with open(file_path, 'w') as f:
                json.dump([], f)
        print(f"\nCalendar and email data reset for testing")
    else:
        print(f"\nPreserving existing calendar and email data")
    
    # Process the query with displayed iterations
    print(f"\nProcessing query: '{query}'")
    result = agent.process_query(query, client, show_iterations=True)
    
    # Display summary of function calls
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
                
                if 'result' in step['function_result'] and 'error' not in step['function_result']['result']:
                    status = "✓ Success"
                else:
                    status = "✗ Failed"
                
                print(f"{i+1}. {status}: {function_name}({param_str})")
    
    # Display the final answer
    print("\n=== Final Answer ===")
    print(result['final_answer'])
    print("=" * 50)
    
    # Display the calendar and email data after execution
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
    
    return result

def main():
    """Main function to handle command line arguments and run the debug agent."""
    parser = argparse.ArgumentParser(description='Debug the Smart Assistant Agent')
    parser.add_argument('query', nargs='*', help='The query to process')
    parser.add_argument('--preserve', '-p', action='store_true', help='Preserve existing calendar data')
    parser.add_argument('--test-conflict', '-t', action='store_true', help='Run a test sequence showing conflict detection')
    args = parser.parse_args()
    
    if args.test_conflict:
        # Run a sequence of commands to demonstrate conflict handling
        print("=== Running conflict detection test ===")
        print("Step 1: Schedule a meeting with Sarah")
        run_query_with_display("Schedule a meeting with Sarah for tomorrow at 3 PM", preserve_data=False)
        
        print("\n\nStep 2: Check availability for the same time")
        run_query_with_display("Check if I'm available tomorrow at 3 PM", preserve_data=True)
        
        print("\n\nStep 3: Try to schedule another meeting at the same time")
        run_query_with_display("Schedule a meeting with John for tomorrow at 3 PM", preserve_data=True)
        return
    
    query = ' '.join(args.query) if args.query else None
    
    if not query:
        # Get query from user input
        print("Enter your query (examples):")
        print("1. 'Schedule a meeting with John for tomorrow at 3 PM and send him an email reminder'")
        print("2. 'Check if I'm available tomorrow at 2 PM'")
        query = input("> ")
    
    if query:
        run_query_with_display(query, preserve_data=args.preserve)
    else:
        print("No query provided. Exiting.")

if __name__ == "__main__":
    # Use the main function to handle command-line arguments
    main() 