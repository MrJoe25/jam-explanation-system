# Importieren der notwendigen Django-Module
from django.core.files.base import ContentFile  # Für Dateiverwaltung, wird aber nicht im weiteren Code verwendet
from django.db import models  # Für die Modellierung der Datenbank

# Definition des Modells 'GroupSplit'
class GroupSplit(models.Model):
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Zeichenkettenfeld für den Superuser mit maximaler Länge von 100 Zeichen. Kann null sein und leer bleiben
    superuser = models.CharField(max_length=100, null=True, blank=True)
    # Zeichenkettenfeld für den Benutzer mit maximaler Länge von 100 Zeichen. Kann null sein und leer bleiben
    user = models.CharField(max_length=100, null=True, blank=True)
    # Zeichenkettenfeld für den Dateinamen mit einer maximalen Länge von 255 Zeichen
    file_name = models.CharField(max_length=255)
    # Zeichenkettenfeld für den Gruppennamen mit einer maximalen Länge von 255 Zeichen
    group_name = models.CharField(max_length=255)
    # Dateifeld zum Speichern der Datei, mit einem spezifischen Upload-Verzeichnis 'group_split/'
    file = models.FileField(upload_to='group_split/')
    # Zeichenkettenfeld für die KI-Methode mit einer maximalen Länge von 100 Zeichen. Kann leer bleiben
    ai_method = models.CharField(max_length=100, blank=True)
    # Zeichenkettenfeld für die Aufteilung von Trainings-, Test- und Validierungsdaten. Max Länge ist 100, kann leer bleiben
    train_test_validation_split = models.CharField(max_length=100, blank=True)
    # Zeichenkettenfeld für die Sampling-Technik mit einer maximalen Länge von 100 Zeichen. Kann null sein und leer bleiben
    sampling_technique = models.CharField(max_length=100, blank=True, null=True)
    # Zeichenkettenfeld für die Bayes'sche Optimierung mit einer maximalen Länge von 100 Zeichen. Standardwert ist 'no'
    bayesian_optimization = models.CharField(max_length=100, blank=True, default='no')
    
    # String-Repräsentation des Modells. Gibt den Zeitpunkt des Hochladens, den Benutzer und den Gruppennamen zurück
    def __str__(self):
        return f'Uploaded {self.uploaded_at}, User {self.user}, Group name {self.group_name}'
