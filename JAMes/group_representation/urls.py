from django.urls import path  # Importiert den path-Helfer von Django
from . import views  # Importiert alle Ansichten (views) aus dem aktuellen Verzeichnis

# Definiert eine Liste von URL-Routen und zugehörigen Ansichten
urlpatterns = [
    path('', views.splitting, name='splitting'),  # Verbindet die Root-URL ('') mit der Ansicht 'splitting' und gibt ihr den Namen 'splitting'
    path('representation/', views.group_representation, name='group_representation')  # Verbindet die URL 'representation/' mit der Ansicht 'group_representation' und gibt ihr den Namen 'group_representation'
]
