# Import der notwendigen Django-Module und weiteren Bibliotheken
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from .forms import FeatureselectionForm
from .models import *
from usermanagement.models import *
import csv, io, os
from tablib import Dataset
import pandas as pd
from .cleaning import cleaning  # Importieren einer Reinigungsfunktion für Daten
from .functions import feature_calc
from django.views.decorators.cache import cache_page
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseRedirect

# Definition der "datacleaning" Funktion, die die Datenreinigungsseite rendert
def datacleaning(request):
    file = request.GET.get('file')  # Dateiname aus GET-Request holen
    current_user = request.GET.get('current_user')  # Aktuellen Benutzer aus GET-Request holen
    cleaning_dict = {'file': file, 'current_user': current_user}  # Daten in ein Dictionary packen
    return render(request, 'datacleaning.html', cleaning_dict)  # Rendern der Datenreinigungsseite mit dem Dictionary

# Definition der "cleaned_data" Funktion, die gereinigte Daten zurückgibt
#@cache_page(15 * 60)  # Die Daten werden für 15 Minuten gecached
def cleaned_data(request):
    file = request.GET.get('file')
    superuser = request.user.username  # Superuser aus dem aktuellen Benutzerobjekt holen
    current_user = request.GET.get('current_user')
    
    # Daten aus der angegebenen Datei lesen und reinigen
    df = pd.read_csv(f'media/' + file)

    try:
        df = cleaning(df)  # Reinigungsfunktion aufrufen
    except MemoryError:
        messages.warning(request, 'Out of memory. The dataset is too large to process.') # Warnung ausgeben
        return HttpResponseRedirect(reverse('personal_upload'))  # Redirect to 'personal_upload' view

    # Count the number of insolvencies
    count_insolvencies = df[df['Insolvenz'] == 1].shape[0]
    # Check if at least 2 insolvencies are present
    if count_insolvencies < 2:
        # Add a warning message
        messages.warning(request, 'The dataset must contain at least 2 bankruptcies.')
        
        # Try to delete the dataset from the SQL database
        try:
            data_to_delete = CSVFile.objects.get(file=file, user=current_user)
            data_to_delete.delete()
        except Exception as e:
            messages.warning(request, f'An error occurred while deleting the database record: {e}')
            return HttpResponseRedirect(reverse('personal_upload'))

        # Try to delete the file from the folder
        try:
            os.remove(f'media/{file}')
        except Exception as e:
            messages.warning(request, f'An error occurred while deleting the file: {e}')

        # Redirect the user to 'personal_upload' page
        return HttpResponseRedirect(reverse('personal_upload'))
    
    # Erhalte verschiedene statistische Daten aus dem DataFrame
    insolvenz_info = df['Insolvenz'].value_counts()
    unique = df[['Company_ID', 'Jahr', 'Insolvenz']].nunique()
    df_null = df[['Company_ID', 'Jahr', 'Insolvenz', 'Anlagevermoegen', 'Umlaufvermoegen', 'Bilanzsumme', 'Eigenkapital', 'kurzfristigeVerbindlichkeiten', 'JahresueberschussFehlbetrag']].isnull().sum().to_frame()
    stat = df[['Company_ID', 'Jahr', 'Insolvenz', 'Anlagevermoegen', 'Umlaufvermoegen', 'Bilanzsumme', 'Eigenkapital', 'kurzfristigeVerbindlichkeiten', 'JahresueberschussFehlbetrag']].describe().apply(lambda s: s.apply('{0:.2f}'.format))
    
    # Erzeuge HTML-Tabellen aus den Daten
    df_head = df[['Company_ID', 'Jahr', 'Insolvenz', 'Anlagevermoegen', 'Umlaufvermoegen', 'Bilanzsumme', 'Eigenkapital', 'kurzfristigeVerbindlichkeiten', 'JahresueberschussFehlbetrag']].head(6).apply(lambda s: s.apply('{0:.2f}'.format) if s.name in ['Anlagevermoegen', 'Umlaufvermoegen', 'Bilanzsumme', 'Eigenkapital', 'kurzfristigeVerbindlichkeiten', 'JahresueberschussFehlbetrag'] else s)
    
    # Umwandeln der DataFrame-Informationen in HTML-Tabellen mit entsprechenden Klassen
    insolvenz_info_df = insolvenz_info.to_frame()
    df_unique = unique.to_frame()
    df_head_html = df_head.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"], header=True, table_id='df_head_table')
    stat_html = stat.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"], header=True, table_id='stat_table')
    insolvenz_info_df_html = insolvenz_info_df.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=True, table_id='insolvenz_info_df_table')
    df_unique_html = df_unique.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=None, table_id='df_unique_table')
    df_null_html = df_null.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=None, table_id='df_null_table')
    
    request.session['old_file_cleaned'] = file  # Speichere den alten Dateinamen in einer Session-Variable
    
    # Erstelle den Dateinamen für die gereinigte Datei
    file_short = os.path.splitext(file)[0]
    cleaned_string = '_Cleaned'
    csv_string = '.csv'
    file_name = file_short + cleaned_string + csv_string
    
    # Speichere den gereinigten DataFrame als CSV
    content = df.to_csv(index=False)
    temp_file = ContentFile(content.encode('utf-8'))
    
    # Erzeuge ein neues Cleaned_File Objekt und speichere es in der Datenbank
    cleaned_file = Cleaned_File.objects.create(superuser=superuser, user=current_user)
    cleaned_file.file.save(file_name, temp_file)
    new_file = cleaned_file.filename()
    
    # Erzeuge das finale Dictionary zur Datenübergabe an die HTML-Seite
    cleaning_dict = {'file': file, 'cleaned_file': new_file, 'current_user': current_user, 'data': df_head_html, 'stat': stat_html, 'insolvenz': insolvenz_info_df_html, 'unique': df_unique_html, 'null': df_null_html}
    
    return render(request, 'cleaned_data.html', cleaning_dict)  # Rendern der Seite mit den gereinigten Daten




