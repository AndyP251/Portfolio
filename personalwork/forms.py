from datetime import datetime
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

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