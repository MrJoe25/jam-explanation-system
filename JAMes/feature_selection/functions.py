# Importieren der erforderlichen Bibliotheken und Module
import csv
from numpy import datetime64, float64, int64, int32
import numpy as np
import pandas as pd
import re
import os
from os.path import exists
import sys
from pathlib import Path
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import TomekLinks
from imblearn.under_sampling import EditedNearestNeighbours
from imblearn.combine import SMOTEENN
from imblearn.combine import SMOTETomek
from collections import Counter
import pandas as pd

# Definition der Funktion remove_missing, die fehlende Werte in einem DataFrame entfernt
def remove_missing(variablen_cleaning,data):
    """
    Methoden zum entfernen aller Beobachtungen die fehlende Werte haben
    :param variablen_cleaning: Liste an Variablen die beruecksichtigt werden
    :param data:  Datensatz
    :return: Datensatz ohne Beobachtungen mit fehlenden Werten
    """
    # Verwenden der dropna-Methode von Pandas, um Zeilen mit fehlenden Werten zu entfernen
    data = data.dropna(axis= 0,subset= variablen_cleaning, how = "any")
    # Rückgabe des bereinigten Datensatzes
    return data

# Definition der Funktion remove_negative_values, die negative Werte in einem DataFrame entfernt
def remove_negative_values(variablen_cleaning,data):
    """
    Entfernen von Beobachtungen die negative Werte fuer eindeutig positive
    Kennzahlen aufweisen
    :param variablen_cleaning: Variablen deren Werte ueberprueft werden
    :param data: Datensatz zum bereinigen
    :return: bereinigter Datensatz
    """
    # Durchlaufen der Liste der Variablen, die berücksichtigt werden sollen
    for variable in variablen_cleaning:
    # Ermittlung der Indexpositionen für Zeilen mit negativen Werten für die aktuelle Variable
        index_to_drop = data[data[variable] < 0].index
    # Entfernen der identifizierten Zeilen aus dem DataFrame
        data = data.drop(index_to_drop)
    # Rückgabe des bereinigten Datensatzes
    return data

# Definition der Funktion rename_list_values, die Werte in einer Liste basierend auf einem Wörterbuch umbenennt
def rename_list_values(lst, rename_dict):
    # Durchlaufen der Liste und Überprüfung, ob der Wert im Wörterbuch rename_dict vorhanden ist
    for i, value in enumerate(lst):
        if value in rename_dict:
            # Ersetzung des Wertes durch den entsprechenden Wert im Wörterbuch rename_dict
            lst[i] = rename_dict[value]
    # Rückgabe der umbenannten Liste
    return lst

# Definition der Funktion feature_calc, die Features in einem DataFrame verarbeitet und berechnet
def feature_calc(original_list, data):
    # Löschen der Spalte 'STDR' aus dem DataFrame
    data.drop('STDR', axis=1, inplace=True)
    
    # Erstellen eines Wörterbuchs, das die Originalnamen der Features mit den abgekürzten Namen abbildet
    rename_dict = {
        'equity_ratio': 'ER',
        'working_capital_ratio': 'WCR',
        'return_on_total_assets': 'RTA',
        'return_on_equity': 'ROE',
        'asset_coverage_ratio': 'ACR',
        'second_degree_liquidity': 'L2',
        'short_term_debt_ratio': 'STDR'
    }
    
    renamed_list = rename_list_values(original_list, rename_dict)


    # Nach dem Datencleaning beginnt der Abschnitt zur Generierung der Features
    for string in renamed_list:
        # Überprüfung des Namens des Features und entsprechende Berechnung
        if string == 'ER':
            # Berechnung des Eigenkapitalquotienten
            data['ER'] = data['Eigenkapital'] / data['Bilanzsumme']
        elif string == 'WCR':
            # Berechnung des Working-Capital-Verhältnisses
            data['WCR'] = data['Umlaufvermoegen'] / data['kurzfristigeVerbindlichkeiten']
        elif string == 'RTA':
            # Berechnung der Rendite auf das gesamte Vermögen
            data['RTA'] = data['JahresueberschussFehlbetrag'] / data['Bilanzsumme']
        elif string == 'ROE':
            # Berechnung der Eigenkapitalrendite
            data['ROE'] = data['JahresueberschussFehlbetrag'] / data['Eigenkapital']
        elif string == 'ACR':
            # Berechnung des Anlagevermögen-Abdeckungsverhältnisses
            data['ACR'] = data['Eigenkapital'] / data['Anlagevermoegen']
        elif string == 'L2':
            # Berechnung der Liquidität zweiten Grades
            data['L2'] = data['Umlaufvermoegen'] / data['kurzfristigeVerbindlichkeiten']
        elif string == 'STDR':
            # Berechnung des Verhältnisses von kurzfristigen Verbindlichkeiten zur Bilanzsumme
            data['STDR'] = data['kurzfristigeVerbindlichkeiten'] / data['Bilanzsumme']

    # Ersetzen von Unendlichkeitswerten durch NaNs für die berechneten Features
    data[renamed_list] = data[renamed_list].replace([-np.inf, np.inf], np.nan)

    # Entfernen von Zeilen mit fehlenden Werten für die berechneten Features
    data.dropna(axis=0, subset=renamed_list, how="any", inplace=True)

    # Liste der Spalten, die am Anfang des DataFrame stehen sollen
    beginning_list = ['Company_ID', 'Jahr', 'Insolvenz', 'Bilanzsumme']

    # Gesamtliste der Spalten für das finale DataFrame
    columns = beginning_list + renamed_list

    # Rückgabe des bereinigten und veränderten DataFrames, beschränkt auf die relevanten Spalten
    return data[columns]


