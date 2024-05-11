from django.shortcuts import render, redirect
from django.http import HttpResponse

#mail form imports
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import reverse
from django.urls import reverse_lazy
from django.views.generic import TemplateView, FormView
from .forms import ContactForm


def getGeneralInformationTemplate(request):
    return render(request, 'generalInformation.html')
def getResumeTemplate(request):
    return render(request, 'resume.html')
def getStory(request):
    return render(request, 'mystory.html')
def getProjects(request):
    return render(request, 'projects.html')

class ContactView(FormView):
    form_class = ContactForm
    template_name = "contact.html"
    success_url = reverse_lazy('success')

    def get_success_url(self):
        return reverse("contact")

    def form_valid(self, form):
        email = form.cleaned_data.get("email")
        subject = form.cleaned_data.get("Subject")
        message = form.cleaned_data.get("message")

        full_message = f"""
            Received message below from {email}, {subject}
            ________________________


            {message}
            """
        send_mail(
            subject="Received contact form submission",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.NOTIFY_EMAIL],
        )
        
        return super(ContactView, self).form_valid(form)

class SuccessView(TemplateView):
    template_name = "success.html"