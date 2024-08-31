from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('pull_canvas/', views.pull_canvas_data, name='pull_canvas'),
    path('add_schedule/', views.add_schedule, name='add_schedule'),
]