# Importieren der notwendigen Django-Module
from django.db import models
from django import forms  # Formularfunktionalitäten, aber nicht im weiteren Code verwendet
from django.contrib.auth.models import User  # Authentifizierungsmodell, aber nicht im weiteren Code verwendet

# Definition des Modells 'Group'
class Group(models.Model):
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Zeichenkettenfeld für den Dateinamen mit einer maximalen Länge von 255 Zeichen
    file_name = models.CharField(max_length=255)
    # Zeichenkettenfeld für den Gruppennamen mit einer maximalen Länge von 255 Zeichen
    group_name = models.CharField(max_length=255)
    # Integer-Feld für die Anzahl der Gruppen
    number_of_groups = models.IntegerField()
    # Integer-Feld für die Auswahl einer Gruppe
    group_choice = models.IntegerField()
    # Integer-Feld für die untere Grenze
    lower_bound = models.IntegerField()
    # Integer-Feld für die obere Grenze
    upper_bound = models.IntegerField()
    
    # String-Repräsentation des Modells, die Gruppenname, Gruppenauswahl und Dateinamen zurückgibt
    def __str__(self):
        return self.group_name + ' ' + str(self.group_choice) + ' ' + self.file_name
