from datetime import datetime
from django import forms

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label='Enter Password')

class ScheduleForm(forms.Form):
    day = forms.ChoiceField(choices=[
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ])
    start_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p', attrs={'placeholder': '00:00 AM'}),
        input_formats=['%I:%M %p'],
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(format='%I:%M %p', attrs={'placeholder': '00:00 PM'}),
        input_formats=['%I:%M %p'],
    )
    event = forms.CharField(max_length=100)
    location = forms.CharField(max_length=100, required=False)
    recurring = forms.BooleanField(required=False)

