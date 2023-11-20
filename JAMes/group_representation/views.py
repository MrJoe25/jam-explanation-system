# Importiere erforderliche Bibliotheken und Module
from django.shortcuts import render
from group_preprocessing.models import *
from .models import *
import csv, io, os
from tablib import Dataset
import pandas as pd
from .functions import *
from django.core.files.base import ContentFile
from django.views.decorators.cache import cache_page
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

# Definiere die "splitting"-Funktion
def splitting(request):
    # Hole den Wert des 'file'-Parameters aus der GET-Anfrage
    file = request.GET.get('file')
    # Hole den Benutzernamen des aktuellen Nutzers
    superuser = request.user.username
    # Hole den Wert des 'current_user'-Parameters aus der GET-Anfrage
    current_user = request.GET.get('current_user')
    # Hole den Wert des 'number_of_groups'-Parameters aus der GET-Anfrage
    number_of_groups = request.GET.get('number_of_groups')
    # Erstelle ein Dictionary, das die obigen Werte enthält
    dict = {'file': file, 'current_user': current_user, 'number_of_groups': number_of_groups}
    # Rendere die "splitting.html"-Vorlage und übergebe das Dictionary als Kontext
    return render(request, 'splitting.html', dict)

# Dekoriere die "group_representation"-Funktion mit einem Cache von 15 Minuten
#@cache_page(15 * 60)
def group_representation(request):
    # Hole den Wert des 'file'-Parameters aus der GET-Anfrage
    file = request.GET.get('file')
    # Hole den Benutzernamen des aktuellen Nutzers
    superuser = request.user.username
    # Hole den Wert des 'current_user'-Parameters aus der GET-Anfrage
    current_user = request.GET.get('current_user')
    # Hole den Wert des 'number_of_groups'-Parameters aus der GET-Anfrage und konvertiere ihn zu einem Integer
    number_of_groups = int(request.GET.get('number_of_groups'))
    # Lösche alte Gruppenaufteilungen und erstelle neue basierend auf aktuellen Einstellungen
    GroupSplit.objects.filter(file_name=file).delete()
    # Hole alle Gruppenobjekte, die der Datei "file" zugeordnet sind
    groups = Group.objects.filter(file_name=file)
    # Hole die letzten "number_of_groups" Gruppenaufteilungen für die Datei "file"
    recent_group_splits = GroupSplit.objects.filter(file_name=file).order_by('-uploaded_at')[:number_of_groups]

    # Lese die CSV-Datei in einen Pandas-DataFrame
    df = pd.read_csv(f'media/{file}')

    # Durchlaufe alle Gruppen und erstelle für jede Gruppe einen DataFrame
    for group in groups:
        # Filtere den DataFrame auf der Grundlage der Grenzwerte der Gruppe
        df_group = df[(df['Bilanzsumme'] >= group.lower_bound) & (df['Bilanzsumme'] < group.upper_bound)]

        # Zähle die Anzahl der Insolvenzen
        count_insolvencies = df_group[df_group['Insolvenz'] == 1].shape[0]
        
        # Überprüfe, ob mindestens 2 Insolvenzen vorhanden sind
        if count_insolvencies < 2:
            messages.warning(request, 'The groups must contain at least 2 bankruptcies each.')
            # Erstelle einen Query-String mit den erforderlichen Parametern
            query_params = f"file={file}&current_user={current_user}&number_of_groups={number_of_groups}"
            # Füge den Query-String zur umgeleiteten URL hinzu
            redirect_url = f"{reverse('group_processing')}?{query_params}"
            return HttpResponseRedirect(redirect_url)


    # Überprüfe, ob bereits Gruppenaufteilungen vorhanden sind
    if not recent_group_splits:

        # Initialisiere eine leere Liste für die DataFrames der Gruppen
        dataframes = []
        # Durchlaufe alle Gruppen und erstelle für jede Gruppe einen DataFrame
        for group in groups:
            # Filtere den DataFrame auf der Grundlage der Grenzwerte der Gruppe
            df_group = df[(df['Bilanzsumme'] >= group.lower_bound) & (df['Bilanzsumme'] < group.upper_bound)]

            # Zähle die Anzahl der Insolvenzen
            count_insolvencies = df_group[df_group['Insolvenz'] == 1].shape[0]
            # Überprüfe, ob mindestens 2 Insolvenzen vorhanden sind
            if count_insolvencies < 2:
                messages.warning(request, 'The groups must contain at least 2 bankruptcies each.')
                # Erstelle einen Query-String mit den erforderlichen Parametern
                query_params = f"file={file}&current_user={current_user}&number_of_groups={number_of_groups}"
                # Füge den Query-String zur umgeleiteten URL hinzu
                redirect_url = f"{reverse('group_processing')}?{query_params}"
                return HttpResponseRedirect(redirect_url)

            # Entferne die Spalte "Bilanzsumme"
            df_group = df_group.drop(['Bilanzsumme'], axis=1)
            # Setze den Namen der Gruppe für den DataFrame
            df_group.name = group.group_name
            # Füge den DataFrame der Liste hinzu
            dataframes.append(df_group)

        # Durchlaufe alle DataFrames und speichere sie als neue Dateien
        for i, df_group in enumerate(dataframes):
            # Konvertiere den DataFrame in einen CSV-String
            content = df_group.to_csv(index=False)
            # Erstelle eine temporäre Datei mit dem CSV-String
            temp_file = ContentFile(content.encode('utf-8'))
            # Setze den Namen der neuen Datei
            file_name = f'group_{i + 1}_{file}'
            # Erstelle ein neues Gruppenaufteilungsobjekt
            group_split = GroupSplit.objects.create(file_name=file, superuser=superuser, user=current_user, group_name=df_group.name)
            # Speichere die temporäre Datei als Datei des Gruppenaufteilungsobjekts
            group_split.file.save(file_name, temp_file)
            # Speichere das Gruppenaufteilungsobjekt in der Datenbank
            group_split.save()

    # Hole erneut die letzten "number_of_groups" Gruppenaufteilungen für die Datei "file"
    recent_group_splits = GroupSplit.objects.filter(file_name=file).order_by('-uploaded_at')[:number_of_groups]
    # Initialisiere eine leere Liste für die Ergebnisse
    results = []
    # Durchlaufe alle kürzlich erstellten Gruppenaufteilungen und berechne statistische Daten
    for split in recent_group_splits:
        
        # Liest die CSV-Datei von dem Dateipfad des 'split' in einen Pandas DataFrame
        df = pd.read_csv(split.file.path)
        
        # Zählt die Häufigkeit der Werte in der Spalte 'Insolvenz' und speichert das Ergebnis
        insolvenz_info = df['Insolvenz'].value_counts()
        
        # Ermittelt die Anzahl der einzigartigen Werte für die Spalten 'Company_ID', 'Jahr', 'Insolvenz'
        unique = df[['Company_ID','Jahr','Insolvenz']].nunique()
        
        # Zählt die Anzahl der fehlenden Werte (NaN) für jede Spalte und konvertiert das Ergebnis in einen DataFrame
        df_null = df.isnull().sum().to_frame()
        
        # Beschreibt statistische Metriken für den DataFrame und formatiert die Zahlen
        stat = df.describe().apply(lambda s: s.apply('{0:.2f}'.format))
        
        # Holt die ersten 6 Zeilen des DataFrames und formatiert die numerischen Spalten
        df_head = df.head(6).apply(lambda s: s.apply('{0:.2f}'.format) if s.name not in ['Company_ID','Jahr','Insolvenz'] else s)
        
        # Konvertiert 'insolvenz_info' in einen DataFrame
        insolvenz_info_df = insolvenz_info.to_frame()
        
        # Konvertiert 'unique' in einen DataFrame
        df_unique = unique.to_frame()
        
        # Erzeugt HTML-Tabellen aus verschiedenen DataFrame-Teilen mit bestimmten CSS-Klassen
        df_head_html = df_head.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"], header=True, table_id='df_head_table')
        stat_html = stat.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped","table-hover"], header=True, table_id='stat_table')
        insolvenz_info_df_html = insolvenz_info_df.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=True, table_id='insolvenz_info_df_table')
        df_unique_html = df_unique.to_html(classes=[ "table", "table-striped", "table-bordered", "table-hover"], header=None, table_id='df_unique_table')
        df_null_html = df_null.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=None, table_id='df_null_table')
        
        # Fügt die berechneten und formatierten Daten dem 'results'-Array als ein Dictionary hinzu
        results.append({
            'file_name': split.file_name,
            'group_name': split.group_name,
            'file_path': split.file.url,
            'insolvenz_info_df_html': insolvenz_info_df_html,
            'df_unique_html': df_unique_html,
            'df_head_html': df_head_html,
            'stat_html': stat_html,
            'df_null_html': df_null_html,
        })

    # Erstelle ein Dictionary, das alle relevanten Daten enthält
    dict = {'file': file, 'current_user': current_user, 'number_of_groups': number_of_groups, 'results': results}
    # Rendere die "group_representation.html"-Vorlage und übergebe das Dictionary als Kontext
    return render(request, 'group_representation.html', dict)
