# Importieren der Django-Funktionen "render" und "redirect"
from django.shortcuts import render, redirect

# Importieren der Django-Messaging-Funktionen und Authentifizierungs-Dekoratoren
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

# Importieren der HttpResponseRedirect-Klasse für Redirects
from django.http import HttpResponseRedirect

# Importieren des Template-Loaders und der "reverse"-Funktion von Django
from django.template import loader
from django.urls import reverse

# Importieren des Logging-Moduls
import logging

# Importieren der Modelle und Formen aus der aktuellen App
from .models import *
from .forms import *

# Importieren von CSV- und IO-Modulen für Dateibearbeitung
import csv, io

# Importieren der Pandas-Bibliothek für Datenanalyse
import pandas as pd

# Importieren von Modellen aus der "ai_selection"-App
from ai_selection.models import *

# Importieren der Cache-Dekoratoren von Django
from django.views.decorators.cache import cache_page

# Ansichtsfunktion für das persönliche Dashboard, erfordert eine Anmeldung
@login_required
def personal_dashboard(request):
    # Abrufen aller CSVFile- und XGModel-Objekte aus der Datenbank
    data = CSVFile.objects.all()
    models = XGModel.objects.all()
    
    # Erstellen eines Dictionarys, das als Kontext für das Template dient
    csv_data = {'id': data, 'models': models}
    
    # Rendern des HTML-Templates mit dem Kontext und Rückgabe als HttpResponse
    return render(request, 'usermanagement/personal_dashboard.html', csv_data)

# Ansichtsfunktion für den Upload von Dateien, erfordert eine Anmeldung
@login_required
def personal_upload(request):
    # Festlegen des Dateipfads für das zu rendernde Template
    template = 'usermanagement/personal_upload.html'
    
    # Überprüfung, ob die HTTP-Anfrage eine POST-Anfrage ist
    if request.method == 'POST':
        # Extrahieren des Benutzernamens und anderer Daten aus dem POST-Request
        superuser = request.user.username
        user = request.POST.get('user')
        file = request.FILES['file']
        
        # Erzeugung eines neuen CSVFile-Objekts in der Datenbank
        CSVFile.objects.create(file=file, superuser=superuser, user=user)
        
        # Überprüfung, ob Dateien im POST-Request vorhanden sind
        if len(request.FILES) != 0:
            # Weiterleitung zur "data_overview"-Seite
            return HttpResponseRedirect('/data_overview/')
        else:
            # Rendern des Upload-Templates, wenn keine Dateien vorhanden sind
            return render(request, template)
    
    # Rendern des Upload-Templates für GET-Anfragen
    return render(request, template)
