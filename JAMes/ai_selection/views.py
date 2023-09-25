from django.shortcuts import render, redirect # Importiere Render und Redirect Funktionen von Django 
from group_representation.models import * # Importiere alle Models aus group_representation App
from .models import * # Importiere alle Models aus aktueller App
from feature_selection.models import * # Importiere alle Models aus feature_selection App
import csv, io, os # Importiere csv, io und os Module
import pandas as pd # Importiere Pandas für Datenanalyse
from django.core.files.base import ContentFile # Importiere ContentFile von Django für Dateiuploads
from django.urls import reverse # Importiere reverse Funktion von Django für URLs
import numpy as np # Importiere Numpy für numerische Operationen 
from sklearn.model_selection import train_test_split # Für Aufteilung in Trainings- und Testdaten
from imblearn.over_sampling import SMOTE # Für Oversampling mit SMOTE
from imblearn.combine import SMOTETomek # Für Kombination aus SMOTE und Tomek Links
from imblearn.combine import SMOTEENN # Für Kombination aus SMOTE und ENN
from django.utils import timezone # Importiere timezone von Django
from IPython.display import display, HTML # Für Anzeige in HTML
import xgboost as xgb # Importiere xgboost 
from hyperopt import fmin, tpe, hp, Trials, SparkTrials # Für Bayesian Optimization
from sklearn.metrics import f1_score # Importiere F1-Score
from hyperopt import STATUS_OK, STATUS_FAIL # Status für Hyperparameter Optimization
from hyperopt import space_eval # Bewertung des Suchraums
from hyperopt.pyll.stochastic import sample # Ziehe Stichproben aus Suchraum
from django.views.decorators.cache import cache_page # Cache Seitenaufrufe
from django.utils.decorators import make_middleware_decorator # Middleware Dekoratoren




