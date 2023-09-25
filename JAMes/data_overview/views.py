# Importiere die benötigten Bibliotheken und Module
from django.shortcuts import render
from .models import *
from usermanagement.models import *
import csv, io
from tablib import Dataset
import pandas as pd
from django.views.decorators.cache import cache_page

# Daten-Übersichts-Ansicht
def data_overview(request):
    # Rendere die 'data_overview.html' Vorlage
    return render(request, 'data_overview.html')

# Ergebnis-Ansicht
def results(request):
    # Hole den übermittelten Benutzernamen aus dem GET-Request
    user_submitted = request.GET.get('user')
    # Filtere die CSV-Dateien basierend auf dem übermittelten Benutzer
    data = CSVFile.objects.filter(user=user_submitted)
    csv_data = {'id': data}
    # Rendere die 'results.html' Vorlage mit den gefilterten CSV-Daten
    return render(request, 'results.html', csv_data)

# Ergebnis-CSV-Ansicht mit einer Cache-Dauer von 15 min
@cache_page(15 * 60)
def results_csv(request):
    # Hole die benötigten Daten aus dem GET-Request
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    # Filtere die CSV-Dateien basierend auf dem aktuellen Benutzer
    data = CSVFile.objects.filter(user=current_user)
    # Lese die CSV-Datei in einen DataFrame
    df = pd.read_csv(f'media/'+file)
    # Zähle die Anzahl der Werte in der 'Insolvenz'-Spalte
    insolvenz_info = df['Insolvenz'].value_counts()
    # Ermittle die Anzahl der eindeutigen Werte für bestimmte Spalten
    unique = df[['Company_ID','Jahr','Insolvenz']].nunique()
    # Zähle die fehlenden Werte je Spalte
    df_null = df.isnull().sum().to_frame()
    # Erhalte statistische Informationen über den DataFrame
    stat = df.describe().apply(lambda s: s.apply('{0:.2f}'.format))
    # Zeige die ersten 6 Zeilen des DataFrames
    df_head = df.head(6).apply(lambda s: s.apply('{0:.2f}'.format) if s.name in ['Anlagevermoegen','Umlaufvermoegen','Bilanzsumme','Eigenkapital','kurzfristigeVerbindlichkeiten','JahresueberschussFehlbetrag'] else s)
    # Konvertiere DataFrames in HTML-Tabellen
    insolvenz_info_df = insolvenz_info.to_frame()
    df_head_html = df_head.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"],
    header=True, table_id='df_head_table')
    stat_html = stat.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped","table-hover"],
    header=True, table_id='stat_table')
    insolvenz_info_df_html = insolvenz_info_df.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],
    header=True, table_id='insolvenz_info_df_table')
    df_unique = unique.to_frame()
    df_unique_html = df_unique.to_html(classes=[ "table", "table-striped", "table-bordered", "table-hover"], header=None,
    table_id='df_unique_table')
    df_null_html = df_null.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=None,
    table_id='df_null_table')
    # Fasse alle Daten für das Rendern zusammen
    file_data = {'file':file,'data':df_head_html,'stat':stat_html,'current_user':current_user,
    'id':data,'insolvenz':insolvenz_info_df_html,'unique':df_unique_html,'null':df_null_html}
    # Rendere die 'results_csv.html' Vorlage mit den zusammengesetzten Daten
    return render(request, 'results_csv.html', file_data)
