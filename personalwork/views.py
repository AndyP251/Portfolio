import datetime
from datetime import timedelta
import uuid
from django.utils.dateformat import DateFormat
import logging
import os
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse
import pytz
import requests
from django.conf import settings
from gradescopeapi.classes.connection import GSConnection
from .forms import PasswordForm, ScheduleForm
from .utils import GRADESCOPE_TASK_FILE, read_json, write_json, CANVAS_TASKS_FILE, SCHEDULE_JSON_FILE

logger = logging.getLogger(__name__)


def delete_event(request):
    if request.method == 'POST':
        event_id = request.POST.get('id')
        logger.info(f"Attempting to delete event with ID: {event_id}")
        schedule = read_json(SCHEDULE_JSON_FILE)
        original_length = len(schedule)
        schedule = [event for event in schedule if event['id'] != event_id]
        if len(schedule) < original_length:
            write_json(SCHEDULE_JSON_FILE, schedule)
            logger.info(f"Event with ID {event_id} deleted successfully")
            return JsonResponse({'status': 'success'})
        else:
            logger.warning(f"Event with ID {event_id} not found in schedule")
            return JsonResponse({'status': 'error', 'message': 'Event not found'}, status=404)
    logger.warning("Invalid request method for delete_event")
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)


def update_event_layer(request):
    logger.info("update_event_layer view called")
    if request.method == 'POST':
        event_id = request.POST.get('id')
        logger.info(f"Received event_id: {event_id}")
        schedule = read_json(SCHEDULE_JSON_FILE)
        for event in schedule:
            if event['id'] == event_id:
                schedule.remove(event)
                schedule.append(event)
                logger.info(f"Event {event_id} moved to the end of the list")
                break
        write_json(SCHEDULE_JSON_FILE, schedule)
        logger.info("Schedule updated successfully")
        return JsonResponse({'status': 'success'})
    logger.warning("Invalid request method for update_event_layer")
    return JsonResponse({'status': 'error'}, status=400)


def add_schedule(request):
    if request.method == 'POST':
        logger.debug('Received POST request with data: %s', request.POST)
        form = ScheduleForm(request.POST)
        if form.is_valid():
            logger.info('Form is valid, processing data...')

            schedule = read_json(SCHEDULE_JSON_FILE)

            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            formatted_start_time = start_time.strftime('%I:%M %p')
            formatted_end_time = end_time.strftime('%I:%M %p')
            new_entry = {
                'id': str(uuid.uuid4()),
                'day': form.cleaned_data['day'],
                'recurring': form.cleaned_data['recurring'],
                'dateSet': datetime.date.today().isoformat(),
                'course': form.cleaned_data['event'],  # Changed from 'course' to 'event'
                'time': f'{formatted_start_time} - {formatted_end_time}',
                'location': form.cleaned_data['location']
            }

            schedule.append(new_entry)
            logger.info('New schedule entry added: %s', new_entry)

            write_json(SCHEDULE_JSON_FILE, schedule)
            logger.info('Schedule data saved successfully.')

            return JsonResponse({'status': 'success', 'id': new_entry['id']})
        else:
            logger.warning('Form is invalid: %s', form.errors)
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        logger.debug('Received non-POST request.')
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    

def dashboard(request):
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] == settings.USER_PASSWORD:
                request.session['authenticated'] = True
                return redirect('dashboard')  # Redirect to the same view
            else:
                form.add_error('password', 'Incorrect password')
    else:
        form = PasswordForm()

    if not request.session.get('authenticated'):
        return render(request, 'password_protect.html', {'form': form})

    selected_source = request.GET.get('data_source', 'sum')

    todos = read_json(CANVAS_TASKS_FILE) + read_json(GRADESCOPE_TASK_FILE)
    
    if selected_source:
        todos = [todo for todo in todos if todo['source'] == selected_source or selected_source == 'sum']
        

    schedules = read_json(SCHEDULE_JSON_FILE)

    # Convert date strings to datetime objects and handle missing dates
    for todo in todos:
        if 'due_date' in todo and todo['due_date']:
            if todo['source'] == 'canvas':
                todo['due_date'] = datetime.datetime.strptime(todo['due_date'], '%Y-%m-%dT%H:%M:%SZ')
            elif todo['source'] == 'gradescope':
                todo['due_date'] = datetime.datetime.strptime(todo['due_date'], '%Y-%m-%d %H:%M:%S%z')
        else:
            todo['due_date'] = None

    # Generate time slots for the schedule
    time_slots = []
    for hour in range(0, 24):
        time_slots.append(f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}")
        time_slots.append(f"{hour % 12 or 12}:30 {'AM' if hour < 12 else 'PM'}")

    # Get the current day of the week
    current_day = datetime.datetime.now().strftime('%A')
    #Get today's schedules:
    todays_schedule: list = []
    for event in schedules:
        if event.get("day", None) == current_day:
            todays_schedule.append(event)

    return render(request, 'dashboard.html', {
        'todos': todos,
        'schedules': todays_schedule,
        'time_slots': time_slots,
        'current_date': datetime.date.today().isoformat(),
    })


