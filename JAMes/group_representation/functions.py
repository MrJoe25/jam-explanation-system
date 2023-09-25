# Importe verschiedener Module und Bibliotheken
import csv
from numpy import datetime64, float64, int64, int32
import numpy as np
import pandas as pd
import re
import os
from os.path import exists
import sys
from pathlib import Path
from collections import Counter
import pandas as pd

# Funktion zur Zuweisung von Firmengrößen
def firmengroesse_zuweisen(data):
    """
    Generierung der Firmengroesse basierend auf §267 und §267a
    als Feature fuer das Aufsplitten des Datensatzes

    :param data: gecleanter Datensatz
    :return: Datensatz mit der Firmengroesse
    """
    # Definition der möglichen Firmengrößen
    groessen_list = ['kleinst', 'klein', 'mittel', 'gross']
    
    # Bedingungen für die verschiedenen Firmengrößen
    condition_list = [
        data['Bilanzsumme'] <= 350000, 
        (data['Bilanzsumme'] > 350000) & (data['Bilanzsumme'] <= 6000000),
        (data['Bilanzsumme'] > 6000000) & (data['Bilanzsumme'] <= 20000000), 
        data['Bilanzsumme'] > 20000000
    ]
    
    # Zuweisung der Firmengröße basierend auf der Bilanzsumme
    data['FIRMENGROESSE'] = np.select(condition_list, groessen_list)
    return data

# Funktion zum Aufteilen des DataFrames
def split_dataframe(data):
    """
    Splittet den gecleanten Datensatz in drei kleinere Datensaetze und speichert
    diesen sofern es Aenderungen gab.
    :param data: Gecleanter Dataframe
    """

    # Loop über alle einzigartigen Firmengrößen im DataFrame
    for firmengroesse in data['FIRMENGROESSE'].unique():
        
        # Erstellen eines DataFrames für jede einzigartige Firmengröße
        dataframe = data[data['FIRMENGROESSE'] == firmengroesse].copy()
        
        return dataframe
