from django import forms

class PasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, label='Enter Password')