def ai_selection(request):
    file = request.GET.get('file') # Dateiname
    superuser = request.user.username # Superuser
    current_user = request.GET.get('current_user') # Aktueller User
    number_of_groups = int(request.GET.get('number_of_groups')) # Anzahl der Gruppen 
    last_page = request.META.get('HTTP_REFERER', None) # Letzte Seite

    if number_of_groups == 0: # Falls keine Gruppe angegeben
        groups = Feature_Table.objects.filter(file=file, user=current_user) # Lade Feature Tabelle

        if request.method == "POST": # Falls POST Request
            ai_method = request.POST.get(f'ai_method') # Hole AI Methode
            group_split = request.POST.get(f'group_split') # Hole Gruppensplit 
            bayesian_optimization = request.POST.get(f'bayesian_optimization') # Hole Bayesian Optimization Option

            if bayesian_optimization == 'no': # Falls kein Bayesian Optimization
                sampling_method = request.POST.get(f'sampling_method') # Hole Sampling Methode
            else:
                sampling_method = None # Sonst keine Sampling Methode

            for i in enumerate(groups): # Für jede Gruppe

                if bayesian_optimization == 'no': # Falls kein Bayesian Optimization
                    train, test, val, X_test_company_id, error_message = get_train_test_val_split(file, group_split, sampling_method) # Splitte Daten
                else:
                    train, test, val, X_test_company_id, error_message = train_test_val_split(file, group_split) # Splitte Daten ohne Sampling

                if error_message != None: # Falls Fehler
                    dict = {'file':file, 'current_user':current_user,'number_of_groups':number_of_groups,'last_page':last_page,'groups':groups,'error_message':error_message} # Erstelle Dict mit Fehlernachricht
                    return render(request, 'ai_selection.html', dict) # Gebe Seite mit Fehlernachricht zurück   

                # Speichere Trainings-, Test- und Validierungsdaten 
                final_data = FinalData(  
                    uploaded_at=timezone.now(),
                    superuser=superuser,
                    user=current_user,
                    file_name=file,
                    group_name=file,
                    ai_method=ai_method,
                    bayesian_optimization=bayesian_optimization,
                    train_test_validation_split=group_split,
                    sampling_technique=sampling_method
                )

                # Speichere Trainingsdaten
                train_file = ContentFile(train.to_csv(index=False, line_terminator='\n')) 
                final_data.train_set.save(f"{final_data.group_name}_train_set.csv", train_file)

                # Speichere Testdaten
                test_file = ContentFile(test.to_csv(index=False, line_terminator='\n'))
                final_data.test_set.save(f"{final_data.group_name}_test_set.csv", test_file)

                # Speichere Firmen-IDs der Testdaten
                id_file = ContentFile(X_test_company_id.to_csv(index=False, line_terminator='\n'))
                final_data.company_id.save(f"{final_data.group_name}_Xtest_id_set.csv", id_file)

                if val is not None: # Falls Validierungsdaten vorhanden
                    # Speichere diese
                    val_file = ContentFile(val.to_csv(index=False, line_terminator='\n'))  
                    final_data.validation_set.save(f"{final_data.group_name}_validation_set.csv", val_file)

                final_data.save() # Speichere FinalData Objekt

            if (ai_method == "xgboost" or "neural_networks"): # Falls XGBoost oder NN
                return redirect(f'/ai_selection/group_stats/?file={file}&current_user={current_user}&number_of_groups={number_of_groups}&ai_method={ai_method}') # Weiterleitung zu Gruppenstatistiken
    
        dict = {'file':file, 'current_user':current_user,'number_of_groups':number_of_groups,'last_page':last_page,'groups':groups}
        return render(request, 'ai_selection.html', dict) # Gebe Seite zurück


    groups = GroupSplit.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:number_of_groups] # Lade Gruppen

    if request.method == "POST": # Falls POST Request
        ai_method = request.POST.get(f'ai_method') # Hole AI Methode
        for i, group in enumerate(groups): # Für jede Gruppe
            group_split = request.POST.get(f'group_split{i + 1}') # Hole Split
            bayesian_optimization = request.POST.get(f'bayesian_optimization{i + 1}') # Hole Bayesian Optimization Option
            group.bayesian_optimization = bayesian_optimization # Setze
            group.ai_method = ai_method # Setze
            group.train_test_validation_split = group_split # Setze
            if bayesian_optimization == 'no': # Falls kein Bayesian Optimization
                group.sampling_technique = request.POST.get(f'sampling_method{i + 1}') # Setze Sampling Methode 
            else:
                group.sampling_technique = None # Sonst keine Sampling Methode
            group.save() # Speichere Gruppe
    

        for group in groups: # Für jede Gruppe
            file_loc = group.file # Dateipfad
            split_ratio = group.train_test_validation_split # Split Ratio
            sampling_method = group.sampling_technique # Sampling Methode
            bayesian_optimization = group.bayesian_optimization # Bayesian Optimization

            if bayesian_optimization == 'no': # Falls kein Bayesian Optimization
                train, test, val, X_test_company_id, error_message = get_train_test_val_split(file_loc, split_ratio, sampling_method) # Splitte mit Sampling
            else:
                train, test, val, X_test_company_id, error_message = train_test_val_split(file_loc, split_ratio) # Splitte ohne Sampling

            if error_message != None: # Falls Fehler
                dict = {'file':file, 'current_user':current_user,'number_of_groups':number_of_groups,'last_page':last_page,'groups':groups,'error_message':error_message} # Erstelle Dict mit Fehlernachricht
                return render(request, 'ai_selection.html', dict) # Gebe Seite mit Fehler zurück

            # Speichere Daten
            final_data = FinalData(  
                uploaded_at=timezone.now(),
                superuser=superuser,
                user=current_user,
                file_name=file,
                group_name=group.group_name,
                ai_method=group.ai_method,
                train_test_validation_split=split_ratio,
                sampling_technique=sampling_method,
                bayesian_optimization=bayesian_optimization
            )

            # Speichere Trainingsdaten
            train_file = ContentFile(train.to_csv(index=False, line_terminator='\n'))
            final_data.train_set.save(f"{final_data.group_name}_train_set.csv", train_file)

            # Speichere Testdaten  
            test_file = ContentFile(test.to_csv(index=False, line_terminator='\n'))
            final_data.test_set.save(f"{final_data.group_name}_test_set.csv", test_file)

            # Speichere Firmen-IDs der Testdaten
            id_file = ContentFile(X_test_company_id.to_csv(index=False, line_terminator='\n'))
            final_data.company_id.save(f"{final_data.group_name}_Xtest_id_set.csv", id_file)

            if val is not None: # Falls Validierungsdaten vorhanden
                # Speichere diese
                val_file = ContentFile(val.to_csv(index=False, line_terminator='\n'))
                final_data.validation_set.save(f"{final_data.group_name}_validation_set.csv", val_file)

            final_data.save() # Speichere FinalData Objekt

        if (ai_method == "xgboost" or "neural_networks"): # Falls XGBoost oder NN
            return redirect(f'/ai_selection/group_stats/?file={file}&current_user={current_user}&number_of_groups={number_of_groups}&ai_method={ai_method}') # Weiterleitung zu Gruppenstatistiken
                   
    dict = {'file':file, 'current_user':current_user,'number_of_groups':number_of_groups,'last_page':last_page,'groups':groups}
    return render(request, 'ai_selection.html', dict) # Gebe Seite zurück

