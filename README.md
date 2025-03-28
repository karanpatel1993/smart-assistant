# Smart Assistant Backend

This is the backend server for the Smart Assistant system. It includes a function-calling agent that can help users perform tasks by calling various functions such as scheduling meetings and sending emails.

## Features

- Agent that processes natural language queries and calls appropriate functions
- Calendar management functions for checking availability and scheduling meetings
- Email functionality for sending messages to recipients
- Support for time parsing in various formats like "3pm", "3PM", "3 p.m.", etc.

## Getting Started

### Running the Server

To start the server:

- **On Windows**: Run `restart_server.bat`
- **On macOS/Linux**: Run `./restart_server.sh`

### Debug Mode

You can use the debug script to see the step-by-step reasoning process of the agent:

```bash
# Navigate to the backend directory
cd backend

# Run the debug script with a query
python debug_agent.py "Schedule a meeting with John for tomorrow at 3 PM and send him an email reminder"

# Preserve calendar data between runs (to test conflicts)
python debug_agent.py --preserve "Check if I'm available tomorrow at 3 PM"

# Run a test sequence showing conflict detection
python debug_agent.py --test-conflict
```

The debug script will show:

1. Each iteration of the agent's reasoning
2. The function calls it makes
3. The results of those function calls
4. The final answer provided to the user
5. A summary of any calendar events or emails created

### Console-Only Mode

For a simpler experience with output only in the console, use the console agent:

```bash
# Run the console agent with a specific scenario
python console_agent.py "Schedule a meeting with John for tomorrow at 3 PM" --scenario meeting
python console_agent.py "Check if I'm available tomorrow at 2 PM" --scenario availability
python console_agent.py "Send an email to Sarah about the project update" --scenario email

# Without a scenario argument, it defaults to the meeting scenario
python console_agent.py "Schedule a meeting with John for tomorrow at 3 PM"
```

The console agent provides predefined LLM responses for each scenario type, avoiding any issues with system prompts being displayed in the chat interface.

### Command-line Options

#### For debug_agent.py:

- `--preserve` or `-p`: Preserves existing calendar and email data between runs
- `--test-conflict` or `-t`: Runs a test sequence showing conflict detection with multiple queries

#### For console_agent.py:

- `--scenario` or `-s`: Choose the scenario type (meeting, availability, email)

## Example Queries

Try these example queries with the debug script:

- "Schedule a meeting with John for tomorrow at 3 PM"
- "Check if I'm available tomorrow at 2 PM"
- "Send an email to Sarah with the subject 'Project Update'"

## Time Format Support

The system supports various time formats, including:

- "3pm", "3PM", "3 pm", "3 PM", "3p.m.", "3P.M."
- 24-hour format like "15:00"
- Time references with "tomorrow" or "today"

## Troubleshooting

### System Prompts Appearing in Chat Interface

If you're seeing raw system prompts in your chat interface like this:

```
You are an assistant that helps users perform tasks by calling functions.
Analyze the user query and decide which Python function(s) to call.
FUNCTION_CALL: function_name|param1,param2
...
```

This means the script is sending output to the chat instead of keeping it in the console. To fix this:

1. **Use console_agent.py**: The `console_agent.py` script is designed to keep all output in the console

   ```bash
   python console_agent.py "Your query here"
   ```

2. **Run from terminal**: Make sure to run the script from a terminal/command prompt, not directly from a chat interface

3. **Check output redirection**: Ensure no output redirection is happening in the script or in how you're calling it

The console-only mode will show the same information (function calls, results, final answer) but in a controlled way that keeps everything in the terminal.

### Chrome Extension Integration

For a clean, simple response in the Chrome extension without any debugging information, the system now uses `simple_agent.py`. This agent returns only the final answer without any function call details or prefixes.

When you use the Chrome extension:

1. Start the backend server using the instructions above

   - For the best experience, use the simple server: `python3 simple_server.py`
   - Alternatively, just use the restart script: `./restart_server.sh` or `restart_server.bat`

2. Type your query in the extension, for example: "Schedule a meeting with John for tomorrow at 3 PM and send him an email reminder"

3. The response will be clean and user-friendly: "I've scheduled a meeting with John for tomorrow at 3 PM and sent an email reminder"

The server automatically handles your request using the simplified agent to ensure a clean user experience in the extension interface.
