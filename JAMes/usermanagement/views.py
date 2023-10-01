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

import os

from ai_selection.models import FinalData, XGModel
from ai_explainability.models import Report
from group_representation.models import GroupSplit
from group_preprocessing.models import Group
from feature_selection.models import Cleaned_File, Featureselection, Feature_Table
from usermanagement.models import CSVFile

import logging

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

@login_required
def delete_csv(request, id):
    try:
        csv_file = CSVFile.objects.get(id=id)
        file_path = f'media/{csv_file.file}'
        if os.path.exists(file_path):
            os.remove(file_path)
        csv_file.delete()
    except Exception as e:
        messages.warning(request, f'An error occurred while deleting the CSV file: {e}')
    return redirect('personal_dashboard')

@login_required
def delete_model(request, id):
    try:
        model = XGModel.objects.get(id=id)
        file_path = f'media/xg_model/{model.file_name}.pkl'
        
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            messages.warning(request, 'The specified model file does not exist.')
            
        model.delete()
        messages.success(request, 'Model and corresponding file have been deleted.')
        
    except Exception as e:
        messages.warning(request, f'An error occurred while deleting the model: {e}')
        
    return redirect('personal_dashboard')

@login_required
def clear_all(request):
    logger = logging.getLogger(__name__)
    try:
        # List to keep track of opened file handles
        file_handles = []
        
        # Open and close all files in the media folder and its subfolders
        for root, dirs, files in os.walk('media/'):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            file_handles.append(f)
                    except Exception as e:
                        messages.warning(request, f'An error occurred while handling {file_path}: {e}')
                        
        # Close all opened file handles
        for f in file_handles:
            f.close()
            
        # Delete all files in the media folder and its subfolders
        for root, dirs, files in os.walk('media/'):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        # Delete all records from your models
        FinalData.objects.all().delete()
        XGModel.objects.all().delete()
        Report.objects.all().delete()
        GroupSplit.objects.all().delete()
        Group.objects.all().delete()
        Cleaned_File.objects.all().delete()
        Featureselection.objects.all().delete()
        Feature_Table.objects.all().delete()
        CSVFile.objects.all().delete()

        messages.success(request, 'All files and records have been deleted.')
        
    except Exception as e:
        messages.warning(request, f'An error occurred: {e}')
        
    return redirect('personal_dashboard')
