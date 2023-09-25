# Importiert die AppConfig-Klasse aus dem django.apps-Modul
from django.apps import AppConfig

# Definiert eine neue Konfigurationsklasse für die App, die von AppConfig erbt
class GroupRepresentationConfig(AppConfig):
    # Setzt den Standard-Auto-Feldtyp für Modelle in dieser App
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Legt den Namen der App fest
    name = 'group_representation'
