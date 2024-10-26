from datetime import datetime, time, timezone
import json
import logging
import pytz

logger = logging.getLogger(__name__)

# Define file paths for JSON storage
CANVAS_TASKS_FILE = 'canvasTasks.json'
GRADESCOPE_TASK_FILE = 'gradescopeTasks.json'
COLLECTIVE_TASK_FILE = 'collectiveTasks.json'
SCHEDULE_JSON_FILE = 'Schedule.json'

# Function to read from JSON files
def read_json(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Return empty list on error

# Function to write to JSON files
def write_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def append_json(file_path, data):
    try:
        with open(file_path, 'r') as file:
            existing_data = json.load(file)
    except FileNotFoundError:
        existing_data = []

    existing_data.append(data)

    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=4)

def combine_existing_jsons(file_paths: list, output_file: str):
    collection : list[dict] = []
    for file_path in file_paths:
        curr_data = read_json(file_path=file_path)
        curr_data.append(collection)
    return collection

def get_todays_schedule(schedules):
    todays_schedule = []
    current_date = datetime.now().date()

    for event in schedules:
        start_at_str = event["start_at"].rsplit('+', 1)[0].rstrip('Z')
        start_at = datetime.strptime(start_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        end_at_str = event["end_at"].rsplit('+', 1)[0].rstrip('Z')
        end_at = datetime.strptime(end_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        if start_at.date() <= current_date <= end_at.date():
            # If the event starts on a previous day but ends today or later, reset start time to 12 AM
            if start_at.date() < current_date:
                start_at = datetime.combine(current_date, time(0, 0))
            
            todays_schedule.append({**event, "start_at": start_at.isoformat(), "end_at": end_at.isoformat()})

    timezone_updated_schedules = []
    for event in todays_schedule:
        timezone_updated_schedules.append(update_event_timezones(event))
        # timezone_updated_schedules.append(event)
    logging.warning(f"\n\n\n\n time zone updated fields = {timezone_updated_schedules}")
    return timezone_updated_schedules


def update_event_timezones(event):
    def parse_datetime(dt_string):
        dt_string = dt_string.split('+')[0].rstrip('Z')
    
        # Parse the datetime string without timezone information
        dt = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")
        
        # Set the timezone to UTC
        dt = dt.replace(tzinfo=timezone.utc)
        
        return dt

    # Parse start_at and end_at
    start_at = parse_datetime(event["start_at"])
    end_at = parse_datetime(event["end_at"])

    # Convert to Eastern Time
    eastern_timezone = pytz.timezone("US/Eastern")
    start_at = start_at.astimezone(eastern_timezone)
    end_at = end_at.astimezone(eastern_timezone)

    # Update the event dictionary with the new timestamps
    event["start_at"] = start_at.strftime("%Y-%m-%dT%H:%M:%S")
    event["end_at"] = end_at.strftime("%Y-%m-%dT%H:%M:%S")

    return event