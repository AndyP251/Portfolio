import datetime
from datetime import timedelta
import uuid
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
import pytz
import requests
from django.conf import settings
from gradescopeapi.classes.connection import GSConnection
from .forms import ScheduleForm, LoginForm, SignUpForm
from .utils import (
    get_todays_schedule,
    convert_schedule_to_datetime_objects,
    convert_todos_to_datetime_objects,
    generate_timeslots_for_schedule,
    read_json, 
    write_json, 
    append_json, 
    GRADESCOPE_TASK_FILE, 
    CANVAS_TASKS_FILE, 
    SCHEDULE_JSON_FILE,
    USERS_FILE)

from .models import S3Utils

logger = logging.getLogger(__name__)

def dashboard(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password'] == settings.USER_PASSWORD:
                request.session['authenticated'] = True
                return redirect('dashboard')  # Redirect to the same view
            else:
                form.add_error('password', 'Incorrect password')
    else:
        form = LoginForm()

    if not request.session.get('authenticated'):
        return render(request, 'password_protect.html', {'form': form})

    selected_source = request.GET.get('data_source', 'sum')

    # implement data base user query here for data
    users_data = S3Utils().read_json_from_s3(USERS_FILE)

    todos = read_json(CANVAS_TASKS_FILE) + read_json(GRADESCOPE_TASK_FILE)
    
    if selected_source:
        todos = [todo for todo in todos if todo['source'] == selected_source or selected_source == 'sum']

    # Convert date strings to datetime objects and handle missing dates
    todos = convert_todos_to_datetime_objects(todos)
    time_slots = generate_timeslots_for_schedule()
    
    schedules = read_json(SCHEDULE_JSON_FILE)

    todays_schedule: list = get_todays_schedule(schedules)
    todays_schedule = convert_schedule_to_datetime_objects(todays_schedule)

    return render(request, 'dashboard.html', {
        'todos': todos,
        'schedules': todays_schedule,
        'time_slots': time_slots,
        'current_date': datetime.date.today().isoformat(),
    })


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            print("\n\nREDIRECTING TO DASHBOARD\n\n")
            return redirect('dashboard') 
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


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
            start_at = form.cleaned_data['start_at'].strftime("%Y-%m-%dT%H:%M:%S")
            end_at = form.cleaned_data['end_at'].strftime("%Y-%m-%dT%H:%M:%S")
            event = form.cleaned_data['event']
            location = form.cleaned_data['location']
            recurring = form.cleaned_data['recurring']

            new_schedule = {
                'id': str(uuid.uuid4()),
                'title': event,
                'start_at': start_at,
                'end_at': end_at,
                'location_name': location,
                'recurring': recurring
            }

            schedules = read_json(SCHEDULE_JSON_FILE)
            schedules.append(new_schedule)
            write_json(SCHEDULE_JSON_FILE, schedules)

            logger.info('Schedule data saved successfully.')

            return JsonResponse({'status': 'success', 'id': new_schedule['id']})
        else:
            logger.warning('Form is invalid: %s', form.errors)
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        logger.debug('Received non-POST request.')
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    


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
    write_json(CANVAS_TASKS_FILE, todos)    
    try:
        pull_canvas_calendar_events(canvas_domain=canvas_domain,
                                    headers=headers)
    except:
        print(f"Exception occured when pulling Canvas calendar events")
    return JsonResponse({'status': 'success', 'message': 'Canvas data pulled and saved successfully.'})

def pull_canvas_calendar_events(canvas_domain, headers):
    url = f'https://{canvas_domain}/api/v1/calendar_events'
    params = {
        'type': 'event',
        'per_page': 100,  
        'all_events': 'true'
    }
    all_events = []
    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise an exception for bad responses
        
        events = response.json()
        all_events.extend(events)
        
        # Check for pagination
        url = response.links.get('next', {}).get('url')
        params = {}  

    event_data = []
    for event in all_events:
        event_info = {
            'id': event.get('id'),
            'title': event.get('title'),
            'start_at': event.get('start_at'),
            'end_at': event.get('end_at'),
            'description': event.get('description'),
            'location_name': event.get('location_name'),
            'location_address': event.get('location_address'),
            'context_code': event.get('context_code'),
            'workflow_state': event.get('workflow_state'),
            'html_url': event.get('html_url'),
            'created_at': event.get('created_at'),
            'updated_at': event.get('updated_at'),
            'all_day': event.get('all_day'),
            'all_day_date': event.get('all_day_date'),
            'important_dates': event.get('important_dates'),
            'series_uuid': event.get('series_uuid'),
            'rrule': event.get('rrule'),
            'blackout_date': event.get('blackout_date')
        }
        event_data.append(event_info)
    print(f"Event Data: {event_data}")
    write_json(SCHEDULE_JSON_FILE, event_data)

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
    