def train_test_val_split(file, split_ratio):

    # Lade Daten in Pandas DataFrame
    df = pd.read_csv(f"media/{file}")

    # Überprüfe ob Spalte vorhanden ist
    if 'Bilanzsumme' in df.columns:
        # Falls ja, entferne sie
        df = df.drop(columns=['Bilanzsumme'])

    df.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)   # Sortiere nach Company_ID und Jahr
    df.reset_index(drop=True, inplace=True) # Setze Index neu

    df_gruppe_mit_Insolvenz = df.copy() # Kopie des DataFrames

    aa = df_gruppe_mit_Insolvenz.groupby('Company_ID')['Insolvenz'].sum() > 0 # Gruppiere nach Company_ID
    df_insolvent_series = aa[aa].index # Hole insolvente Firmen

    # Nur Gruppen mit Insolvenz  
    df_gruppe_ohne_Insolvenz = df_gruppe_mit_Insolvenz[~df_gruppe_mit_Insolvenz['Company_ID'].isin(df_insolvent_series)] 
    df_gruppe_mit_Insolvenz = df_gruppe_mit_Insolvenz[df_gruppe_mit_Insolvenz['Company_ID'].isin(df_insolvent_series)]
    df_gruppe_mit_Insolvenz.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)  
    df_gruppe_mit_Insolvenz.reset_index(drop=True, inplace=True)
    df_gruppe_ohne_Insolvenz.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)    
    df_gruppe_ohne_Insolvenz.reset_index(drop=True, inplace=True)

    # Entferne Zeilen nach Insolvenz 
    mask = df_gruppe_mit_Insolvenz.groupby('Company_ID')['Insolvenz'].cumsum() != 0 
    df_gruppe_mit_Insolvenz_cleaned = df_gruppe_mit_Insolvenz[mask]

    # Dataframes werden zusammengefügt
    df_merged = pd.concat([df_gruppe_mit_Insolvenz_cleaned, df_gruppe_ohne_Insolvenz])

    # Daten werden sortiert
    df_merged.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)   
    df_merged.reset_index(drop=True, inplace=True)

    # Anzahl Perioden wird bestimmt, die den kleinsten gemeinsamen Nenner für alle Firmen darstellen
    number_arrays = df_gruppe_mit_Insolvenz_cleaned.groupby(['Company_ID']).size().mean().astype(int)
    if number_arrays == 1:
        number_arrays = number_arrays+1

    # Anzahl Perioden in der Vergangenheit
    number_t_minus = number_arrays-1

    # Lösche Zeilen von Gruppen, die kleiner sind als festgelegte Anzahl Perioden
    df_change_gleich_perioden = df_merged.groupby('Company_ID').filter(lambda x: len(x) == number_arrays)
    df_change_groesser_perioden = df_merged.groupby('Company_ID').filter(lambda x: len(x) > number_arrays)

    # Wähle die ersten n Zeilen der Firmen aus
    df_change_groesser_perioden = df_change_groesser_perioden.groupby('Company_ID').head(number_arrays).reset_index(drop=True)


    # Dataframes werden zusammengefügt
    df_join = pd.concat([df_change_gleich_perioden, df_change_groesser_perioden])

    # Daten werden sortiert
    df_join.sort_values(['Company_ID', 'Jahr'], ascending=[True, True], inplace=True)   
    df_join.reset_index(drop=True, inplace=True)

    # Lösche Spalte Jahr
    df_join = df_join.drop('Jahr', axis=1)

    # Zeitreihe von lang nach breit
    group_size = number_arrays
    period = -number_t_minus
    dataframes= []
    for t in range(0, group_size):
        aa = df_join.rename(columns={col: col+('(t'+str(period)+')') for col in df_join.columns if col not in ['Company_ID']})
        dataframes.append(aa.groupby('Company_ID').nth([t]).reset_index(level=0))
        period = period+1

    df_gruppe = pd.concat(dataframes, axis = 1)

    # Entferne doppelte Spalten (nach Name)
    df_gruppe = df_gruppe.loc[:,~df_gruppe.columns.duplicated()].copy()

    # Entferne Zielspalten (t-n)
    df_gruppe = df_gruppe.loc[:,~df_gruppe.columns.str.startswith('Insolvenz(t-')]

    # Erstelle Kopie des Dataframes
    df = df_gruppe.copy()

    # Teile Daten in Trainings-, Test- und Validierungsdaten
    train_ratio, test_ratio, val_ratio = map(int, split_ratio.split("-"))
    train_ratio = train_ratio / 100
    test_ratio = test_ratio / 100

    # Erstelle Daten ohne Zielvariable
    X = df.drop("Insolvenz(t0)", axis=1)

    # Zielvariable
    y = df["Insolvenz(t0)"]

    # Prüfe ob Zielvariable nur 1 Klasse hat
    if len(np.unique(y)) <= 1:
        error_message = "Error: The target 'y' has not more than 1 class."
        return None, None, None, None, error_message
    
    # Teile Daten in Trainings- und Testdaten
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_ratio, stratify=y)

    # Speichere Firmen IDs der Testdaten   
    X_test_company_id = X_test['Company_ID']

    # Entferne Spalte Company_ID aus X_train und X_test
    X_train = X_train.drop('Company_ID', axis=1)
    X_test = X_test.drop('Company_ID', axis=1)

    # Falls keine Validierungsdaten
    if val_ratio == 0:
        return pd.concat([X_train, y_train], axis=1), pd.concat([X_test, y_test], axis=1), None, X_test_company_id , None
    else:
        # Berechne Validierungsdaten Anteil
        val_ratio = val_ratio / 100
        X_test, X_val, y_test, y_val = train_test_split(X_test, y_test, test_size=val_ratio, stratify=y_test)
        return pd.concat([X_train, y_train], axis=1), pd.concat([X_test, y_test], axis=1), pd.concat([X_val, y_val], axis=1), X_test_company_id, None

