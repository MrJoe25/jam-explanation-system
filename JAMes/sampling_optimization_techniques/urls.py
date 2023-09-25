from django.urls import path
from . import views

urlpatterns = [
    path('', views.sampling_optimization_techniques, name='sampling_optimization_techniques'),
]