# Importieren der "render"-Funktion aus Django
from django.shortcuts import render

# Importieren aller Modelle aus dem "group_representation"- und dem aktuellen App-Modul
from group_representation.models import *
from .models import *

# Verschiedene Bibliotheken und Module für CSV-Verarbeitung, Dateimanipulation und Datensatzverarbeitung
import csv, io, os
from tablib import Dataset

# Importieren der Pandas-Bibliothek für Datenmanipulation und -analyse
import pandas as pd

# Importieren von ContentFile, das zum Speichern von Dateien im Django-Modell benötigt wird
from django.core.files.base import ContentFile

# Importieren der "reverse"-Funktion für URL-Umkehrung aus Django
from django.urls import reverse

# Definieren einer Django-Ansichtsfunktion für "sampling_optimization_techniques"
def sampling_optimization_techniques(request):
    # Abrufen von Query-Parametern aus der URL
    file = request.GET.get('file')  # Dateiname
    superuser = request.user.username  # Benutzername des aktuellen Benutzers
    current_user = request.GET.get('current_user')  # aktueller Benutzername aus der URL
    number_of_groups = int(request.GET.get('number_of_groups'))  # Anzahl der Gruppen als Ganzzahl
    
    # Abrufen der letzten besuchten Seite aus den Metadaten des HTTP-Requests
    last_page = request.META.get('HTTP_REFERER', None)
    
    # Erstellen eines Dictionarys für die Kontextdaten der Vorlage
    dict = {'file':file, 'current_user':current_user, 'number_of_groups':number_of_groups, 'last_page':last_page}
    
    # Rendern der HTML-Vorlage und Rückgabe als HttpResponse
    return render(request, 'sampling_optimization_techniques.html', dict)
