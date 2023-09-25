# Importieren des models-Moduls aus dem Django-Framework
from django.db import models

# Definition des Modells 'CSVFile'
class CSVFile(models.Model):
    # Zeichenkettenfeld für den Superuser mit maximaler Länge von 100 Zeichen. Kann null sein und leer bleiben
    superuser = models.CharField(max_length=100, null=True, blank=True)
    # Zeichenkettenfeld für den Benutzer mit maximaler Länge von 100 Zeichen. Kann null sein und leer bleiben
    user = models.CharField(max_length=100, null=True, blank=True)
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Dateifeld zum Speichern der CSV-Datei. Das Upload-Verzeichnis ist leer, was den MEDIA_ROOT verwendet
    file = models.FileField(upload_to='')
    
    # String-Repräsentation des Modells. Gibt den Zeitpunkt des Hochladens und die Datei zurück
    def __str__(self):
        return f'Uploaded {self.uploaded_at}, CSV File {self.file}'
