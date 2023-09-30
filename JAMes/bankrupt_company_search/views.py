# Importieren der notwendigen Django-Bibliotheken und anderen Hilfsbibliotheken
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
import pickle
import os
from django.conf import settings
from ai_selection.models import FinalData, XGModel
import io
from bankrupt_company_search.templatetags.custom_filter import exclude_keys
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.http import HttpResponse
import csv

@cache_page(15 * 60)  # Cachen der View für 15 min
def search_company(request):
    # Initialisieren einer Fehlermeldung als None (wird später gesetzt, falls ein Fehler auftritt)
    error_message = None

    # Abfrage der GET-Parameter aus der Anfrage
    company_id = request.GET.get('company_id', '')
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    ai_method = request.GET.get('ai_method')

    # Konvertieren der `number_of_groups` in einen Integer, wenn vorhanden
    if number_of_groups is not None:
        number_of_groups = int(number_of_groups)

    # Datenbankabfrage für finale Datensätze anhand von Datei und Benutzer
    final_data_groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')

    # Fehlermeldung setzen, wenn keine Datensätze gefunden wurden
    if not final_data_groups:
        error_message = "No final data group found for the given user and file."
        return render(request, 'company_search.html', {'error_message': error_message})

    all_test_data = []
    for final_data_group in final_data_groups:
        # Abfrage des XGModel-Datensatzes für die aktuelle Daten-Gruppe
        xg_model_groups = XGModel.objects.filter(file_name=file, user=current_user, group_name=final_data_group.group_name).order_by('-uploaded_at')[:1]

        # Weiter zum nächsten Schritt, wenn keine passenden Modelle gefunden wurden
        if not xg_model_groups:
            continue

        xg_model_group = xg_model_groups[0]

        # Einlesen und Verarbeiten des Testdatensatzes und der Company-IDs
        test_data = pd.read_csv(io.StringIO(final_data_group.test_set.read().decode('utf-8')))
        company_ids_df = pd.read_csv(io.StringIO(final_data_group.company_id.read().decode('utf-8')))

        # Laden des trainierten Modells und Vorhersage mit den Testdaten
        model = pickle.loads(xg_model_group.model_file.read())
        X_test = test_data.drop(columns=['Insolvenz(t0)'])
        predictions = model.predict(X_test)

        # Hinzufügen der Vorhersagen und anderer relevanter Daten zu den Testdaten
        test_data['Prediction'] = predictions
        test_data['Company_ID'] = company_ids_df['Company_ID']
        test_data['Group_Name'] = final_data_group.group_name
        if final_data_group.group_name:
            test_data['Group_Name'] = final_data_group.group_name
        else:
            test_data['Group_Name'] = "Full Dataset"

        all_test_data.append(test_data)

    # Zusammenführen aller Testdatensätze in einen Gesamtdatensatz
    combined_test_data = pd.concat(all_test_data, ignore_index=True)

    data_rows = combined_test_data.to_dict('records')

    # Implementierung der Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(data_rows, 10)  # Anzeige von 10 Zeilen pro Seite
    try:
        data_rows = paginator.page(page)
    except PageNotAnInteger:
        data_rows = paginator.page(1)
    except EmptyPage:
        data_rows = paginator.page(paginator.num_pages)

    # Bestimmen der aktuellen, Start- und Endseite für die Pagination
    current_page = data_rows.number
    start_page = max(current_page - 5, 1)
    end_page = min(current_page + 4, paginator.num_pages)

    # Filtern von Schlüsseln für die Ausgabe
    filtered_keys = exclude_keys(data_rows[0], 'Company_ID,Prediction,Insolvenz(t0),Group_Name') if data_rows else {}

    # Rendern der Vorlage mit den vorbereiteten Daten
    return render(request, 'company_search.html', {'rows': data_rows, 'file': file, 'current_user': current_user, 'number_of_groups': 0 if number_of_groups is None else number_of_groups, 'ai_method': ai_method, 'company_id': company_id, 'start_page': start_page, 'end_page': end_page})

