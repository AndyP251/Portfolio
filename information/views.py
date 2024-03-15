from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("//Information Index\\")
def getGeneralInformationTemplate(request):
    return render(request, 'generalInformation.html')
def getResumeTemplate(request):
    return render(request, 'resume.html')
def getStory(request):
    return render(request, 'mystory.html')
def getProjects(request):
    return render(request, 'projects.html')
def getContactForm(request):
    return render(request, 'contact.html')