def featureselection(request):
    # Dateiname aus der Anfrage holen
    file = request.GET.get('file')
    # Aktuellen Benutzernamen holen
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    # Alten Dateinamen aus der Session holen
    old_file = request.session.get('old_file_cleaned')
    
    if request.method == 'POST':
        # Formular zur Auswahl von Features initialisieren
        form = FeatureselectionForm(request.POST)
        
        if form.is_valid():
            selected_features = []
            # Durchlaufen aller Felder im Formular und Auswahl der ausgewählten Features
            for field in form:
                if field.value():
                    selected_features.append(field.name)
            
            # Überprüfen, ob mindestens 3 Features ausgewählt wurden
            if len(selected_features) < 3:
                error_message = "Please select at least 3 features"
                return render(request, 'featureselection.html', {'form': form, 'error_message': error_message})
            
            form.save()
            
            # Einlesen der CSV-Datei
            df = pd.read_csv(f'media/'+file)
            # Feature-Berechnung durchführen
            df = feature_calc(selected_features, df)
            
            # Speichern des alten Dateinamens in einer Session-Variable
            request.session['old_file_selection'] = file
            
            # Erstellen des Namens für die neue Datei
            file_short = os.path.splitext(file)[0]
            cleaned_string = '_Features'
            csv_string = '.csv'
            file_name = file_short + cleaned_string + csv_string
            content = df.to_csv(index=False)
            temp_file = ContentFile(content.encode('utf-8'))
            
            # Speichern der neuen Datei in der Datenbank
            feature_file = Feature_Table.objects.create(superuser=superuser, user=current_user)
            feature_file.file.save(file_name, temp_file)
            new_file = feature_file.filename() 
            # Weiterleitung zur Statistikseite
            return redirect(f'featurestat/?file={new_file}&current_user={current_user}')
    else:
        # Wenn keine POST-Anfrage vorliegt, Formular ohne Daten initialisieren
        form = FeatureselectionForm()

    # Rückgabedaten für das Rendering vorbereiten
    dict = {'form': form, 'file': file, 'current_user': current_user, 'old_file': old_file}
    return render(request, 'featureselection.html', dict)

@cache_page(15 * 60)  # Caching der Ansicht für 15 Minuten
def featurestat(request):
    # Daten aus der Anfrage und Session holen
    file = request.GET.get('file')
    old_file = request.session.get('old_file_selection')
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    
    # Einlesen der Datei mit Pandas
    df = pd.read_csv(f'media/'+file)
    
    # Count the number of insolvencies
    count_insolvencies = df[df['Insolvenz'] == 1].shape[0]
    # Check if at least 2 insolvencies are present
    if count_insolvencies < 2:
        messages.warning(request, 'The dataset must contain at least 2 bankruptcies.')
        # Erstelle einen Query-String mit den erforderlichen Parametern
        query_params = f"file={file}&current_user={current_user}"
        # Füge den Query-String zur umgeleiteten URL hinzu
        redirect_url = f"{reverse('featureselection')}?{query_params}"
        return HttpResponseRedirect(redirect_url)  # Redirect to 'featureselection' view

    # Statistische Informationen aus dem DataFrame holen
    insolvenz_info = df['Insolvenz'].value_counts()
    unique = df[['Company_ID','Jahr','Insolvenz']].nunique()
    df_null = df.isnull().sum().to_frame()
    stat = df.describe().apply(lambda s: s.apply('{0:.2f}'.format))
    df_head = df.head(6).apply(lambda s: s.apply('{0:.2f}'.format) if s.name not in ['Company_ID','Jahr','Insolvenz'] else s)
    
    # Daten in HTML-Format umwandeln für die Anzeige im Frontend
    insolvenz_info_df = insolvenz_info.to_frame()
    df_unique = unique.to_frame()
    df_head_html = df_head.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped", "table-hover"], header=True, table_id='df_head_table')
    stat_html = stat.to_html(classes=["table", "table-responsive", "table-bordered", "table-striped","table-hover"], header=True, table_id='stat_table')
    insolvenz_info_df_html = insolvenz_info_df.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=True, table_id='insolvenz_info_df_table')
    df_unique_html = df_unique.to_html(classes=[ "table", "table-striped", "table-bordered", "table-hover"], header=None, table_id='df_unique_table')
    df_null_html = df_null.to_html(classes=["table", "table-striped", "table-bordered", "table-hover"], header=None, table_id='df_null_table')

    # Vorbereitung der Daten für das Rendering der Webseite
    dict = {'file':file, 'current_user':current_user, 'data':df_head_html, 'stat':stat_html, 'insolvenz':insolvenz_info_df_html, 'unique':df_unique_html, 'null':df_null_html, 'old_file': old_file}

    return render(request, 'featurestat.html', dict)

