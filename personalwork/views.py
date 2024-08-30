import datetime
import os
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from django.conf import settings
from .forms import PasswordForm
from .utils import read_json, write_json, TODO_JSON_FILE, SCHEDULE_JSON_FILE


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




    schedule = {
    'Monday': [
        {'course': 'CS 3710', 'time': '10:00 AM - 10:50 AM', 'location': 'Olsson Hall 120'},
        {'course': 'COMM 3230', 'time': '12:30 PM - 1:45 PM', 'location': 'Robertson Hall 225'},
        {'course': 'RELC 1220', 'time': '2:00 PM - 2:50 PM', 'location': 'Wilson Hall 402'},
    ],
    'Tuesday': [
        {'course': 'CS 3240', 'time': '9:30 AM - 10:45 AM', 'location': 'Rice Hall 130'},
        {'course': 'CS 3100', 'time': '11:00 AM - 11:50 AM', 'location': 'Rice Hall 130'},
        {'course': 'SPAN 2020', 'time': '3:30 PM - 4:45 PM', 'location': 'New Cabell Hall 364'},
    ],
    'Wednesday': [
        {'course': 'CS 3710', 'time': '10:00 AM - 10:50 AM', 'location': 'Olsson Hall 120'},
        {'course': 'COMM 3230', 'time': '12:30 PM - 1:45 PM', 'location': 'Robertson Hall 225'},
        {'course': 'RELC 1220', 'time': '2:00 PM - 2:50 PM', 'location': 'Wilson Hall 402'},
    ],
    'Thursday': [
        {'course': 'CS 3240', 'time': '9:30 AM - 10:45 AM', 'location': 'Rice Hall 130'},
        {'course': 'CS 3710', 'time': '11:00 AM - 12:15 AM', 'location': 'Olsson Hall 120'},
        {'course': 'SPAN 2020', 'time': '3:30 PM - 4:45 PM', 'location': 'New Cabell Hall 364'},
    ],
    'Friday': [
        {'course': 'CS 3710', 'time': '10:00 AM - 10:50 AM', 'location': 'Olsson Hall 120'},
        ]
    }
    
    todos = read_json(TODO_JSON_FILE)
    schedules = read_json(SCHEDULE_JSON_FILE)

    # Convert date strings to datetime objects and handle missing dates
    for todo in todos:
        if 'due_date' in todo and todo['due_date']:
            todo['due_date'] = datetime.datetime.strptime(todo['due_date'], '%Y-%m-%dT%H:%M:%SZ')
        else:
            todo['due_date'] = None

    # Generate time slots for the schedule
    time_slots = []
    for hour in range(0, 24):
        time_slots.append(f"{hour % 12 or 12}:00 {'AM' if hour < 12 else 'PM'}")
        time_slots.append(f"{hour % 12 or 12}:30 {'AM' if hour < 12 else 'PM'}")

    # Get the current day of the week
    current_day = datetime.datetime.now().strftime('%A')
    daily_schedule = schedule.get(current_day, [])

    return render(request, 'dashboard.html', {
        'todos': todos,
        'schedules': schedules,
        'daily_schedule': daily_schedule,
        'time_slots': time_slots
    })
def pull_canvas_data(request):
    # Get the access token from your environment variables or settings
    access_token = settings.CANVAS_API_TOKEN
    # Your Canvas domain
    canvas_domain = settings.CANVAS_DOMAIN
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json+canvas-string-ids'
    }
    
    # Fetch courses
    courses_url = f'https://{canvas_domain}/api/v1/courses'
    courses_response = requests.get(courses_url, headers=headers)
    
    if courses_response.status_code != 200:
        return JsonResponse({'status': 'error', 'message': 'Failed to fetch courses'}, status=400)
    
    courses = courses_response.json()
    
    todos = []
    schedules = []
    
    for course in courses:

        # Fetch assignments for each course
        if course["id"] not in ["116443", "117250", "111463", "111439"]:
            continue #cyber, relc, comm
        assignments_url = f'https://{canvas_domain}/api/v1/courses/{course["id"]}/assignments'
        assignments_response = requests.get(assignments_url, headers=headers)
        
        if assignments_response.status_code == 200:
            assignments = assignments_response.json()
            for assignment in assignments:
                todos.append({
                    'course': course["name"],
                    'title': assignment['name'],
                    'due_date': assignment['due_at']
                })
        
        # Fetch course schedule (you might need to adjust this based on available endpoints)
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
    
    # Save to JSON files (you can adjust this based on your needs)
    write_json(TODO_JSON_FILE, todos)
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
    