# Funktion um Trainings-, Test- und Validierungsdaten zu splitten
def get_train_test_val_split(file, split_ratio, sampling_method):

    # Lade die Daten in einen Pandas DataFrame
    df = pd.read_csv(f"media/{file}")

    # Überprüfe ob die Spalte existiert
    if 'Bilanzsumme' in df.columns:
        # Lösche die Spalte wenn sie existiert
        df = df.drop(columns=['Bilanzsumme'])

    # Sortiere die Daten
    df.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)   
    df.reset_index(drop=True, inplace=True)

    # Erstelle Kopie des Dataframes
    df_gruppe_mit_Insolvenz = df.copy()

    # Finde Firmen mit Insolvenz
    aa = df_gruppe_mit_Insolvenz.groupby('Company_ID')['Insolvenz'].sum() > 0
    df_insolvent_series = aa[aa].index

    # Nur Gruppen mit Insolvenz
    df_gruppe_ohne_Insolvenz = df_gruppe_mit_Insolvenz[~df_gruppe_mit_Insolvenz['Company_ID'].isin(df_insolvent_series)]
    df_gruppe_mit_Insolvenz = df_gruppe_mit_Insolvenz[df_gruppe_mit_Insolvenz['Company_ID'].isin(df_insolvent_series)]

    # Sortiere die Daten
    df_gruppe_mit_Insolvenz.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)   
    df_gruppe_mit_Insolvenz.reset_index(drop=True, inplace=True)
    df_gruppe_ohne_Insolvenz.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)   
    df_gruppe_ohne_Insolvenz.reset_index(drop=True, inplace=True)

    # # Lösche Zeilen nach Insolvenz (um nur die Informationen bis zur Insolvenz zu berücksichtigen)
    mask = df_gruppe_mit_Insolvenz.groupby('Company_ID')['Insolvenz'].cumsum() != 0
    df_gruppe_mit_Insolvenz_cleaned = df_gruppe_mit_Insolvenz[mask]

    # Dataframes verbinden
    df_merged = pd.concat([df_gruppe_mit_Insolvenz_cleaned, df_gruppe_ohne_Insolvenz])

    # Daten sortieren
    df_merged.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)   
    df_merged.reset_index(drop=True, inplace=True)

    # Bestimme Anzahl an Perioden, die den kleinsten gemeinsamen Nenner rerpäsentieren
    number_arrays = df_gruppe_mit_Insolvenz_cleaned.groupby(['Company_ID']).size().mean().astype(int)
    if number_arrays == 1:
        number_arrays = number_arrays+1

    # Anzahl Perioden in der Vergangenheit
    number_t_minus = number_arrays-1

    # # Lösche Zeilen mit zu wenig Perioden
    df_change_gleich_perioden = df_merged.groupby('Company_ID').filter(lambda x: len(x) == number_arrays)
    df_change_groesser_perioden = df_merged.groupby('Company_ID').filter(lambda x: len(x) > number_arrays)

    # Wähle erste n Zeilen
    df_change_groesser_perioden = df_change_groesser_perioden.groupby('Company_ID').head(number_arrays).reset_index(drop=True)


    # Verbinde Dataframes
    df_join = pd.concat([df_change_gleich_perioden, df_change_groesser_perioden])

    # Daten sortieren
    df_join.sort_values(['Company_ID', 'Jahr'], ascending=[True, True], inplace=True)   
    df_join.reset_index(drop=True, inplace=True)

    # Spalte 'Jahr' löschen
    df_join = df_join.drop('Jahr', axis=1)

    # Zeitreihe von long nach wide
    group_size = number_arrays
    period = -number_t_minus
    dataframes= []
    for t in range(0, group_size):
        aa = df_join.rename(columns={col: col+('(t'+str(period)+')') for col in df_join.columns if col not in ['Company_ID']})
        dataframes.append(aa.groupby('Company_ID').nth([t]).reset_index(level=0))
        period = period+1

    df_gruppe = pd.concat(dataframes, axis = 1)

    # Entferne doppelte Spalten (nach Name)
    df_gruppe = df_gruppe.loc[:,~df_gruppe.columns.duplicated()].copy()

    # Entferne Zielspalten (t-n)
    df_gruppe = df_gruppe.loc[:,~df_gruppe.columns.str.startswith('Insolvenz(t-')]

    # Erstelle Kopie des Dataframes
    df = df_gruppe.copy()

    # Teile Daten in Trainings-, Test- und Validierungsdaten
    train_ratio, test_ratio, val_ratio = map(int, split_ratio.split("-"))
    train_ratio = train_ratio / 100
    test_ratio = test_ratio / 100

    # Erstelle Daten ohne Zielvariable
    X = df.drop("Insolvenz(t0)", axis=1)

    # Zielvariable
    y = df["Insolvenz(t0)"]

    # Prüfen ob Zielvariable nur eine Klasse hat
    if len(np.unique(y)) <= 1:
        error_message = "Error: The target 'y' has not more than 1 class."
        return None, None, None, None, error_message

    # Teile Daten in Trainings- und Testdaten
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_ratio, stratify=y)

    # Speichere Firmen IDs der Testdaten
    X_test_company_id = X_test['Company_ID']

    # Entferne Spalte Company_ID aus X_train und X_test
    X_train = X_train.drop('Company_ID', axis=1)
    X_test = X_test.drop('Company_ID', axis=1)

    # Zähle Klassen der Zielvariablen
    y_count = y.value_counts()
    y_train_count = y_train.value_counts()
    y_test_count = y_test.value_counts()

    # Prüfe ob genügend Insolvenzen in Trainingsdaten
    if y_train_count[1] < 6:
        error_message = "Error: The training set has less than 6 bankruptcies. More data should be added to the data set. You could also try a different split or use Bayesian Optimization."
        return None, None, None, None, error_message

    # Wende Samplingmethode auf Trainingsdaten an
    if sampling_method == "smote":
        smote = SMOTE()
        X_train, y_train = smote.fit_resample(X_train, y_train)
    elif sampling_method == "smote_tomek":
        smote_tomek = SMOTETomek()
        X_train, y_train = smote_tomek.fit_resample(X_train, y_train)
    elif sampling_method == "smote_enn":
        smote_enn = SMOTEENN()
        X_train, y_train = smote_enn.fit_resample(X_train, y_train)

    # Falls keine Validierungsdaten
    if val_ratio == 0:
        return pd.concat([X_train, y_train], axis=1), pd.concat([X_test, y_test], axis=1), None, X_test_company_id, None
    else:
        
        # Berechne Validierungsdaten
        val_ratio = val_ratio / 100
        X_test, X_val, y_test, y_val = train_test_split(X_test, y_test, test_size=val_ratio, stratify=y_test)
        return pd.concat([X_train, y_train], axis=1), pd.concat([X_test, y_test], axis=1), pd.concat([X_val, y_val], axis=1), X_test_company_id, None

