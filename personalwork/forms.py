from datetime import datetime
from django import forms

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label='Enter Password')

class ScheduleForm(forms.Form):
    RECURRING_CHOICES = [
        ('never', 'Never'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]

    start_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    end_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M'],
    )
    event = forms.CharField(max_length=100)
    location = forms.CharField(max_length=100, required=False)
    recurring = forms.ChoiceField(choices=RECURRING_CHOICES, initial='never')

class LoginForm(forms.Form):
    email = forms.CharField(widget=forms.EmailInput, label="Enter E-Mail", required=True)
    password = forms.CharField(widget=forms.PasswordInput, label='Enter Password', required=True)