def filter_company(request):
    # Abfrage der GET-Parameter aus der Anfrage
    company_id = request.GET.get('company_id', '')
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    ai_method = request.GET.get('ai_method')

    # Konvertieren der `number_of_groups` in einen Integer, wenn vorhanden
    if number_of_groups is not None:
        number_of_groups = int(number_of_groups)

    # Datenbankabfrage für finale Datensätze und Modelle anhand von Datei und Benutzer
    final_data_groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')
    xg_model_groups = XGModel.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')

    test_data_list = []

    # Schleife durch die finalen Datensätze
    for final_data_group in final_data_groups:
        # Abfrage des passenden XGModel-Datensatzes für die aktuelle Daten-Gruppe
        xg_model_group = xg_model_groups.filter(group_name=final_data_group.group_name).first()

        # Weiter zum nächsten Schritt, wenn kein passendes Modell gefunden wurde
        if not xg_model_group:
            continue

        # Einlesen und Verarbeiten des Testdatensatzes und der Company-IDs
        test_data = pd.read_csv(io.StringIO(final_data_group.test_set.read().decode('utf-8')))
        company_ids_df = pd.read_csv(io.StringIO(final_data_group.company_id.read().decode('utf-8')))

        # Laden des trainierten Modells und Vorhersage mit den Testdaten
        model = pickle.loads(xg_model_group.model_file.read())
        X_test = test_data.drop(columns=['Insolvenz(t0)'])
        predictions = model.predict(X_test)

        # Hinzufügen der Vorhersagen und anderer relevanter Daten zu den Testdaten
        test_data['Prediction'] = predictions
        test_data['Company_ID'] = company_ids_df['Company_ID']
        test_data['Group_Name'] = final_data_group.group_name if final_data_group.group_name else "Full Dataset"

        # Anhängen der bearbeiteten Daten an die Gesamtliste
        test_data_list.append(test_data)

    # Zusammenführen aller Testdatensätze in einen Gesamtdatensatz
    combined_test_data = pd.concat(test_data_list, ignore_index=True)

    # Konvertieren des Datensatzes in ein Dictionary
    data_rows = combined_test_data.to_dict('records')

    # Filtern der Zeilen basierend auf der `Company_ID`
    filtered_rows = [row for row in data_rows if row['Company_ID'] == int(company_id)]

    # Rückgabe der gefilterten Zeilen als JSON-Antwort
    return JsonResponse({'rows': filtered_rows})





def filter_bankrupt(request):
    # Abfrage der GET-Parameter aus der Anfrage
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    ai_method = request.GET.get('ai_method')

    # Konvertieren von `number_of_groups` in einen Integer, wenn vorhanden
    if number_of_groups is not None:
        number_of_groups = int(number_of_groups)

    # Datenbankabfrage für finale Datensätze
    final_data_groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')

    all_test_data = []

    # Schleife durch die finalen Datensätze
    for final_data_group in final_data_groups:
        # Abfrage des passenden XGModel-Datensatzes für die aktuelle Daten-Gruppe
        xg_model_groups = XGModel.objects.filter(file_name=file, user=current_user, group_name=final_data_group.group_name).order_by('-uploaded_at')[:1]

        # Weiter zum nächsten Schritt, wenn kein passendes Modell gefunden wurde
        if not xg_model_groups:
            continue

        xg_model_group = xg_model_groups[0]

        # Einlesen und Verarbeiten des Testdatensatzes und der Company-IDs
        test_data = pd.read_csv(io.StringIO(final_data_group.test_set.read().decode('utf-8')))
        company_ids_df = pd.read_csv(io.StringIO(final_data_group.company_id.read().decode('utf-8')))

        # Laden des trainierten Modells und Vorhersage mit den Testdaten
        model = pickle.loads(xg_model_group.model_file.read())
        X_test = test_data.drop(columns=['Insolvenz(t0)'])
        predictions = model.predict(X_test)

        # Hinzufügen der Vorhersagen und anderer relevanter Daten zu den Testdaten
        test_data['Prediction'] = predictions
        test_data['Company_ID'] = company_ids_df['Company_ID']
        test_data['Group_Name'] = final_data_group.group_name if final_data_group.group_name else "Full Dataset"

        # Anhängen der bearbeiteten Daten an die Gesamtliste
        all_test_data.append(test_data)

    # Zusammenführen aller Testdatensätze in einen Gesamtdatensatz
    combined_test_data = pd.concat(all_test_data, ignore_index=True)
    model_predictions = combined_test_data.to_dict('records')

    # Filtern der Zeilen nach tatsächlichem Insolvenzstatus
    filtered_rows = [row for row in model_predictions if row['Insolvenz(t0)'] == 1]

    return JsonResponse({'rows': list(filtered_rows)})