@cache_page(15 * 60) # Für 15 Minuten cachen
# Funktion für Gruppenstatistiken
def group_stats(request):  # Django View-Funktion, die einen HTTP-Request als Argument nimmt.
    # Abfrage von GET-Parametern und Metadaten
    file = request.GET.get('file')
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    number_of_groups = int(request.GET.get('number_of_groups'))
    ai_method = request.GET.get('ai_method')
    last_page = request.META.get('HTTP_REFERER', None)

    html_tables = []  # Leere Liste, die später HTML-Tabellen speichern könnte

    # Überprüfung der Anzahl der Gruppen
    if number_of_groups == 0:
        # Abfrage der FinalData-Objekte, die den Filterkriterien entsprechen
        groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:1]
        
        group_tables = []  # Leere Liste, die später Gruppentabellen speichern wird

        for group in groups:  # Durchläuft alle Gruppen in der Liste
            group_html_tables = []  # Leere Liste für HTML-Tabellen einer einzelnen Gruppe
            
            # Behandlung des Trainingsdatensatzes, falls vorhanden
            if group.train_set:
                train_df = pd.read_csv(group.train_set.path)
                group_html_tables.append(("Train set value count for 'Insolvenz' column", train_df['Insolvenz(t0)'].value_counts().to_frame().to_html(classes=["table", "table-striped", "table-bordered", "table-hover", "table-responsive"],header=True)))
                group_html_tables.append(("Train set description", train_df.describe().apply(lambda s: s.apply('{0:.2f}'.format)).to_html(classes=["table", "table-striped", "table-bordered", "table-hover", "table-responsive"],header=True)))

            # Behandlung des Testdatensatzes, falls vorhanden
            if group.test_set:
                test_df = pd.read_csv(group.test_set.path)
                group_html_tables.append(("Test set value count for 'Insolvenz' column", test_df['Insolvenz(t0)'].value_counts().to_frame().to_html(classes=["table", "table-striped", "table-bordered", "table-hover", "table-responsive"],header=True)))
                group_html_tables.append(("Test set description", test_df.describe().apply(lambda s: s.apply('{0:.2f}'.format)).to_html(classes=["table", "table-striped", "table-bordered", "table-hover", "table-responsive"],header=True)))

            # Behandlung des Validierungsdatensatzes, falls vorhanden
            if group.validation_set:
                validation_df = pd.read_csv(group.validation_set.path)
                group_html_tables.append(("Validation set value count for 'Insolvenz' column", validation_df['Insolvenz(t0)'].value_counts().to_frame().to_html(classes=["table", "table-striped", "table-bordered", "table-hover", "table-responsive"],header=True)))
                group_html_tables.append(("Validation set description", validation_df.describe().apply(lambda s: s.apply('{0:.2f}'.format)).to_html(classes=["table", "table-striped", "table-bordered", "table-hover", "table-responsive"],header=True)))

            # Fügt die HTML-Tabellen der aktuellen Gruppe zur Gesamtliste hinzu
            group_tables.append(group_html_tables)

        # Erstellung eines Kontext-Dictionarys für das Template
        dict = {'file': file, 'current_user': current_user, 'number_of_groups': number_of_groups, 'last_page': last_page, 'group_tables': group_tables, 'ai_method': ai_method, 'groups': groups}

        # Rendert die HTML-Seite mit dem Kontext
        return render(request, 'group_stats.html', dict)



    # Abfrage der FinalData-Objekte aus der Datenbank, die den Filterkriterien entsprechen.
