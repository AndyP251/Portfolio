import json

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

def combine_existing_jsons(file_paths: list, output_file: str):
    collection : list[dict] = []
    for file_path in file_paths:
        curr_data = read_json(file_path=file_path)
        curr_data.append(collection)
    return collection