def filter_predicted_bankrupt(request):
    # Abfrage der GET-Parameter aus der Anfrage
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    ai_method = request.GET.get('ai_method')

    # Konvertieren von `number_of_groups` in einen Integer, wenn vorhanden
    if number_of_groups is not None:
        number_of_groups = int(number_of_groups)

    # Datenbankabfrage für finale Datensätze
    final_data_groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')

    all_test_data = []

    # Schleife durch die finalen Datensätze
    for final_data_group in final_data_groups:
        xg_model_groups = XGModel.objects.filter(file_name=file, user=current_user, group_name=final_data_group.group_name).order_by('-uploaded_at')[:1]
        if not xg_model_groups:
            continue

        xg_model_group = xg_model_groups[0]
        test_data = pd.read_csv(io.StringIO(final_data_group.test_set.read().decode('utf-8')))
        company_ids_df = pd.read_csv(io.StringIO(final_data_group.company_id.read().decode('utf-8')))
        model = pickle.loads(xg_model_group.model_file.read())
        X_test = test_data.drop(columns=['Insolvenz(t0)'])
        predictions = model.predict(X_test)
        test_data['Prediction'] = predictions
        test_data['Company_ID'] = company_ids_df['Company_ID']
        test_data['Group_Name'] = final_data_group.group_name if final_data_group.group_name else "Full Dataset"
        all_test_data.append(test_data)

    combined_test_data = pd.concat(all_test_data, ignore_index=True)
    data_rows = combined_test_data.to_dict('records') 

    return JsonResponse({'rows': list(data_rows)})


def filter_bankrupt_and_predicted(request):
    # Werte aus dem GET-Request extrahieren
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    ai_method = request.GET.get('ai_method')  # Nicht genutzter Parameter

    # Falls 'number_of_groups' gesetzt ist, konvertiere es in einen Integer
    if number_of_groups is not None:
        number_of_groups = int(number_of_groups)

    # Filtere FinalData Objekte basierend auf dem Dateinamen und dem aktuellen Benutzer und sortiere sie nach Upload-Datum
    final_data_groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')

    data_rows = []
    for final_data_group in final_data_groups:
        # Filtere die XGModel Objekte für die entsprechende Gruppe und sortiere sie nach Upload-Datum
        xg_model_groups = XGModel.objects.filter(file_name=file, user=current_user, group_name=final_data_group.group_name).order_by('-uploaded_at')[:1]
        if not xg_model_groups:
            continue
        xg_model_group = xg_model_groups[0]

        # Lese die Testdaten und Unternehmens-IDs aus den Dateien
        test_data = pd.read_csv(io.StringIO(final_data_group.test_set.read().decode('utf-8')))
        company_ids_df = pd.read_csv(io.StringIO(final_data_group.company_id.read().decode('utf-8')))

        # Lade das trainierte Modell
        model = pickle.loads(xg_model_group.model_file.read())

        # Entferne die Zielvariable für die Vorhersage
        X_test = test_data.drop(columns=['Insolvenz(t0)'])
        predictions = model.predict(X_test)

        # Füge Vorhersagen und weitere Informationen zum Testdaten-DataFrame hinzu
        test_data['Prediction'] = predictions
        test_data['Company_ID'] = company_ids_df['Company_ID']
        test_data['Group_Name'] = final_data_group.group_name

        data_rows += test_data.to_dict('records')

    # Filtere die Datenzeilen nach tatsächlichem Insolvenzstatus und vorhergesagtem Insolvenzstatus
    data_rows = [row for row in data_rows if row['Insolvenz(t0)'] == 1 and row['Prediction'] == 1]

    return JsonResponse({'rows': list(data_rows)})