# Sortiert die Ergebnisse in absteigender Reihenfolge nach 'uploaded_at' und schränkt die Anzahl der Ergebnisse ein.
    groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:number_of_groups]

    group_tables = []  # Leere Liste, die später HTML-Tabellen für verschiedene Gruppen speichern wird.

    # Iteriert durch jede Gruppe in der Abfrageergebnisliste
    for group in groups:
        group_html_tables = []  # Leere Liste, die HTML-Tabellen für die aktuelle Gruppe speichern wird.

        # Überprüft, ob ein Trainingsdatensatz für die aktuelle Gruppe vorhanden ist.
        if group.train_set:
            train_df = pd.read_csv(group.train_set.path)  # Liest den Trainingsdatensatz in einen Pandas DataFrame.
            # Fügt HTML-Tabellen für Trainingsdaten in die Liste ein.
            group_html_tables.append(("Train set value count for 'Insolvenz' column - group: " + group.group_name, train_df['Insolvenz(t0)'].value_counts().to_frame().to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],header=True)))
            group_html_tables.append(("Train set description - group: " + group.group_name, train_df.describe().apply(lambda s: s.apply('{0:.2f}'.format)).to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],header=True)))

        # Überprüft, ob ein Testdatensatz für die aktuelle Gruppe vorhanden ist.
        if group.test_set:
            test_df = pd.read_csv(group.test_set.path)  # Liest den Testdatensatz in einen Pandas DataFrame.
            # Fügt HTML-Tabellen für Testdaten in die Liste ein.
            group_html_tables.append(("Test set value count for 'Insolvenz' column - group: " + group.group_name, test_df['Insolvenz(t0)'].value_counts().to_frame().to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],header=True)))
            group_html_tables.append(("Test set description - group: " + group.group_name, test_df.describe().apply(lambda s: s.apply('{0:.2f}'.format)).to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],header=True)))

        # Überprüft, ob ein Validierungsdatensatz für die aktuelle Gruppe vorhanden ist.
        if group.validation_set:
            validation_df = pd.read_csv(group.validation_set.path)  # Liest den Validierungsdatensatz in einen Pandas DataFrame.
            # Fügt HTML-Tabellen für Validierungsdaten in die Liste ein.
            group_html_tables.append(("Validation set value count for 'Insolvenz' column - group: " + group.group_name, validation_df['Insolvenz(t0)'].value_counts().to_frame().to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],header=True)))
            group_html_tables.append(("Validation set description - group: " + group.group_name, validation_df.describe().apply(lambda s: s.apply('{0:.2f}'.format)).to_html(classes=["table", "table-striped", "table-bordered", "table-hover"],header=True)))

        # Fügt die generierten HTML-Tabellen für die aktuelle Gruppe zur Gesamtliste hinzu.
        group_tables.append(group_html_tables)

    # Erstellung eines Dictionarys für den Kontext der HTML-Vorlage.
    dict = {'file': file, 'current_user': current_user, 'number_of_groups': number_of_groups, 'last_page': last_page, 'group_tables': group_tables, 'ai_method': ai_method, 'groups': groups}

    # Rendert die HTML-Vorlage 'group_stats.html' mit dem Kontext-Dictionary und gibt sie als HTTP-Antwort zurück.
    return render(request, 'group_stats.html', dict)



