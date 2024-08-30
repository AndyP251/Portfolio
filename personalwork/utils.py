import json

# Define file paths for JSON storage
TODO_JSON_FILE = 'todos.json'
SCHEDULE_JSON_FILE = 'schedule.json'

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