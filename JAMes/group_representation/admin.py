# Importiert das admin-Modul von Django
from django.contrib import admin

# Importiert alle Modelle aus dem aktuellen Verzeichnis (.models)
from .models import *

# Registriert das Modell GroupSplit im Django-Admin-Interface
admin.site.register(GroupSplit)
