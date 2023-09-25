from django.http import FileResponse, Http404 # Importiere FileResponse und Http404 Klassen von Django
import pandas as pd # Importiere Pandas für Datenanalyse 
from .models import * # Importiere alle Models aus dem aktuellen App-Verzeichnis
from ai_selection.models import * # Importiere alle Models aus ai_selection App  
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, brier_score_loss # Importiere Klassifikationsmetriken von Scikit-Learn
from sklearn.metrics import confusion_matrix # Importiere Confusion Matrix von Scikit-Learn
from django.shortcuts import render, redirect # Importiere render und redirect Funktionen von Django 
import csv, io, os # Importiere csv, io und os Module
#from tablib import Dataset # Tablib Dataset wird nicht verwendet, auskommentiert
from django.core.files.base import ContentFile # Importiere ContentFile von Django für Datei-Uploads
from django.urls import reverse # Importiere reverse Funktion von Django für URLs  
import numpy as np # Importiere Numpy für numerische Operationen
from sklearn.metrics import ConfusionMatrixDisplay # Importiere ConfusionMatrixDisplay von Scikit-Learn
from matplotlib import * # Importiere alles von Matplotlib
import matplotlib # Importiere Matplotlib 
matplotlib.use('Agg') # Nutze Agg Backend für Matplotlib in Django  
import matplotlib.pyplot as plt # Importiere Pyplot von Matplotlib
from django.conf import settings # Importiere Django Settings 
import shap # Importiere SHAP für Modellerklärungen
import uuid # Importiere uuid für zufällige IDs
import pickle # Importiere pickle für Serialisierung von Modellen  
import eli5 # Importiere ELI5 für Permutation Importance
from eli5.sklearn import PermutationImportance # Importiere PermutationImportance von ELI5
import seaborn as sns # Importiere Seaborn für statistische Visualisierungen
from django.http import HttpResponse # Importiere HttpResponse von Django
from django.http import FileResponse # FileResponse wurde schon importiert
from reportlab.lib.enums import TA_CENTER # Importiere Text Alignment von Reportlab 
from reportlab.lib.pagesizes import letter, landscape # Importiere Seitenformatierungen von Reportlab
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # Importiere Textstile von Reportlab
from reportlab.lib.units import inch # Importiere Maßeinheiten von Reportlab
from reportlab.pdfgen import canvas # Importiere PDF canvas von Reportlab
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak # Importiere PDF Elemente von Reportlab 
from PyPDF2 import PdfFileMerger, PdfFileReader # Importiere PDF Manipulationsmodule
from reportlab.lib import colors as colors # Importiere Farben von Reportlab
from django.core.files import File # Importiere Django File Klasse
from django.core.files.base import ContentFile # ContentFile wurde schon importiert
from io import BytesIO # Importiere BytesIO für In-Memory Dateien  
from reportlab.platypus.flowables import KeepTogether # Importiere KeepTogether für formatting von Reportlab Elementen
from django.views.decorators.cache import cache_page # Importiere cache_page decorator von Django
from PIL import Image as PILImage # Importiere PIL Image Klasse







def load_model(model_file_path): # Funktion zum Laden eines Modells
    with open(model_file_path, 'rb') as f: # Öffne Modell im Lesemodus
        model = pickle.load(f) # Lade Modell mit Pickle
    return model # Gebe Modell zurück


def get_confusion_matrix(test_y_df, y_pred, group_name, labels=('Solvent', 'Bankrupt')): # Erstelle Confusion Matrix
    cf_matrix = confusion_matrix(test_y_df, y_pred) # Berechne Confusion Matrix
    # Use a heatmap color map and display the values in each cell
    # create SHAP-like colormap
    shap_colors = sns.color_palette('coolwarm', as_cmap=True) # Erstelle Farbpalette
    sns.heatmap(cf_matrix, cmap=shap_colors, annot=True, fmt='d', xticklabels=labels, yticklabels=labels) # Plotte Heatmap

    plt.title('Confusion Matrix') # Setze Titel
    plt.xlabel('Predicted') # Setze x-Label
    plt.ylabel('True') # Setze y-Label

    cf_matrix_file = 'xg_cm/cm_{}.png'.format(group_name) # Dateipfad für Confusion Matrix Plot
    cf_matrix_path = os.path.join(settings.MEDIA_ROOT, cf_matrix_file) # Erstelle absoluten Dateipfad

    # Save the figure as a high DPI PNG with a transparent background
    plt.savefig(cf_matrix_path, dpi=300, bbox_inches='tight', pad_inches=0, transparent=True) 

    # Clear the figure
    plt.clf()

    return cf_matrix_path