def firmengroesse_zuweisen(data):
    """
    Generierung der Firmengroesse basierend auf §267 und §267a
    als Feature fuer das Aufsplitten des Datensatzes

    :param data: gecleanter Datensatz
    :return: Datensatz mit der Firmengroesse
    """
    # Definition der verschiedenen Firmengrößen als Liste
    groessen_list = ['kleinst', 'klein', 'mittel', 'gross']

    # Definition der Bedingungen für jede Firmengröße als Liste von Booleans
    condition_list = [
        data['Bilanzsumme'] <= 350000, 
        (data['Bilanzsumme'] > 350000) & (data['Bilanzsumme'] <= 6000000),
        (data['Bilanzsumme'] > 6000000) & (data['Bilanzsumme'] <= 20000000), 
        data['Bilanzsumme'] > 20000000
    ]

    # Zuweisung der Firmengröße basierend auf den Bedingungen
    # Die Funktion np.select wählt Werte aus der 'groessen_list' basierend auf den 'condition_list'
    data['FIRMENGROESSE'] = np.select(condition_list, groessen_list)

    # Rückgabe des aktualisierten Datensatzes
    return data

def speichere_split_dataframe(dataframe, firmengroesse):
    """ Schreibt die Gespliteten Datensätze in den data Folder

    Methode die überprüft ob der Datensatz bereits existiert und wenn nicht
    diesen erstellt.

    :param aufgabe: Parameter zur Unterscheidung welche Prognose durchgefuehrt wird
    :param dataframe: Der Dataframe der jeweiligen Unternehmensgröße
    :param firmengroesse: String variable Firmengroesse
    :return: None
    """
    # Basispfad, in dem die CSV-Dateien gespeichert werden sollen
    path = 'C:/Users/user/joach/Cleaning_Mustafa/data'

    # Generieren des Dateinamens basierend auf der Firmengröße
    filename = "split_" + str(firmengroesse) + ".csv"

    # Kombinieren von Basispfad und Dateinamen zu einem vollständigen Pfad
    path = os.path.join(path, filename)

    # Überprüfen, ob eine Datei mit demselben Namen bereits im Verzeichnis existiert
    if os.path.isfile(path):
        # Wenn die Datei bereits existiert, wird eine Meldung ausgegeben
        print(f"Datensatz:{filename} nicht geschrieben - existiert bereits im data ordner")

    else:
        # Speichern des DataFrames als CSV-Datei, wenn sie noch nicht existiert
        dataframe.to_csv(path, index = False)

        # Ausgabe einer Erfolgsmeldung
        print(f"Split Datensatz:{filename} erfolgreich erstellt")
   

def split_dataframe(data):
    """
    Splittet den gecleanten Datensatz in drei kleinere Datensaetze und speichert
    diesen sofern es Aenderungen gab.
    :param data: Gecleanter Dataframe
    :param aufgabe: Aktuelle Aufgabe : Insolvenz oder Kreditrating
    """


    dataframe_list = [] # Erstelle eine leere Liste namens dataframe_list
    for firmengroesse in data['FIRMENGROESSE'].unique(): # Durchlaufe alle einzigartigen Werte in der Spalte 'FIRMENGROESSE'
        dataframe = data[data['FIRMENGROESSE'] == firmengroesse].copy() # Erstelle für jeden Wert ein DataFrame mit allen Zeilen, die diesen Wert in 'FIRMENGROESSE' haben
        dataframe_list.append(dataframe) # Füge das DataFrame zur Liste dataframe_list hinzu
        speichere_split_dataframe(dataframe, firmengroesse) # Rufe eine Funktion auf, um das DataFrame zu speichern

    return dataframe_list # Gib die Liste mit den aufgeteilten DataFrames zurück

