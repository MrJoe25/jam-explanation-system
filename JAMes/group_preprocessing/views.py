# Importe für Django-Funktionalitäten und Modelle
from django.shortcuts import render, redirect
from .models import Group
from .forms import GroupForm

# Datenbank- und Datei-Handling-Bibliotheken
import sqlite3
import json
from django.http import JsonResponse
from django.core.files.base import ContentFile

# Importe für andere Modelle aus der App und einer anderen App
from .models import *
from usermanagement.models import *

# Importe für CSV- und Datei-Handling
import csv, io, os
from tablib import Dataset

# Datenmanipulation mit Pandas und Funktionen für die Merkmalsauswahl
import pandas as pd
from feature_selection.functions import feature_calc

# Importe für Datenbank-Fehlerbehandlung und Caching
from django.db import IntegrityError
from django.views.decorators.cache import cache_page

# Funktion für die Gruppenverarbeitung
def group_processing(request):
    # Auslesen der 'file'-Variable aus den GET-Parametern
    file = request.GET.get('file')
    # Auslesen des aktuellen Superuser-Namens
    superuser = request.user.username
    # Auslesen des 'current_user'-Wertes aus den GET-Parametern
    current_user = request.GET.get('current_user')
    # Erstellung eines Wörterbuchs zur Übergabe an das Template
    dict = {'file': file, 'current_user': current_user}
    # Rendern der 'group_processing.html'-Seite mit dem Wörterbuch als Kontext
    return render(request, 'group_processing.html', dict)

# Funktion für die Vor-Segmentierung
def presegmentation(request):
    # Auslesen der 'file'-Variable aus den GET-Parametern
    file = request.GET.get('file')
    # Auslesen des aktuellen Superuser-Namens
    superuser = request.user.username
    # Auslesen des 'current_user'-Wertes aus den GET-Parametern
    current_user = request.GET.get('current_user')
    # Erstellung eines Wörterbuchs zur Übergabe an das Template
    dict = {'file': file, 'current_user': current_user}
    # Überprüfen, ob die Anfrage eine POST-Anfrage ist
    if request.method == 'POST':
        # Auslesen der 'number_of_groups' aus dem POST-Body
        number_of_groups = request.POST['number_of_groups']
        # Umleitung zur Segmentierungsseite mit aktualisierten Parametern
        return redirect(f'/group_preprocessing/segmentation/?file={file}&current_user={current_user}&number_of_groups={number_of_groups}')
    else:
        # Rendern der 'presegmentation.html'-Seite, falls keine POST-Anfrage vorliegt
        return render(request, 'presegmentation.html', dict)


# Funktion für die Segmentierung
def segmentation(request):
    # Auslesen der GET-Parameter
    file = request.GET.get('file')
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')

    # Lese die CSV-Datei in einen Pandas-DataFrame
    df = pd.read_csv(f'media/{file}')
    # Erstelle ein describe für die Spalte 'Bilanzsumme'
    describe = df['Bilanzsumme'].describe().map('{:.0f}'.format)

    # Konvertiere die Series in einen DataFrame
    describe_df = describe.to_frame()
    # Konvertiere den DataFrame in HTML
    describe_html = describe_df.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"], header=True, table_id='describe_table')

    # Berechne die Quantile der Bilanzsumme
    quantiles = df['Bilanzsumme'].quantile([0.25, 0.5, 0.75])

    # Erstelle eine neue Spalte, die das Quantil für jede Zeile anzeigt
    df['Quantile'] = pd.cut(df['Bilanzsumme'], bins=[0] + list(quantiles) + [float('inf')], labels=['0-25%', '25-50%', '50-75%', '75-100%'])

    # Gruppieren des DataFrames nach 'Quantile' und Zählen der Anzahl der Insolvenzen
    insolvency_distribution = df.groupby('Quantile')['Insolvenz'].sum().reset_index()

    # Formatieren der Insolvenzanzahl als Ganzzahlen
    insolvency_distribution['Insolvenz'] = insolvency_distribution['Insolvenz'].map('{:.0f}'.format)

    # Konvertieren des DataFrames in HTML
    insolvency_distribution_html = insolvency_distribution.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"], header=True, table_id='insolvency_distribution_table')
    
    # Erstellen einer Liste und Auswahlmöglichkeiten für die Gruppenanzahl
    int_list = list(range(1, int(number_of_groups)+1))
    choices = [(i, i) for i in int_list]
    
    # Abruf aller Gruppen für die aktuelle Datei
    groups = Group.objects.filter(file_name=file)
    error_message = None
    
    # Behandlung der POST-Anfrage
    if request.method == 'POST':
        form = GroupForm(request.POST)
        form.fields['file'].initial = file
        form.fields['group_choice'].choices = choices
        try:
            # Formularvalidierung
            if form.is_valid():
                form.clean()
                group_choice = form.cleaned_data['group_choice']
                group_name = form.cleaned_data['group_name']
                lower_bound = form.cleaned_data['lower_bound']
                upper_bound = form.cleaned_data['upper_bound']
                
                # Überprüfung der Gültigkeit der unteren und oberen Grenzen
                if lower_bound >= upper_bound:
                    error_message = "Lower bound should be smaller than upper bound."
                # Überprüfung auf bereits existierenden Gruppennamen für diese Datei
                elif Group.objects.filter(file_name=file, group_name=group_name).exists():
                    error_message = "Group name already exists for this file."
                else:
                    # Überprüfung, ob die Grenzen mit einer anderen Gruppe für diese Datei überschneiden
                    intersecting_groups = groups.filter(lower_bound__lt=upper_bound, upper_bound__gt=lower_bound)
                    if intersecting_groups:
                        error_message = "Bounds intersect with another group with the same file name."
                    else:
                        # Speichern der Gruppeninformationen in der Datenbank
                        group = Group(file_name=file, number_of_groups=number_of_groups, group_choice=group_choice,
                                    group_name=group_name, lower_bound=lower_bound, upper_bound=upper_bound)
                        group.save()
        # Handling von Validierungsfehlern
        except forms.ValidationError as e:
            error_message = str(e)
    
    # Für den Fall, dass es keine POST-Anfrage ist, Initialisierung des Formulars
    else:
        form = GroupForm(initial={'file': file})
        form.fields['group_choice'].choices = choices
        error_message = None
    
    # Überprüfen, ob der "Löschen"-Button gedrückt wurde
    if request.method == 'POST' and 'delete' in request.POST:
        group_id = request.POST.get('delete')
        Group.objects.filter(id=group_id).delete()
    
    # Erstellen des Kontext-Dictionarys für das Template
    dict = {'file':file, 'current_user':current_user, 'form':form, 'number_of_groups':number_of_groups, 'choices':choices,'groups':groups, 'error_message': error_message, 'describe_html': describe_html, 'insolvency_distribution_html': insolvency_distribution_html}
    
    # Rendern des HTML-Templates mit dem Kontext-Dictionary
    return render(request, 'segmentation.html', dict)



# Funktion zum Löschen einer Gruppe
def delete_group(request):
    # Abrufen der Gruppen-ID aus den GET-Parametern
    id = request.GET.get('group_id')
    
    # Finden der entsprechenden Gruppe in der Datenbank
    group = Group.objects.get(id=id)
    
    # Löschen der Gruppe aus der Datenbank
    group.delete()
    
    # Abrufen weiterer GET-Parameter
    file = request.GET.get('file')
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    
    # Umleitung zurück zur Segmentierungsseite mit den aktuellen Parametern
    return redirect(f'/group_preprocessing/segmentation/?file={file}&current_user={current_user}&number_of_groups={number_of_groups}')


