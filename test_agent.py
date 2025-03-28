import json
import os
import sys
import time
from agent import AssistantAgent

# Simple mock LLM client for testing
class MockLLMClient:
    def __init__(self):
        pass
    
    def generate_content(self, prompt):
        return prompt

def run_test_queries():
    """Run a series of test queries to verify agent functionality."""
    agent = AssistantAgent()
    client = MockLLMClient()
    
    # Ensure the data directory exists
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Test queries
    test_queries = [
        "Schedule a meeting with John for tomorrow at 3 PM and send him an email reminder",
        "Check if I'm available next Monday at 2 PM",
        "Send an email to Sarah about the project deadline"
    ]
    
    print("\n===== RUNNING AGENT TESTS =====\n")
    
    for i, query in enumerate(test_queries):
        print(f"\n--- TEST {i+1}: {query} ---")
        
        try:
            # Process the query
            start_time = time.time()
            result = agent.process_query(query, client)
            elapsed_time = time.time() - start_time
            
            # Show the final answer
            print(f"Final answer: {result['final_answer']}")
            print(f"Processing time: {elapsed_time:.2f} seconds")
            print(f"Iterations: {len(result['conversation_history'])}")
            
            # Show the function calls that were made
            for i, step in enumerate(result['conversation_history']):
                if 'function_call' in step:
                    func_name = step['function_result']['function']
                    print(f"  Function called: {func_name}")
            
            print("Test PASSED")
            
        except Exception as e:
            print(f"Error: {e}")
            print("Test FAILED")
    
    print("\n===== ALL TESTS COMPLETED =====\n")

if __name__ == "__main__":
    run_test_queries() 