# Definieren einer Funktion namens schreibe_verteilung_insolvenzen, die eine Liste von DataFrames als Parameter nimmt
def schreibe_verteilung_insolvenzen(data_list):
    """ Schreibt Verteilung von Insolventen zu nicht insolventen Datensätzen
    """

    # Initialisierung eines leeren Wörterbuchs namens insolvenzen_counter
    insolvenzen_counter = {
        
        # Füllen des Wörterbuchs mit Schlüssel-Wert-Paaren, wobei der Schlüssel der Wert der Spalte 'FIRMENGROESSE' ist
        # und der Wert ein Counter-Objekt ist, das die Häufigkeit des Auftretens von 'Insolvenz' in jedem DataFrame zählt
        df['FIRMENGROESSE'].agg('max'): Counter(df['Insolvenz']) for df in
        data_list
    }

    # Ausgabe des erstellten Wörterbuchs
    print(insolvenzen_counter)

# Definition der Funktion oversampling_SMOTE
def oversampling_SMOTE(data_list,feature_namen,label_name,sampling_strategy):
    """ Methode zum Sampling mit SMOTE

    :param data_list: List von Dataframes (kleinst, klein, mittel)
    :param feature_namen: relevante Features
    :param label_name: Zielvariabe
    :return: datalist: Oversampelte Dataframes in einer Liste, Firmengroessen Liste
    """

    # Initialisieren einer leeren Liste für die Firmengrößen
    firmengroesse_list =[]

    # Schleife über alle DataFrames in data_list
    for index,df in enumerate(data_list):
        # Einzigartigen Wert der Spalte 'FIRMENGROESSE' extrahieren
        firmengroesse = df['FIRMENGROESSE'].unique()[0]
        # Firmengröße zur Liste hinzufügen
        firmengroesse_list.append(firmengroesse)
        print("Resampling für Firmengroesse:" + firmengroesse)
        # Auswählen der relevanten Spalten für das Modell
        column_liste = feature_namen + list(label_name.split(" "))
        df = df.loc[:,column_liste]
        # Zielvariable und Eingabevariablen definieren
        y = df[label_name]
        X = df.loc[:,feature_namen]
        # Ausgabe der Größen der Ziel- und Eingabevariablen vor dem Oversampling
        print("Größe von y vor dem Oversampling " + str(y.shape))
        print("Größe von X vor dem Oversampling" +  str(X.shape))
        # Ausgabe der Verteilung der Zielvariable vor dem Oversampling
        print("Verteilung von Label: " + label_name + " vor dem Oversampling %s" %Counter(y))
        # SMOTE-Sampler initialisieren
        sm = SMOTE(random_state=1989, sampling_strategy=sampling_strategy,
                   k_neighbors=5)
        # Durchführung des Oversampling-Prozesses
        X_resampled, y_resampled = sm.fit_resample(X,y)
        print(X_resampled.shape)
        # Ausgabe der neuen Größe und Verteilung der resampelten Daten
        print("Verteilung von Label: " + label_name + " nach dem Sampling mit SMOTE %s" %Counter(y))
        print("Größe von X_resampled: " + str(X_resampled.shape))
        # Zusammenfügen der resampelten Eingabevariablen und der Zielvariable in einem neuen DataFrame
        data_list[index] = pd.concat([X_resampled, y_resampled], axis='columns')

    # Rückgabe der Liste der resampelten DataFrames und der Liste der Firmengrößen
    return data_list, firmengroesse_list

