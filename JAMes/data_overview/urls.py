from django.urls import path  # Importiere path aus Django
from . import views  # Importiere views aus dem aktuellen Verzeichnis

# Definiere URL-Muster
urlpatterns = [
    path('', views.data_overview, name='data_overview'),  # Root-URL, führt zur data_overview-Funktion in views
    path('results/', views.results, name='results'),  # URL für Ergebnisse, führt zur results-Funktion in views
    path('results_csv/', views.results_csv, name='results_csv')  # URL für CSV-Ergebnisse, führt zur results_csv-Funktion in views
]