def save_predictions_to_csv(request): 
    error_message = None

    # Werte aus dem GET-Request extrahieren
    company_id = request.GET.get('company_id', '')
    file = request.GET.get('file')
    current_user = request.GET.get('current_user')
    number_of_groups = request.GET.get('number_of_groups')
    ai_method = request.GET.get('ai_method')  # Nicht genutzter Parameter

    # Falls 'number_of_groups' gesetzt ist, konvertiere es in einen Integer
    if number_of_groups is not None:
        number_of_groups = int(number_of_groups)

    # Filtere FinalData Objekte basierend auf dem Dateinamen und dem aktuellen Benutzer
    final_data_groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')

    # Überprüfe, ob entsprechende Daten gefunden wurden
    if not final_data_groups:
        error_message = "Für den gegebenen Benutzer und die Datei wurde keine abschließende Datengruppe gefunden."
        return render(request, 'company_search.html', {'error_message': error_message})

    all_test_data = []
    for final_data_group in final_data_groups:
        # Filtere die XGModel Objekte für die entsprechende Gruppe
        xg_model_groups = XGModel.objects.filter(file_name=file, user=current_user, group_name=final_data_group.group_name).order_by('-uploaded_at')[:1]
        if not xg_model_groups:
            continue
        xg_model_group = xg_model_groups[0]

        # Lese die Testdaten und Unternehmens-IDs aus den Dateien
        test_data = pd.read_csv(io.StringIO(final_data_group.test_set.read().decode('utf-8')))
        company_ids_df = pd.read_csv(io.StringIO(final_data_group.company_id.read().decode('utf-8')))

        # Lade das trainierte Modell
        model = pickle.loads(xg_model_group.model_file.read())

        # Entferne die Zielvariable für die Vorhersage
        X_test = test_data.drop(columns=['Insolvenz(t0)'])
        predictions = model.predict(X_test)

        # Füge Vorhersagen und weitere Informationen zum Testdaten-DataFrame hinzu
        test_data['Prediction'] = predictions
        test_data['Company_ID'] = company_ids_df['Company_ID']
        test_data['Group_Name'] = final_data_group.group_name if final_data_group.group_name else "Voller Datensatz"
        all_test_data.append(test_data)

    # Kombiniere alle Testdaten in einem DataFrame
    combined_test_data = pd.concat(all_test_data, ignore_index=True)

    # Ändere den Spaltennamen 'Insolvenz(t0)' in 'Actual Bankruptcy'
    combined_test_data.rename(columns={'Insolvenz(t0)': 'Actual Bankruptcy'}, inplace=True)

    # Ordne die Spalten neu
    ordered_columns = ['Group_Name', 'Company_ID', 'Prediction', 'Actual Bankruptcy'] + [col for col in combined_test_data.columns if col not in ['Group_Name', 'Company_ID', 'Prediction', 'Actual Bankruptcy']]
    combined_test_data = combined_test_data[ordered_columns]

    # Konvertiere die Spalten 'Actual Bankruptcy' und 'Prediction' in "yes" für 1 und "no" für 0
    combined_test_data['Actual Bankruptcy'] = combined_test_data['Actual Bankruptcy'].apply(lambda x: 'yes' if x == 1 else 'no')
    combined_test_data['Prediction'] = combined_test_data['Prediction'].apply(lambda x: 'yes' if x == 1 else 'no')

    # Erstelle die HttpResponse mit den entsprechenden CSV-Headern
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=predictions.csv'

    # Schreibe die Daten in die CSV-Datei
    writer = csv.writer(response)
    header = combined_test_data.columns.tolist()
    writer.writerow(header)
    for row in combined_test_data.values.tolist():
        writer.writerow(row)

    return response
