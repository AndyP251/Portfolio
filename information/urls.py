from django.urls import path

from . import views

urlpatterns = [
    path("", views.getGeneralInformationTemplate, name='mainHL'),
    path("resume/", views.getResumeTemplate, name='resumeHL'),
    path("story/", views.getStory, name='storyHL'),
    path("projects/", views.getProjects, name='projectsHL'),
    path("contactForm/", views.getContactForm, name='contact')
    
]