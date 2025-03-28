import json
import re
from functions.calendar_functions import check_calendar_availability, schedule_meeting
from functions.email_functions import send_email

# Dictionary mapping function names to actual functions
FUNCTION_MAP = {
    "check_calendar_availability": check_calendar_availability,
    "schedule_meeting": schedule_meeting,
    "send_email": send_email
}

class AssistantAgent:
    def __init__(self, verbose=False):
        self.max_iterations = 4  # Increased to 4 to allow for more complex tasks
        self.verbose = verbose
        self.system_prompt = """You are an assistant that helps users perform tasks by calling functions.

Analyze the user query and decide which Python function(s) to call. You'll see results and can make multiple function calls in sequence.

Available functions:
1. check_calendar_availability(time_str): Checks if a time slot is available on the calendar. Returns availability status and details.
2. schedule_meeting(person, time_str, title=None): Schedules a meeting with a person at a specific time. Returns success status and meeting details.
3. send_email(recipient, subject, body=None): Sends an email to a recipient with the given subject and body. Returns success status.

IMPORTANT INSTRUCTIONS:
- DO NOT use functions that aren't in this list.
- When you need to call a function, format your response EXACTLY as: FUNCTION_CALL: function_name|param1,param2,...
- After seeing function results, you can call another function if needed or provide a final answer.
- Your final answer should be prefixed with: FINAL_ANSWER:
- For calendar functions, time strings can include "today", "tomorrow", or times like "3 PM", "15:00"
- When scheduling meetings, check availability first before attempting to schedule
- Functions use a JSON database to store calendar and email data persistently

Task flow examples:
1. Checking availability: check_calendar_availability → final answer
2. Scheduling meeting: check_calendar_availability → schedule_meeting → send_email → final answer

Now, analyze the user query and respond with the appropriate function call or final answer.
"""

    def _extract_function_call(self, llm_response):
        """Extract a function call from the LLM response."""
        # Look for the exact function call format
        func_call_match = re.search(r"FUNCTION_CALL:\s*(\w+)\|(.+?)(?=\n|$)", llm_response)
        
        if func_call_match:
            function_name = func_call_match.group(1).strip()
            params_str = func_call_match.group(2).strip()
            return f"FUNCTION_CALL: {function_name}|{params_str}"
        
        # Try a more lenient approach to find function calls
        for function_name in FUNCTION_MAP.keys():
            # Look for patterns like "call check_calendar_availability with parameter X"
            pattern = rf"(?:call|use|execute)?\s*{function_name}\s*(?:\(|\s+with\s+|:)?\s*([^)]+)(?:\)|\.|\n|$)"
            func_match = re.search(pattern, llm_response, re.IGNORECASE)
            
            if func_match:
                params_str = func_match.group(1).strip().replace("=", ",").replace(" and ", ",")
                # Clean up the parameters
                params_str = re.sub(r'[\'"]', '', params_str)  # Remove quotes
                params_str = re.sub(r'\s*,\s*', ',', params_str)  # Clean up commas
                return f"FUNCTION_CALL: {function_name}|{params_str}"
        
        return None

    def _execute_function_call(self, function_call):
        """Execute a function call string and return the result."""
        try:
            # Parse the function call
            parts = function_call.split(":", 1)
            if len(parts) != 2 or parts[0].strip() != "FUNCTION_CALL":
                return {"error": "Invalid function call format"}
            
            function_info = parts[1].strip()
            function_parts = function_info.split("|", 1)
            
            if len(function_parts) != 2:
                return {"error": "Invalid function call format"}
            
            function_name = function_parts[0].strip()
            params_str = function_parts[1].strip()
            
            # Check if function exists
            if function_name not in FUNCTION_MAP:
                return {"error": f"Function '{function_name}' not found"}
            
            # Parse parameters
            params = []
            kwargs = {}
            
            # Special handling for send_email function to handle commas in body
            if function_name == "send_email":
                email_parts = params_str.split(",", 2)  # Split only on first two commas
                if len(email_parts) >= 1:
                    params.append(email_parts[0].strip())  # recipient
                if len(email_parts) >= 2:
                    params.append(email_parts[1].strip())  # subject
                if len(email_parts) >= 3:
                    kwargs["body"] = email_parts[2].strip()  # body as kwarg
            else:
                # Regular parameter parsing for other functions
                if params_str:
                    # Handle both positional and keyword arguments
                    # For simplicity, assuming comma-separated values
                    for param in params_str.split(","):
                        param = param.strip()
                        if "=" in param:
                            # Keyword argument
                            key, value = param.split("=", 1)
                            # Try to convert to appropriate type
                            try:
                                if value.lower() == "true":
                                    value = True
                                elif value.lower() == "false":
                                    value = False
                                elif value.lower() == "none":
                                    value = None
                                elif value.isdigit():
                                    value = int(value)
                                elif value.replace(".", "", 1).isdigit():
                                    value = float(value)
                            except:
                                pass
                            kwargs[key.strip()] = value
                        else:
                            # Positional argument
                            params.append(param)
            
            # Execute the function
            function = FUNCTION_MAP[function_name]
            result = function(*params, **kwargs)
            
            return {
                "function": function_name,
                "params": params,
                "kwargs": kwargs,
                "result": result
            }
        except Exception as e:
            return {"error": str(e)}

    def process_query(self, query, llm_client, show_iterations=False):
        """
        Process a user query using an iterative approach with an LLM.
        
        Args:
            query (str): The user's query
            llm_client: A client that can call an LLM API
            show_iterations (bool): Whether to print each iteration
            
        Returns:
            dict: The final result with full conversation history
        """
        iteration = 0
        last_result = None
        conversation_history = []
        
        if show_iterations:
            print("\n=== Agent Execution Started ===")
            print(f"User Query: {query}")
            print("=" * 50)
        
        while iteration < self.max_iterations:
            if show_iterations:
                print(f"\n--- Iteration {iteration + 1} ---")
                
            # Prepare the prompt for the LLM
            if last_result is None:
                current_prompt = f"{self.system_prompt}\n\nUser query: {query}"
            else:
                # Include the result of the previous function call
                result_str = json.dumps(last_result, indent=2)
                current_prompt = f"{current_prompt}\n\nResult of function call: {result_str}"
                current_prompt += "\n\nWhat would you like to do next? Call another function or provide a final answer:"
            
            # Call the LLM - Only log to console in verbose mode, never to chat
            llm_response = self._call_llm(llm_client, current_prompt)
            
            if show_iterations:
                print(f"LLM Response: {llm_response}")
            
            # Record this step in conversation history
            conversation_history.append({
                "iteration": iteration + 1,
                "prompt": current_prompt,
                "llm_response": llm_response
            })
            
            # Check if it's a function call or try to extract one
            function_call = None
            if "FUNCTION_CALL:" in llm_response:
                # Use regex to extract the exact function call format
                function_call = self._extract_function_call(llm_response)
            else:
                # Try to extract a function call from free text
                function_call = self._extract_function_call(llm_response)
            
            if function_call:
                # Execute the function call
                result = self._execute_function_call(function_call)
                last_result = result
                
                if show_iterations:
                    # Display the function call in a clean format
                    function_name = result.get("function", "unknown")
                    params_display = ", ".join([f"'{p}'" for p in result.get("params", [])])
                    kwargs_display = ", ".join([f"{k}='{v}'" for k, v in result.get("kwargs", {}).items()])
                    all_params = ", ".join(filter(None, [params_display, kwargs_display]))
                    
                    print(f"  Function Call: {function_name}({all_params})")
                    
                    # Display simplified result for better readability
                    if "result" in result and isinstance(result["result"], dict):
                        print("  Result:")
                        for key, value in result["result"].items():
                            print(f"    {key}: {value}")
                    else:
                        print(f"  Result: {result}")
                
                # Record the function call result
                conversation_history[-1]["function_call"] = function_call
                conversation_history[-1]["function_result"] = result
            elif "FINAL_ANSWER:" in llm_response:
                # It's the final answer
                conversation_history[-1]["final_answer"] = True
                
                if show_iterations:
                    final_answer = llm_response.replace("FINAL_ANSWER:", "").strip()
                    print("\n=== Agent Execution Complete ===")
                    print(f"Final Answer: {final_answer}")
                    print("=" * 50)
                break
            else:
                # Treat it as a final answer if the LLM didn't generate a function call
                conversation_history[-1]["final_answer"] = True
                
                if show_iterations:
                    print("\n=== Agent Execution Complete ===")
                    print(f"Response: {llm_response}")
                    print("=" * 50)
                break
            
            iteration += 1
        
        # Generate a final summary if we hit the iteration limit
        if iteration >= self.max_iterations and not any(step.get("final_answer") for step in conversation_history):
            final_prompt = f"{current_prompt}\n\nYou've reached the maximum number of iterations. Please provide a final summary:"
            final_response = self._call_llm(llm_client, final_prompt)
            
            if show_iterations:
                print("\n=== Maximum Iterations Reached ===")
                print(f"Final Summary: {final_response}")
                print("=" * 50)
            
            conversation_history.append({
                "iteration": iteration + 1,
                "prompt": final_prompt,
                "llm_response": final_response,
                "final_answer": True
            })
        
        # Extract just the final answer for the response
        final_step = next((step for step in reversed(conversation_history) if step.get("final_answer")), None)
        final_answer = final_step["llm_response"] if final_step else "No final answer was generated."
        
        # Format the final answer by removing the FINAL_ANSWER: prefix if present
        if "FINAL_ANSWER:" in final_answer:
            final_answer = final_answer.replace("FINAL_ANSWER:", "").strip()
        
        return {
            "query": query,
            "conversation_history": conversation_history,
            "final_answer": final_answer
        }
    
    def _call_llm(self, llm_client, prompt):
        """
        Call the LLM with the given prompt.
        
        This function calls the LLM client's generate_content method.
        """
        # The LLM client should have a generate_content method
        return llm_client.generate_content(prompt) 