def pull_combined_data(request):
    canvas_response = pull_canvas_data(request)
    gradescope_response = pull_gradescope_data(request)

    if canvas_response.status_code == 200 and gradescope_response.status_code == 200:
        return JsonResponse({'status': 'success', 'message': 'Data pulled successfully from both sources.'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Failed to pull data from one or both sources.'})

# TODO: Implement cengage mindtap, matlabs, MAA workweb


def pull_gradescope_data(request):
    connection = GSConnection()
    connection.login(settings.GRADESCOPE_USER_KEY, settings.GRADESCOPE_USER_SECRET)
    courses = connection.account.get_courses()
    current_date = datetime.datetime.now(pytz.UTC)
    cutoff_date = current_date - timedelta(days=90)  # Assuming a semester is about 4 months

    def safe_compare_dates(date1, date2):
        if date1 is None or date2 is None:
            return False
        if date1.tzinfo is None:
            date1 = pytz.UTC.localize(date1)
        if date2.tzinfo is None:
            date2 = pytz.UTC.localize(date2)
        return date1 > date2

    collected_data = []

    for course_id in courses["student"]:
        try:
            assignments = connection.account.get_assignments(course_id)
            for assignment in assignments:
                try:
                    if safe_compare_dates(assignment.due_date, cutoff_date):
                        print(f"- {assignment.name}: Due {assignment.due_date}, Status: {assignment.submissions_status}")
                        curr_assignment = {
                            "source": "gradescope",
                            "course": course_id,
                            "courseName": courses["student"][course_id].name,
                            "title": assignment.name,
                            "due_date": str(assignment.due_date),
                            "submitted": assignment.submissions_status == "Submitted",
                            "html_link": f"https://www.gradescope.com/courses/{course_id}/assignments/{assignment.assignment_id}"
                        }
                        collected_data.append(curr_assignment)
                except AttributeError as e:
                    print(f"  Error processing assignment: {e}")
        except Exception as e:
            print(f"Error fetching assignments for course {course_id}: {e}")
    
    write_json(GRADESCOPE_TASK_FILE, collected_data)
    
    return JsonResponse({'status': 'success', 'message': 'Gradescope data pulled and saved successfully.'})

def pull_canvas_data(request):
    access_token = settings.CANVAS_API_TOKEN
    canvas_domain = settings.CANVAS_DOMAIN
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json+canvas-string-ids'
    }
    courses = []
    url = f'https://{canvas_domain}/api/v1/courses'
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return JsonResponse({'status': 'error', 'message': 'Failed to fetch courses'}, status=400)
        courses.extend(response.json())
        if 'next' in response.links:
            url = response.links['next']['url']
        else:
            url = None
    todos = []
    schedules = []
    cutoff_date = datetime.datetime.strptime("2024-01-01T10:00:00Z", "%Y-%m-%dT%H:%M:%SZ")

    for course in courses:
        course_created_at = datetime.datetime.strptime(course["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        if course_created_at < cutoff_date:
            continue
        assignments_url = f'https://{canvas_domain}/api/v1/courses/{course["id"]}/assignments'
        assignments_response = requests.get(assignments_url, headers=headers)
        
        if assignments_response.status_code == 200:
            assignments = assignments_response.json()
            for assignment in assignments:

                course_code = course["course_code"]
                course_parts = course_code.split('_')
                if len(course_parts) >= 2:
                    formatted_course_code = course_parts[0] + ' ' + course_parts[1].split('-')[0]
                else:
                    formatted_course_code = course_code
                todos.append({
                    "source": "canvas",
                    'course': course["id"],
                    'courseName': formatted_course_code,
                    'title': assignment['name'],
                    'due_date': assignment['due_at'],
                    'submitted': assignment['has_submitted_submissions'],
                    'html_link': assignment['html_url']
                })
        schedule_url = f'https://{canvas_domain}/api/v1/courses/{course["id"]}/calendar_events'
        schedule_response = requests.get(schedule_url, headers=headers)
        if schedule_response.status_code == 200:
            events = schedule_response.json()
            for event in events:
                schedules.append({
                    'title': event['title'],
                    'start_time': event['start_at'],
                    'end_time': event['end_at']
                })
    write_json(CANVAS_TASKS_FILE, todos)
    write_json(SCHEDULE_JSON_FILE, schedules)
    
    return JsonResponse({'status': 'success', 'message': 'Canvas data pulled and saved successfully.'})


def ai_interface(request):
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        api_key = settings.PERPLEXITY_API_TOKEN
        response = call_perplexity_api(prompt, api_key)
        return render(request, 'ai_interface.html', {'response': response})
    return render(request, 'ai_interface.html')

def call_perplexity_api(prompt, api_key):
    url = 'https://api.perplexity.ai/chat/completions'
    headers = {
        'accept': 'application/json',
        'content-type': 'application/json',
        'authorization': f'Bearer {api_key}'
    }
    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        result = response.json()
        return result['choices'][0]['message']['content']
    except requests.RequestException as e:
        return f"An error occurred: {str(e)}\nStatus code: {e.response.status_code if e.response else 'N/A'}\nResponse text: {e.response.text if e.response else 'N/A'}"
    








