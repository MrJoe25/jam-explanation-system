# Importieren des admin-Moduls aus dem Django-Framework
from django.contrib import admin
# Importieren aller Modelle aus der aktuellen Modelldatei (models.py)
from .models import *

# Registrierung der Modelle im Django-Admin-Bereich
# Damit werden die Modelle im Admin-Bereich sichtbar und können dort verwaltet werden

# Registrierung des Modells für gereinigte Dateien
admin.site.register(Cleaned_File)

# Registrierung des Modells für die Feature-Auswahl
admin.site.register(Featureselection)

# Registrierung des Modells für die Feature-Tabelle
admin.site.register(Feature_Table)
