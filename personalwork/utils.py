from datetime import time, timezone
from django.contrib.auth.hashers import make_password, check_password
from .models import S3Utils
from uuid import uuid4
import datetime
import json
import logging
import pytz

logger = logging.getLogger(__name__)

# JSON TESTING FILE PATH's
CANVAS_TASKS_FILE = 'canvasTasks.json'
GRADESCOPE_TASK_FILE = 'gradescopeTasks.json'
COLLECTIVE_TASK_FILE = 'collectiveTasks.json'
SCHEDULE_JSON_FILE = 'Schedule.json'

# HOLISTIC DATA FILE PATH's
USERS_FILE = 'users.json'

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
        start_at_str = event["start_at"].rsplit('+', 1)[0].rstrip('Z')
        start_at = datetime.datetime.strptime(start_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        end_at_str = event["end_at"].rsplit('+', 1)[0].rstrip('Z')
        end_at = datetime.datetime.strptime(end_at_str, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        if start_at.date() <= current_date <= end_at.date():
            # If the event starts on a previous day but ends today or later, reset start time to 12 AM
            if start_at.date() < current_date:
                start_at = datetime.datetime.combine(current_date, time(0, 0))
            
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
        dt = datetime.datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%S")
        
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

def convert_schedule_to_datetime_objects(schedule):
    for event in schedule:
        start_time = datetime.datetime.strptime(event['start_at'], '%Y-%m-%dT%H:%M:%S')
        end_time = datetime.datetime.strptime(event['end_at'], '%Y-%m-%dT%H:%M:%S')
        # Calculate top position (in pixels)
        minutes_since_midnight = start_time.hour * 60 + start_time.minute
        event['top_position'] = (minutes_since_midnight // 30) * 25

        # Calculate height (in pixels)
        duration_minutes = (end_time - start_time).total_seconds() / 60
        event['height'] = (duration_minutes / 30) * 25

        event['start_at'] = start_time
        event['end_at'] = end_time
    return schedule

def convert_todos_to_datetime_objects(todos):
    for todo in todos:
        if 'due_date' in todo and todo['due_date']:
            if todo['source'] == 'canvas':
                todo['due_date'] = datetime.datetime.strptime(todo['due_date'], '%Y-%m-%dT%H:%M:%SZ')
            elif todo['source'] == 'gradescope':
                todo['due_date'] = datetime.datetime.strptime(todo['due_date'], '%Y-%m-%d %H:%M:%S%z')
        else:
            todo['due_date'] = None
    return todos

def generate_timeslots_for_schedule():
    return [datetime.time(hour=h, minute=m).strftime('%H:%M') for h in range(24) for m in (0, 30)]


#Account Utils

def is_current_user(username):
    user_data = S3Utils().read_json_from_s3(USERS_FILE)
    if isinstance(user_data, list):
        for user in user_data:
            if isinstance(user, dict) and user.get('username') == username:
                return True
    elif user_data[username]:
        return True
    return False

def passwords_match(pass1, pass2):
    if pass1 == pass2:
        return True
    return False

def create_user(user, password):
    try:
        user_data = S3Utils().read_json_from_s3(USERS_FILE)
        if user_data is None:
            user_data = []
            
        hashed_password = make_password(password)
        new_user = {
            'id': str(uuid4()),
            'username': user,
            'hash': hashed_password
        }
        user_data.append(new_user)
        s3_utils = S3Utils()
        success = s3_utils.upload_data_to_s3(user_data, USERS_FILE)
        s3_utils.initialize_user_directory(new_user['id'])
        
        if not success:
            print("Failed to upload user data to S3")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error in create_user: {e}")
        return False
    
def verify_user(username, password):
    try:
        user_data = S3Utils().read_json_from_s3(USERS_FILE)
        
        # Find the user in the list
        for user in user_data:
            if user['username'] == username:
                # Use Django's check_password to verify the hash
                return check_password(password, user['hash'])
        
        return False
        
    except Exception as e:
        print(f"Error in verify_user: {e}")
        return False