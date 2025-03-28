import datetime
import json
import os
import re

# Path to store our mock data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
CALENDAR_FILE = os.path.join(DATA_DIR, 'calendar.json')

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize the calendar file if it doesn't exist
if not os.path.exists(CALENDAR_FILE):
    with open(CALENDAR_FILE, 'w') as f:
        json.dump([], f)

def parse_time(time_str):
    """Parse a time string into a datetime object."""
    try:
        # Handle "tomorrow" or "today" keywords
        today = datetime.datetime.now()
        if "tomorrow" in time_str.lower():
            date = today + datetime.timedelta(days=1)
            time_str = time_str.lower().replace("tomorrow", "").strip()
        elif "today" in time_str.lower():
            date = today
            time_str = time_str.lower().replace("today", "").strip()
        else:
            # Default to today if only time is specified
            date = today
        
        # Normalize the time string - insert space between number and AM/PM if missing
        time_str = time_str.strip()
        
        # Regular expression to match patterns like "3pm", "3PM", "3p.m.", "3 pm", etc.
        am_pm_pattern = re.compile(r'(\d+)([aApP]\.?[mM]\.?)')
        match = am_pm_pattern.search(time_str)
        
        if match:
            # Extract the hour and AM/PM part
            hour = match.group(1)
            am_pm = match.group(2).upper().replace('.', '')
            
            # Normalize to "3 PM" format
            if am_pm.startswith('A'):
                am_pm = 'AM'
            else:
                am_pm = 'PM'
                
            time_str = f"{hour} {am_pm}"
            time_format = "%I %p"
        elif ":" in time_str:
            # Handle 24-hour format like "15:00"
            time_format = "%H:%M"
        else:
            # Default to 12-hour format
            time_format = "%I %p"
        
        # Parse the time
        time_obj = datetime.datetime.strptime(time_str, time_format).time()
        return datetime.datetime.combine(date.date(), time_obj)
    except Exception as e:
        print(f"Error parsing time: {e}")
        print(f"Problematic time string: '{time_str}'")
        return None

def check_calendar_availability(time_str):
    """Check if a given time slot is available in the calendar."""
    try:
        # Parse the time string
        meeting_time = parse_time(time_str)
        if not meeting_time:
            return {"available": False, "error": "Could not parse time format"}
        
        # Load existing meetings
        with open(CALENDAR_FILE, 'r') as f:
            meetings = json.load(f)
        
        # Check for conflicts (simple 1-hour slot check)
        meeting_end = meeting_time + datetime.timedelta(hours=1)
        
        for meeting in meetings:
            start_time = datetime.datetime.fromisoformat(meeting['start_time'])
            end_time = datetime.datetime.fromisoformat(meeting['end_time'])
            
            # Check for overlap
            if (meeting_time < end_time and meeting_end > start_time):
                return {
                    "available": False,
                    "conflict": meeting['title'],
                    "conflict_time": meeting['start_time']
                }
        
        return {"available": True, "time": meeting_time.isoformat()}
    except Exception as e:
        return {"available": False, "error": str(e)}

def schedule_meeting(person, time_str, title=None):
    """Schedule a meeting with the given person at the specified time."""
    try:
        # Check availability first
        availability = check_calendar_availability(time_str)
        if not availability.get("available", False):
            return {"success": False, "reason": "Time slot not available", "details": availability}
        
        meeting_time = parse_time(time_str)
        meeting_end = meeting_time + datetime.timedelta(hours=1)
        
        # Create a meeting title if not provided
        if not title:
            title = f"Meeting with {person}"
        
        # Load existing meetings
        with open(CALENDAR_FILE, 'r') as f:
            meetings = json.load(f)
        
        # Add the new meeting
        new_meeting = {
            "id": len(meetings) + 1,
            "title": title,
            "attendee": person,
            "start_time": meeting_time.isoformat(),
            "end_time": meeting_end.isoformat(),
            "created_at": datetime.datetime.now().isoformat()
        }
        
        meetings.append(new_meeting)
        
        # Save the updated meetings
        with open(CALENDAR_FILE, 'w') as f:
            json.dump(meetings, f, indent=2)
        
        return {
            "success": True,
            "meeting": {
                "title": title,
                "with": person,
                "time": meeting_time.isoformat()
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_upcoming_meetings(limit=5):
    """Get a list of upcoming meetings."""
    try:
        # Load existing meetings
        with open(CALENDAR_FILE, 'r') as f:
            meetings = json.load(f)
        
        # Sort by start time
        meetings.sort(key=lambda x: x['start_time'])
        
        # Filter to only include future meetings
        now = datetime.datetime.now()
        future_meetings = [
            meeting for meeting in meetings 
            if datetime.datetime.fromisoformat(meeting['start_time']) > now
        ]
        
        return {"meetings": future_meetings[:limit]}
    except Exception as e:
        return {"error": str(e)} 