def oversampling_undersampling_tomek(data_list, feature_namen, label_name, sampling_strategy):
    """ Methode kombiniert Undersampling mit Tomek Links und Oversampling mit SMOTE.

    :param data_list: Liste von Dataframes (unterschiedliche Unternehmensgrößen)
    :param feature_namen: Liste der Feature-Namen
    :param label_name: Name der Zielvariablen
    :param sampling_strategy: Strategie für SMOTE-Oversampling
    :return: datalist: Liste von Dataframes nach Resampling, Liste der Firmengrößen
    """

    firmengroesse_list = []  # Liste, um die eindeutigen Firmengrößen zu speichern

    # Durchläuft alle DataFrames in der Liste data_list
    for index, df in enumerate(data_list):

        # Eindeutigen Wert der Spalte "FIRMENGROESSE" für Diagnosezwecke speichern
        firmengroesse = df['FIRMENGROESSE'].unique()[0]
        firmengroesse_list.append(firmengroesse)

        # Ausgabe der aktuell verarbeiteten Firmengröße
        print("Resampling für Firmengroesse:" + firmengroesse)

        # Auswahl der relevanten Spalten aus dem DataFrame
        column_liste = feature_namen + list(label_name.split(" "))
        df = df.loc[:, column_liste]

        # Zielvariable und Features für das Resampling
        y = df[label_name]
        X = df.loc[:, feature_namen]

        # Diagnose: Ausgabe der Größe der Zielvariable und der Features vor dem Resampling
        print("Größe von y vor dem Oversampling " + str(y.shape))
        print("Größe von X vor dem Oversampling" + str(X.shape))

        # Diagnose: Ausgabe der Verteilung der Zielvariable vor dem Resampling
        print("Verteilung von Insolvenzen vor dem Oversampling %s" % Counter(y))

        # Initialisierung von SMOTE und Tomek Links
        sm = SMOTE(random_state=1989, sampling_strategy=sampling_strategy, k_neighbors=5)
        tomek = TomekLinks(sampling_strategy='auto')

        # Kombination von SMOTE und Tomek Links
        smt = SMOTETomek(random_state=1989, smote=sm, tomek=tomek)

        # Durchführung des Resampling
        X_resampled, y_resampled = smt.fit_resample(X, y)

        # Diagnose: Ausgabe der Verteilung der Zielvariablen nach dem Resampling
        print("Verteilung von Label: " + label_name + " nach dem Sampling mit SMOTE-TOMEK %s" % Counter(y))

        # Diagnose: Ausgabe der Größe der resampelten Features
        print("Größe von X_resampled: " + str(X_resampled.shape))

        # Zusammenführung der resampelten Features und der resampelten Zielvariable in einem DataFrame
        data_list[index] = pd.concat([X_resampled, y_resampled], axis='columns')

    return data_list, firmengroesse_list  # Rückgabe der Liste der resampelten DataFrames und der Firmengrößen


def oversampling_undersampling_ENN(data_list, feature_namen, label_name, sampling_strategy):
    """ Methode kombiniert Oversampling mit SMOTE und Undersampling mit dem Edited Nearest Neighbour Algorithmus.

    :param data_list: Liste von Dataframes (unterschiedliche Unternehmensgrößen)
    :param feature_namen: Liste der Feature-Namen
    :param label_name: Name der Zielvariablen
    :param sampling_strategy: Strategie für SMOTE-Oversampling
    :return: datalist: Liste von Dataframes nach Resampling, Liste der Firmengrößen
    """

    firmengroesse_list = []  # Liste, um die eindeutigen Firmengrößen zu speichern

    # Durchläuft alle DataFrames in der Liste data_list
    for index, df in enumerate(data_list):

        # Eindeutigen Wert der Spalte "FIRMENGROESSE" für Diagnosezwecke speichern
        firmengroesse = df['FIRMENGROESSE'].unique()[0]
        firmengroesse_list.append(firmengroesse)

        # Ausgabe der aktuell verarbeiteten Firmengröße
        print("Resampling für Firmengroesse:" + firmengroesse)

        # Auswahl der relevanten Spalten aus dem DataFrame
        column_liste = feature_namen + list(label_name.split(" "))
        df = df.loc[:, column_liste]

        # Zielvariable und Features für das Resampling
        y = df[label_name]
        X = df.loc[:, feature_namen]

        # Diagnose: Ausgabe der Größe der Zielvariable und der Features vor dem Resampling
        print("Größe von y vor dem Oversampling " + str(y.shape))
        print("Größe von X vor dem Oversampling" + str(X.shape))

        # Diagnose: Ausgabe der Verteilung der Zielvariable vor dem Resampling
        print("Verteilung von Label: " + label_name + " vor dem Oversampling %s" % Counter(y))

        # Initialisierung von SMOTE
        sm = SMOTE(random_state=1989, sampling_strategy=sampling_strategy, k_neighbors=5)

        # Initialisierung von Edited Nearest Neighbours
        enn = EditedNearestNeighbours(sampling_strategy='not minority', n_neighbors=5, kind_sel="all")

        # Kombination von SMOTE und Edited Nearest Neighbours
        smote_enn = SMOTEENN(random_state=1989, smote=sm, enn=enn)

        # Durchführung des Resampling
        X_resampled, y_resampled = smote_enn.fit_resample(X, y)

        # Diagnose: Ausgabe der Verteilung der Zielvariablen nach dem Resampling
        print("Verteilung von Label: " + label_name + " nach dem Sampling mit SMOTE-ENN %s" % Counter(y))

        # Diagnose: Ausgabe der Größe der resampelten Features
        print("Größe von X_resampled: " + str(X_resampled.shape))

        # Zusammenführung der resampelten Features und der resampelten Zielvariable in einem DataFrame
        data_list[index] = pd.concat([X_resampled, y_resampled], axis='columns')

    return data_list, firmengroesse_list  # Rückgabe der Liste der resampelten DataFrames und der Firmengrößen