# Die Funktion xg_param nimmt einen HTTP-Request als Eingabe.
def xg_param(request):
    # Verschiedene Parameter werden aus dem GET-Request und der aktuellen Benutzersitzung extrahiert.
    file = request.GET.get('file')
    superuser = request.user.username
    current_user = request.GET.get('current_user')
    number_of_groups = int(request.GET.get('number_of_groups'))
    ai_method = request.GET.get('ai_method')
    last_page = request.META.get('HTTP_REFERER', None)
    
    # Abhängig von der Anzahl der Gruppen werden unterschiedliche Datenbankeinträge abgefragt.
    if number_of_groups == 0:
        groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:1]
    else:
        groups = FinalData.objects.filter(file_name=file, user=current_user).order_by('-uploaded_at')[:number_of_groups]
        
    # Überprüft, ob der HTTP-Request eine POST-Methode ist.
    if request.method == "POST":
       # Für jede Gruppe in der Liste 'groups' wird eine Reihe von Operationen ausgeführt.
       for group in groups:
            # Lädt den Trainingsdatensatz aus der Datei in einen Pandas DataFrame.
            train_df = pd.read_csv(group.train_set)
            # Teilt die Daten in Merkmale (train_x) und Zielvariable (train_y).
            train_x = train_df.drop("Insolvenz(t0)", axis=1)
            train_y = train_df["Insolvenz(t0)"].astype(int)
            
            # Lädt den Testdatensatz aus der Datei in einen Pandas DataFrame.
            test_df = pd.read_csv(group.test_set)
            # Teilt die Daten in Merkmale (test_x) und Zielvariable (test_y).
            test_x = test_df.drop("Insolvenz(t0)", axis=1)
            test_y = test_df["Insolvenz(t0)"].astype(int)
            
            # Überprüft, ob Bayesian Optimization für die aktuelle Gruppe aktiviert ist.
            if group.bayesian_optimization == 'yes':
                # Definiert den Hyperparametersuchraum für das XGBoost-Modell.
                space = {'max_depth': hp.quniform("max_depth", 3, 20, 1),
                         'gamma': hp.quniform('gamma', 1, 9, 1),
                         'scale_pos_weight': hp.quniform('scale_pos_weight', 1, 1000, 1),
                         'learning_rate': hp.uniform('learning_rate', 0.1, 1),
                         'n_estimators': hp.quniform('n_estimators', 100, 5000, 100),
                         'subsample': hp.uniform('subsample', 0.5, 1),
                         'colsample_bytree': hp.uniform('colsample_bytree', 0.5, 1),
                         'min_child_weight': hp.uniform('min_child_weight', 0.5, 1),
                         'seed': 0}

                
                # Die Zielfunktion 'objective' wird definiert. Diese Funktion soll von Hyperopt minimiert werden.
                def objective(params):
                    # Verschiedene Hyperparameter werden in die erwarteten Datentypen umgewandelt.
                    params['max_depth'] = int(params['max_depth'])
                    params['gamma'] = int(params['gamma'])
                    params['scale_pos_weight'] = int(params['scale_pos_weight'])
                    params['n_estimators'] = int(params['n_estimators'])
                    params['seed'] = int(params['seed'])
                    
                    # Weitere Hyperparameter und Metriken für das XGBoost-Modell werden festgelegt.
                    params['objective'] = 'binary:logistic'
                    params['eval_metric'] = 'aucpr'
                    params['booster'] = 'gbtree'
                    params['subsample'] = float(params['subsample'])
                    params['colsample_bytree'] = float(params['colsample_bytree'])
                    params['min_child_weight'] = float(params['min_child_weight'])
                    params['learning_rate'] = float(params['learning_rate'])
                    params['grow_policy'] = 'lossguide'
                    params['tree_method'] = 'hist'
                    
                    # Das XGBoost-Klassifikationsmodell wird mit den festgelegten Parametern trainiert.
                    model = xgb.XGBClassifier(**params)
                    model.fit(train_x, train_y)
                    
                    # Vorhersagen auf dem Testdatensatz werden gemacht.
                    preds = model.predict(test_x)
                    
                    # Die F1-Score wird berechnet.
                    f1 = f1_score(test_y, preds)
                    
                    # Die Zielfunktion gibt einen negativen F1-Score zurück, da Hyperopt minimiert.
                    return {'loss': -f1, 'status': STATUS_OK, 'model': model, 'params': params, 'f1': f1}

                # Hyperparameter-Suche wird mit dem Tree-structured Parzen Estimator (TPE) Algorithmus durchgeführt.
                trials = Trials()
                best = fmin(fn=objective, 
                            space=space, 
                            algo=tpe.suggest, 
                            max_evals=333, 
                            trials=trials, 
                            show_progressbar=True, 
                            return_argmin=True, 
                            catch_eval_exceptions=True)

                # Ein XGBoost-Modell wird mit den besten Hyperparametern erstellt, die durch Hyperopt gefunden wurden.
                best = {
                    'gamma': int(best['gamma']),
                    'max_depth': int(best['max_depth']),
                    'n_estimators': int(best['n_estimators']),
                    'scale_pos_weight': int(best['scale_pos_weight']),
                    'seed': 0,
                    'subsample': float(best['subsample']),
                    'colsample_bytree': float(best['colsample_bytree']),
                    'min_child_weight': float(best['min_child_weight']),
                    'learning_rate': float(best['learning_rate']),
                    'eval_metric': 'aucpr',
                    'objective': 'binary:logistic',
                    'booster': 'gbtree',
                    'grow_policy': 'lossguide',
                    'tree_method': 'hist',
                }

                # Das XGBoost-Modell wird mit den besten gefundenen Hyperparametern trainiert.
                model = xgb.XGBClassifier(**best)
                model.fit(train_x, train_y)

                # Vorhersagen werden auf dem Testdatensatz gemacht.
                preds = model.predict(test_x)

                # Der F1-Score wird berechnet.
                f1 = f1_score(test_y, preds)

                # Die besten Hyperparameter und der F1-Score werden ausgegeben.
                print("Best parameters:", best)
                print("F1 score in percent:", f1 * 100)

                
                # Die besten Hyperparameter und die Versuchshistorie werden im XGModel-Objekt gespeichert.
                xg_model = XGModel.objects.create(
                    number_of_groups=number_of_groups,
                    uploaded_at=timezone.now(),
                    superuser=superuser,
                    user=current_user,
                    file_name=file,
                    group_name=group.group_name,
                    ai_method=ai_method,
                    train_test_validation_split=group.train_test_validation_split,
                    sampling_technique=group.sampling_technique,
                    bayesian_optimization=group.bayesian_optimization,
                    best_params=str(best),
                    trials=str(trials.trials)
                )

            # Andernfalls wird das XGBoost-Modell mit den vom Benutzer ausgewählten Hyperparametern trainiert.
            else:
                learning_rate = float(request.POST.get(f"learning_rate_{group.id}"))
                max_depth = int(request.POST.get(f"max_depth_{group.id}"))
                n_estimators = int(request.POST.get(f"n_estimators_{group.id}"))
                subsample = float(request.POST.get(f"subsample_{group.id}"))
                colsample_bytree = float(request.POST.get(f"colsample_bytree_{group.id}"))
                min_child_weight = float(request.POST.get(f"min_child_weight_{group.id}"))
                scale_pos_weight = int(request.POST.get(f"scale_pos_weight_{group.id}"))
                seed = 0
                gamma = int(request.POST.get(f"gamma_{group.id}"))

                model = xgb.XGBClassifier(
                    learning_rate=learning_rate, 
                    max_depth=max_depth, 
                    n_estimators=n_estimators, 
                    eval_metric='aucpr', 
                    objective='binary:logistic', 
                    booster='gbtree', 
                    grow_policy='lossguide', 
                    tree_method='hist', 
                    subsample=subsample, 
                    colsample_bytree=colsample_bytree, 
                    min_child_weight=min_child_weight, 
                    scale_pos_weight=scale_pos_weight, 
                    seed=seed, 
                    gamma=gamma
                )
                model.fit(train_x, train_y)


                # Speichert das trainierte XGBoost-Modell in XGModel
                xg_model = XGModel.objects.create(
                    number_of_groups=number_of_groups,
                    uploaded_at=timezone.now(),
                    superuser=superuser,
                    user=current_user,
                    file_name=file,
                    group_name=group.group_name,
                    ai_method=ai_method,
                    bayesian_optimization=group.bayesian_optimization,
                    train_test_validation_split=group.train_test_validation_split,
                    sampling_technique=group.sampling_technique
                )

            # Speichert die Trainings- und Testdaten im XGModel-Objekt
            train_x_file = ContentFile(train_x.to_csv(index=False, line_terminator='\n'))
            train_y_file = ContentFile(train_y.to_csv(index=False, line_terminator='\n'))
            test_x_file = ContentFile(test_x.to_csv(index=False, line_terminator='\n'))
            test_y_file = ContentFile(test_y.to_csv(index=False, line_terminator='\n'))
            xg_model.train_x_set.save(f"train_x_{group.group_name}.csv", train_x_file)
            xg_model.train_y_set.save(f"train_y_{group.group_name}.csv", train_y_file)
            xg_model.test_x_set.save(f"test_x_{group.group_name}.csv", test_x_file)
            xg_model.test_y_set.save(f"test_y_{group.group_name}.csv", test_y_file)

            # Serialisiert das Modell und speichert es als Pickle-Datei
            model_file = pickle.dumps(model)
            xg_model.model_file.save(f"{group.group_name}.pkl", ContentFile(model_file))

    # Wenn die Anfrage-Methode POST war, wird zur nächsten Seite weitergeleitet
    if request.method == 'POST':
        return redirect(f'/ai_explainability/?file={file}&current_user={current_user}&number_of_groups={number_of_groups}&ai_method={ai_method}')

    dict = {'file': file, 'current_user': current_user, 'number_of_groups': number_of_groups, 'last_page': last_page, 'groups': groups, 'ai_method': ai_method}
    return render(request, 'xg_param.html', dict)




