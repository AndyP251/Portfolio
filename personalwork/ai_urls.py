from django.urls import path
from . import views

urlpatterns = [
    path('', views.ai_interface, name='ai_interface'),
]