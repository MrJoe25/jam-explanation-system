# Importieren der erforderlichen Module und Bibliotheken
import csv
from numpy import datetime64, float64, int64, int32
import numpy as np
import pandas as pd
import re
import os
import sys
from .functions import *  # Importieren aller Funktionen aus der "functions"-Datei im aktuellen Verzeichnis

# Definition der Reinigungsfunktion, die einen DataFrame als Argument nimmt
def cleaning(df):

    # Finden der Zeilennummern, in denen "Insolvenz" gleich 1 ist
    row_numbers = df[df['Insolvenz'] == 1].index

    # Schleife durch alle Zeilennummern
    for row in row_numbers:
        # Wenn die "Company_ID" in der nächsten Zeile der aktuellen Zeile entspricht,
        # wird das "Insolvenz"-Feld der nächsten Zeile auf den Wert der aktuellen Zeile gesetzt
        if df.iloc[row+1]['Company_ID'] == df.iloc[row]['Company_ID']:
            df.at[row+1,'Insolvenz'] = df.iloc[row]['Insolvenz']

    # Datentypen von 'Jahr' und 'Company_ID' ändern
    df['Jahr']=df['Jahr'].astype(int)
    df['Company_ID'] = df['Company_ID'].astype(int64)

    # Neue Spalte 'Gesamtvermoegen' hinzufügen, die die Summe von 'Anlagevermoegen' und 'Umlaufvermoegen' enthält
    df['Gesamtvermoegen'] = df['Anlagevermoegen'] + df['Umlaufvermoegen']

    # Neue Spalte 'Anlagenintensitaet' hinzufügen, die das Verhältnis von 'Anlagevermoegen' zu 'Gesamtvermoegen' darstellt
    df['Anlagenintensitaet'] = df['Anlagevermoegen'] / df['Gesamtvermoegen']

    # Neue Spalte 'Umlaufintensitaet' hinzufügen, die das Verhältnis von 'Umlaufvermoegen' zu 'Gesamtvermoegen' darstellt
    df['Umlaufintensitaet'] = df['Umlaufvermoegen'] / df['Gesamtvermoegen']

    # Neue Spalte 'STDR' hinzufügen, die das Verhältnis von 'kurzfristigeVerbindlichkeiten' zu 'Bilanzsumme' darstellt
    df['STDR'] = df['kurzfristigeVerbindlichkeiten'] / df['Bilanzsumme']

    # Erstellung einer Kopie des DataFrame
    df_gruppe_mit_Insolvenz = df.copy()


        # Gruppierung des DataFrames df_gruppe_mit_Insolvenz nach 'Company_ID' und Summierung der 'Insolvenz'-Werte
    # Danach Überprüfung, ob die Summe größer als 0 ist
    aa = df_gruppe_mit_Insolvenz.groupby('Company_ID')['Insolvenz'].sum() > 0

    # Erstellung einer Serie von insolventen Unternehmen
    df_insolvent_series = aa[aa].index

    # Erstellung eines neuen DataFrames, der nur Unternehmen enthält, die nicht insolvent sind
    df_gruppe_ohne_Insolvenz = df_gruppe_mit_Insolvenz[~df_gruppe_mit_Insolvenz['Company_ID'].isin(df_insolvent_series)]

    # Aktualisierung des DataFrames df_gruppe_mit_Insolvenz, um nur insolvente Unternehmen zu enthalten
    df_gruppe_mit_Insolvenz = df_gruppe_mit_Insolvenz[df_gruppe_mit_Insolvenz['Company_ID'].isin(df_insolvent_series)]

    # Sortierung und Zurücksetzen des Index für beide DataFrames
    df_gruppe_mit_Insolvenz.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)
    df_gruppe_mit_Insolvenz.reset_index(drop=True, inplace=True)
    df_gruppe_ohne_Insolvenz.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)
    df_gruppe_ohne_Insolvenz.reset_index(drop=True, inplace=True)

    # Entfernen von Zeilen über der ersten Insolvenz für jedes insolvente Unternehmen
    mask = df_gruppe_mit_Insolvenz.groupby('Company_ID')['Insolvenz'].cumsum() == 2
    df_gruppe_mit_Insolvenz_cleaned = df_gruppe_mit_Insolvenz[mask]

    # Zusammenführen der beiden DataFrames
    df_merged = pd.concat([df_gruppe_mit_Insolvenz_cleaned, df_gruppe_ohne_Insolvenz])

    # Sortierung und Zurücksetzen des Index für den zusammengeführten DataFrame
    df_merged.sort_values(['Company_ID', 'Jahr'], ascending=[True, False], inplace=True)
    df_merged.reset_index(drop=True, inplace=True)

    # Start der Datenbereinigung
    # Entfernen von fehlenden Werten
    variablen_cleaning = ['Anlagevermoegen','Umlaufvermoegen', 'Bilanzsumme', 'Eigenkapital','kurzfristigeVerbindlichkeiten','JahresueberschussFehlbetrag']
    data = remove_missing(variablen_cleaning, df_merged)

    # Entfernen von negativen Werten
    variablen_cleaning = ['Bilanzsumme','Anlagenintensitaet','Umlaufintensitaet','STDR']
    data = remove_negative_values(variablen_cleaning, data)

    # Rückgabe des bereinigten DataFrames
    return data
