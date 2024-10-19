import datetime
import json

import pytz

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
    current_date = datetime.datetime.now().date()

    for event in schedules:
        start_at = datetime.datetime.strptime(event["start_at"], "%Y-%m-%dT%H:%M:%SZ")
        end_at = datetime.datetime.strptime(event["end_at"], "%Y-%m-%dT%H:%M:%SZ")
        if start_at.date() <= current_date <= end_at.date():
            # If the event starts on a previous day but ends today or later, reset start time to 12 AM
            if start_at.date() < current_date:
                start_at = datetime.datetime.combine(current_date, datetime.time(0, 0))
            
            todays_schedule.append({**event, "start_at": start_at.isoformat()})

    timezone_updated_schedules = []
    for event in todays_schedule:
        timezone_updated_schedules.append(update_event_timezones(event))

    return timezone_updated_schedules


def update_event_timezones(event):
    start_at = datetime.datetime.fromisoformat(event["start_at"])
    end_at = datetime.datetime.fromisoformat(event["end_at"])

    # Convert to Eastern Time
    eastern_timezone = pytz.timezone("US/Eastern")
    start_at = start_at.astimezone(eastern_timezone)
    end_at = end_at.astimezone(eastern_timezone)

    # Update the event dictionary with the new timestamps
    event["start_at"] = start_at.isoformat()
    event["end_at"] = end_at.isoformat()

    return event
