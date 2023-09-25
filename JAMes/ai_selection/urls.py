from django.urls import path  # Importiert die 'path' Funktion aus Django's URL-Modul
from . import views  # Importiert alle View-Funktionen aus dem 'views' Modul des aktuellen Pakets

urlpatterns = [  # Definiert eine Liste von URL-Mustern für diese Django-App
    path('', views.ai_selection, name='ai_selection'),  # Root-URL, die zur 'ai_selection' View-Funktion weiterleitet
    path('group_stats/', views.group_stats, name='group_stats'),  # URL-Muster, das zur 'group_stats' View-Funktion weiterleitet
    path('xg_param/', views.xg_param, name='xg_param'),  # URL-Muster, das zur 'xg_param' View-Funktion weiterleitet
]
