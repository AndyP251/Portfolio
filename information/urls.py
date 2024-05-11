from django.urls import path

from . import views
from .views import SuccessView, ContactView

urlpatterns = [
    path("", views.getGeneralInformationTemplate, name='mainHL'),
    path("resume/", views.getResumeTemplate, name='resumeHL'),
    path("story/", views.getStory, name='storyHL'),
    path("projects/", views.getProjects, name='projectsHL'),
    # path("contactForm/", views.getContactForm, name='contact')
    path("contact/", ContactView.as_view(), name="contact"),
    path("success/", SuccessView.as_view(), name="success")
    
]