def sampling_durchfuehren(data_list,sampling_methode,feature_namen,label_name):
    """ Methode zum durchfuehren des Samplings

    :param data_list: Dataframe Liste mit den einzelnen gesplitteten Dataframes
    :param sampling_methode: zu verwende Sampling Methode
    :param feature_namen: Relevante Feature Namen fuer das Model
    :param label_name: Zielvariable
    :param aufgabe: Variable zur Bestimmung des SMOTE Sampling Parameters
    :return:
    """
    sampling_strategy = 0.5 # Festlegen der Sampling-Strategie (hier 50%)


    # Entscheidungsstruktur, um die geeignete Sampling-Methode auszuwählen und anzuwenden
    if sampling_methode == "SMOTE":
        # SMOTE-Oversampling durchführen
        data_list, firmengroesse_list = oversampling_SMOTE \
                                    (data_list = data_list ,
                                     feature_namen= feature_namen,
                                     label_name= label_name,
                                     sampling_strategy = sampling_strategy
                                    )
        return data_list, firmengroesse_list # Rückgabe der resampelten Daten und der Firmengrößen

    elif sampling_methode =="SMOTE-TOMEK":
        # Kombiniertes SMOTE-TOMEK Sampling durchführen
        data_list, firmengroesse_list = oversampling_undersampling_tomek \
            (data_list=data_list,
             feature_namen=feature_namen,
             label_name=label_name,
             sampling_strategy = sampling_strategy
             )
        return data_list,firmengroesse_list  # Rückgabe der resampelten Daten und der Firmengrößen

    elif sampling_methode =="SMOTE-ENN":
        # Kombiniertes SMOTE-ENN Sampling durchführen
        data_list, firmengroesse_list = oversampling_undersampling_ENN \
            (data_list=data_list,
             feature_namen=feature_namen,
             label_name=label_name,
             sampling_strategy = sampling_strategy
             )
        return data_list,firmengroesse_list # Rückgabe der resampelten Daten und der Firmengrößen

def speichere_oversampled_dataframe(dataframe_list,firmengroesse_list,sampling_methode):
    """
    Methode zum speichern der oversampelten dataframes im Ordner data
    :param dataframe_list: Die drei Dataframes für kleinst,klein,mittel Firmen
    :param firmengroesse_list: Liste mit Firmengroesse Strings
    :param sampling_methode: Verwendete Sampling Methode
    :param aufgabe: String mit Wert Kreditrating oder Insolvenz
    """

    # Durchläuft jede DataFrame in der Liste
    for index, dataframe in enumerate(dataframe_list):
        # Erstellt den Dateinamen unter Einbeziehung der Firmengröße und der Sampling-Methode
        filename = "oversampled_{0}_sampling_methode_{1}.csv".format(firmengroesse_list[index], sampling_methode)
        
        # Festlegung des Pfads, wo die Datei gespeichert werden soll
        path = 'C:/Users/user/joach/Cleaning_Mustafa/data'
        
        # Kombiniert den Basispfad und den Dateinamen zum vollständigen Pfad
        path_to_file = os.path.join(path, filename)
        
        # Überprüft, ob die Datei bereits existiert
        path = Path(path_to_file)
        if path.is_file():
            # Datei existiert bereits, daher keine erneute Speicherung
            print("Oversampled_Datensatz:" + filename + " nicht erstellt - er existiert bereits im data ordner")
        else:
            # Speichert die DataFrame als CSV-Datei
            dataframe.to_csv(path, index=True)
            print("Oversampled_Datensatz:" + filename + " erfolgreich erstellt")

