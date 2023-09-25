from django.urls import path  # Importiert die 'path' Funktion aus Django's URL-Modul
from . import views  # Importiert alle Views aus dem aktuellen Verzeichnis

urlpatterns = [  # Erstellt eine Liste von URL-Mustern für die Anwendung
    path('', views.home, name='users-home'),  # Verbindet die Root-URL ('') mit der 'home' Funktion im 'views' Modul. Gibt dieser URL das Namen 'users-home'
    path('about/', views.about, name='users-about'),  # Verbindet die 'about/' URL mit der 'about' Funktion im 'views' Modul. Gibt dieser URL den Namen 'users-about'
]