def get_model_details(model_file_path): # Funktion für Modellmetadaten
    # Load the saved model
    model = pickle.load(open(model_file_path, 'rb')) 

    # Get the number of boosting rounds
    try:
        num_boost_round = model.best_iteration+1 
    except AttributeError:
        num_boost_round = model.n_estimators+1

    # Get the hyperparameters
    try:
        hyperparameters_dict = model.get_xgb_params()
    except AttributeError:
        hyperparameters_dict = model.get_params()

    return num_boost_round, hyperparameters_dict







@cache_page(15 * 60) # Cache die Seite für 15 min
def xgexplain(request):
    file = request.GET.get('file') 
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    number_of_groups = int(request.GET.get('number_of_groups'))
    ai_method = request.GET.get('ai_method')
    last_page = request.META.get('HTTP_REFERER', None)

    # Erstelle den Ordner 'xg_shap', falls er nicht existiert
    xg_shap = os.path.join(settings.MEDIA_ROOT, 'xg_shap')
    if not os.path.exists(xg_shap):
        os.makedirs(xg_shap)

    # Erstelle den Ordner 'xg_cm', falls er nicht existiert
    xg_cm = os.path.join(settings.MEDIA_ROOT, 'xg_cm')
    if not os.path.exists(xg_cm):
        os.makedirs(xg_cm)

    if number_of_groups == 0: # Lade neuste Gruppe wenn keine angegeben
        groups = XGModel.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:1] 
    else: # sonst lade angegebene Anzahl Gruppen
        groups = XGModel.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:number_of_groups]

    results = []
    for group in groups:
        test_x_df = pd.read_csv(group.test_x_set.path) # Lade Testdaten
        test_y_df = pd.read_csv(group.test_y_set.path)

        # predict using the saved model
        model = load_model(group.model_file.path) # Lade Modell
        y_pred = model.predict(test_x_df) # Vorhersage mit Testdaten

        # calculate the accuracy, f1-score, precision, recall, roc-auc, brier-score, and confusion matrix
        accuracy = accuracy_score(test_y_df, y_pred) # Berechne Genauigkeit
        f1 = f1_score(test_y_df, y_pred) # Berechne F1-Score
        precision = precision_score(test_y_df, y_pred) # Berechne Präzision
        recall = recall_score(test_y_df, y_pred) # Berechne Recall
        roc_auc = roc_auc_score(test_y_df, y_pred) # Berechne ROC AUC
        brier = brier_score_loss(test_y_df, y_pred) # Berechne Brier Score

        num_boost_round, hyperparameters_dict = get_model_details(group.model_file.path) # Lade Modellmetadaten

        # Get the feature importances
        xg_feature_importances = model.get_booster().get_score(importance_type='gain') 
        sum_importances = sum(xg_feature_importances.values())
        xg_feature_importances = {k: float(v) / sum_importances for k, v in xg_feature_importances.items()}
        xg_feature_importances = sorted(xg_feature_importances.items(), key=lambda x: x[1], reverse=True)

        # Wählen Sie das wichtigste Feature für den Dependenzplot aus
        most_important_feature = xg_feature_importances[0][0]

        plt.switch_backend('agg') # Nutze Agg Backend
        explainer = shap.TreeExplainer(model) # Erstelle SHAP Erklärer
        shap_values = explainer.shap_values(test_x_df, check_additivity=False) # Berechne SHAP Werte
        shap_values_proba = 1 / (1 + np.exp(-shap_values)) # Transformiere SHAP Werte für Prognose       
        shap.summary_plot(shap_values_proba, test_x_df, plot_type="bar", class_names=True, show=False) # Erstelle SHAP Summary Plot
        plt.gcf()

        shap_file = 'xg_shap/shap_summary_plot_{}.png'.format(group.group_name) # Dateiname für Summary Plot
        plt.savefig(os.path.join(settings.MEDIA_ROOT, shap_file), dpi=300, bbox_inches='tight') # Speichere Summary Plot
        plt.clf()

        shap.summary_plot(shap_values_proba, test_x_df, show=False) # Erstelle SHAP Summary Plot
        plt.gcf()
        shap_file_value = 'xg_shap/shap_summary_plot_value{}.png'.format(group.group_name) # Dateiname für Summary Plot mit SHAP Werten
        plt.savefig(os.path.join(settings.MEDIA_ROOT, shap_file_value), dpi=300, bbox_inches='tight')
        plt.clf()

        # Erstellen des SHAP-Dependenzplots für das wichtigste Feature laut xgboost feature importance
        shap.dependence_plot(most_important_feature, shap_values, test_x_df, show=False) # Erstelle SHAP Dependenzplot
        plt.gcf()
        shap_file_dependence = 'xg_shap/shap_dependence_plot_{}.png'.format(group.group_name) # Dateiname für Dependenzplot
        plt.savefig(os.path.join(settings.MEDIA_ROOT, shap_file_dependence), dpi=300,  bbox_inches='tight')
        plt.clf()

        cf_matrix_path = get_confusion_matrix(test_y_df, y_pred, group.group_name, labels=['Solvent', 'Bankrupt']) # Erstelle Confusion Matrix
        cf_matrix_file = cf_matrix_path[len(settings.MEDIA_ROOT):] # Dateiname für Confusion Matrix
               
        # Generate the SHAP force plot
        explainer = shap.TreeExplainer(model) # Erstelle SHAP Erklärer
        shap_values = explainer.shap_values(test_x_df) # Berechne SHAP Werte
        shap.initjs() 
        shap.force_plot(explainer.expected_value, shap_values[0,:], test_x_df.iloc[[0]], show=False) # Erstelle SHAP Force Plot
        shap_file_force_plot = 'xg_shap/shap_force_plot{}.png'.format(group.group_name) # Dateiname für Force Plot
        plt.savefig(os.path.join(settings.MEDIA_ROOT, shap_file_force_plot), bbox_inches='tight') # Speichere Force Plot
        plt.clf()



        results.append({ # Füge Ergebnisse für Gruppe hinzu
        'group_name': group.group_name, 
        'accuracy': accuracy,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'roc_auc': roc_auc,
        'brier': brier,
        'confusion_matrix': f'{settings.MEDIA_URL}{cf_matrix_file}',  
        'xg_feature_importances': xg_feature_importances,
        'num_boost_round': num_boost_round,
        'hyperparameters': hyperparameters_dict,
        'shap_summary_plot': f'{settings.MEDIA_URL}{shap_file}',
        'shap_summary_plot_value': f'{settings.MEDIA_URL}{shap_file_value}',
        'shap_dependence_plot': f'{settings.MEDIA_URL}{shap_file_dependence}',
        'shap_force_plot': f'{settings.MEDIA_URL}{shap_file_force_plot}',
    })

        # Generate PDF report
    filename = f"xgboost_report.pdf" # Dateiname für PDF Report
    doc = SimpleDocTemplate(filename, pagesize=landscape(letter)) # Initialisiere SimpleDocTemplate 
    story = []

    # Add title to report
    story.append(Paragraph(f"XGBoost Report", getSampleStyleSheet()['Title'])) # Füge Titel hinzu

    # Add table for model evaluation metrics
    for result in results:
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Füge Gruppenname als Überschrift hinzu 
        story.append(KeepTogether([Paragraph("Model Evaluation Metrics", getSampleStyleSheet()['Heading2'])])) # Füge Metriken Überschrift hinzu
        headers=['Metric', 'Value'] # Tabellenkopf
        data = [headers]+[['Accuracy', result['accuracy']], ['F1-score', result['f1']], ['Precision', result['precision']], # Tabellendaten
        ['Recall', result['recall']], ['ROC AUC', result['roc_auc']], ['Brier Score', result['brier']]]  
        table = Table(data, colWidths=[150, 150]) # Erstelle Tabelle
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), # Formatierung und Stil
                                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  
                                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                ('FONTSIZE', (0, 0), (-1, 0), 14),
                                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 1), (-1, -1), 12),
                                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        story.append(table) # Füge Tabelle hinzu
        story.append(Spacer(1, 20)) # Leerzeile als Platzhalter
        story.append(PageBreak()) # Seitenumbruch
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Gruppenname
        story.append(KeepTogether([Paragraph(f" Feature Importances", getSampleStyleSheet()['Heading2'])])) # Überschrift
        data = [['Feature', 'Importance']] # Tabellenkopf
        for feature, importance in result['xg_feature_importances']: # Tabellendaten
            data.append([feature, importance])
        table = Table(data, colWidths=[150, 150]) # Erstelle Tabelle
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), # Formatierung
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),  
                                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                    ('FONTSIZE', (0, 1), (-1, -1), 12),
                                    ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        story.append(table) # Füge Tabelle hinzu
        story.append(Spacer(1, 20)) # Leerzeile als Platzhalter
        story.append(PageBreak())




            # Add hyperparameters
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Gruppenname
        story.append(KeepTogether([Paragraph(f"Hyperparameters", getSampleStyleSheet()['Heading2'])])) # Überschrift
        headers = ['Hyperparameter', 'Value'] # Tabellenkopf
        data = [headers]+[[key, value] for key, value in result['hyperparameters'].items()] # Tabellendaten
        table = Table(data, colWidths=[150, 150]) # Erstelle Tabelle
        table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey), # Formatierung
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), 
                                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                                    ('TOPPADDING', (0, 0), (-1, 0), 0),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 0),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                                    ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                                    ('TOPPADDING', (0, 1), (-1, -1), 0),
                                    ('BOTTOMPADDING', (0, 1), (-1, -1), 0),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)]))
        story.append(table) # Füge Tabelle hinzu
        story.append(PageBreak())



        def get_image_path(image_rel_path): # Hilfsfunktion um Bildpfad zu erhalten
            return os.path.normpath(os.path.join(settings.MEDIA_ROOT.rstrip('/media'), image_rel_path.lstrip('/')))  



        # Add confusion matrix
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Gruppenname
        story.append(Paragraph("Confusion Matrix", getSampleStyleSheet()['Heading2'])) # Überschrift
        image_path = get_image_path(result['confusion_matrix']) # Lade Bild
        story.append(Image(image_path, width=300, height=300, kind='proportional', hAlign='CENTER', mask='auto', lazy=True)) # Füge Bild hinzu
        story.append(Spacer(1, 20)) # Abstand 
        story.append(PageBreak()) # Seitenumbruch


        # Add SHAP summary plot
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Gruppenname
        story.append(Paragraph("SHAP Summary Plot", getSampleStyleSheet()['Heading2'])) # Überschrift
        image_path = get_image_path(result['shap_summary_plot']) # Lade Bild
        story.append(Image(image_path, width=300, height=300, kind='proportional', hAlign='CENTER', mask='auto', lazy=True)) # Füge Bild hinzu
        story.append(Spacer(1, 20)) # Abstand
        story.append(PageBreak()) # Seitenumbruch


        # Add SHAP summary plot value
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Gruppenname
        story.append(Paragraph("SHAP Summary Plot Value", getSampleStyleSheet()['Heading2'])) # Überschrift
        image_path = get_image_path(result['shap_summary_plot_value']) # Lade Bild
        story.append(Image(image_path, width=300, height=300, kind='proportional', hAlign='CENTER', mask='auto', lazy=True)) # Füge Bild hinzu
        story.append(Spacer(1, 20)) # Abstand
        story.append(PageBreak()) # Seitenumbruch

        # Add SHAP dependence plot
        story.append(Paragraph(f"Group: {result['group_name']}", getSampleStyleSheet()['Heading1'])) # Gruppenname
        story.append(Paragraph("SHAP Dependence Plot", getSampleStyleSheet()['Heading2'])) # Überschrift
        image_path = get_image_path(result['shap_dependence_plot']) # Lade Bild
        story.append(Image(image_path, width=300, height=300, kind='proportional', hAlign='CENTER', mask='auto', lazy=True)) # Füge Bild hinzu
        story.append(Spacer(1, 20)) # Abstand
        story.append(PageBreak()) # Seitenumbruch

        
   # Add report to database
    filename = f"xgboost_report.pdf" # Dateiname
    file_path = os.path.join(settings.MEDIA_ROOT, filename) # Dateipfad
    pdf_buffer = BytesIO() # Buffer für PDF Inhalt

    try:
        doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter)) # Initialisiere SimpleDocTemplate
        doc.build(story) # Baue PDF Dokument
    except Exception as e: 
        print(e) # Falls Fehler, gebe Fehler aus

    pdf_data = pdf_buffer.getvalue() # Lies PDF Daten aus Buffer

    # Save pdf buffer to file for testing purposes
    # with open("test.pdf", "wb") as f:
        # f.write(pdf_data)

    pdf_buffer.close() # Schließe Buffer


    report = Report(user=request.user) # Initialisiere Report Objekt
    report.report_file.save(filename, ContentFile(pdf_data)) # Speichere PDF
    report.save() # Speichere Report

    dict = {'file': file, 'current_user': current_user, 'number_of_groups': number_of_groups, 'last_page': last_page,
            'groups': groups, 'results': results, 'ai_method': ai_method, 'report': report}
    return render(request, 'xgexplain.html', dict) # Gebe Seite zurück