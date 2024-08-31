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
    start_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'))
    end_time = forms.TimeField(widget=forms.TimeInput(format='%H:%M'))
    course = forms.CharField(max_length=100)
    location = forms.CharField(max_length=100, required=False)