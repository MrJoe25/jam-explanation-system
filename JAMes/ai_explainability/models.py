# Importieren der "models"-Klasse von Django für Datenbankmodelle
from django.db import models

# Importieren des eingebauten "User"-Modells von Django
from django.contrib.auth.models import User

# Definition des "Report"-Modells, das von "models.Model" erbt
class Report(models.Model):
    # Erstellen eines Fremdschlüssel-Felds "user", das auf das eingebaute "User"-Modell verweist
    # "on_delete=models.CASCADE" bedeutet, dass bei Löschung eines User-Objekts auch alle zugehörigen Report-Objekte gelöscht werden
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Erstellen eines CharField "file_name" für den Dateinamen, maximale Länge ist 255 Zeichen
    file_name = models.CharField(max_length=255)
    
    # Erstellen eines FileField "report_file" für die Datei
    # Dateien werden im aktuellen Verzeichnis gespeichert
    # "null=True, blank=True" bedeutet, dass dieses Feld optional sein kann
    report_file = models.FileField(upload_to='.', null=True, blank=True)
    
    # Erstellen eines DateTimeField "created_at", das automatisch den Zeitpunkt der Erstellung des Objekts speichert
    created_at = models.DateTimeField(auto_now_add=True)

    # Überschreiben der save()-Methode des Modells
    def save(self, *args, **kwargs):
        # Wenn ein "report_file" vorhanden ist, wird der Dateiname in "file_name" gespeichert
        if self.report_file:
            self.file_name = self.report_file.name
        # Aufruf der ursprünglichen save()-Methode der Elternklasse
        super().save(*args, **kwargs)
