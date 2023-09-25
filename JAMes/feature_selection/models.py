# Importieren der notwendigen Django-Module
from django.db import models
import os  # Betriebssystem-Funktionalitäten, hier verwendet für Dateinamen

# Definition des Modells Cleaned_File
class Cleaned_File(models.Model):
    # Zeichenkettenfelder für Superuser und Benutzer, sowohl 'null' als auch 'blank' sind erlaubt
    superuser = models.CharField(max_length=100, null=True, blank=True)
    user = models.CharField(max_length=100, null=True, blank=True)
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Dateifeld für die Datei
    file = models.FileField()

    # String-Repräsentation des Modells
    def __str__(self):
        return f'Uploaded {self.uploaded_at}, CSV File {self.file}'
    
    # Methode zur Rückgabe des Basisnamens der Datei
    def filename(self):
        return os.path.basename(self.file.name)

# Definition des Modells Featureselection
class Featureselection(models.Model):
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Boolesche Felder für verschiedene Merkmale
    equity_ratio = models.BooleanField()
    working_capital_ratio = models.BooleanField()
    return_on_total_assets = models.BooleanField()
    return_on_equity = models.BooleanField()
    asset_coverage_ratio = models.BooleanField()
    second_degree_liquidity = models.BooleanField()
    short_term_debt_ratio = models.BooleanField()

# Definition des Modells Feature_Table
class Feature_Table(models.Model):
    # Zeichenkettenfelder für Superuser und Benutzer, sowohl 'null' als auch 'blank' sind erlaubt
    superuser = models.CharField(max_length=100, null=True, blank=True)
    user = models.CharField(max_length=100, null=True, blank=True)
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Dateifeld für die Datei
    file = models.FileField()

    # String-Repräsentation des Modells
    def __str__(self):
        return f'Uploaded {self.uploaded_at}, CSV File {self.file}'
        
    # Methode zur Rückgabe des Basisnamens der Datei
    def filename(self):
        return os.path.basename(self.file.name)
