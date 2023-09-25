# Importieren der AppConfig-Klasse aus dem Django-Modul
from django.apps import AppConfig

# Definition der Konfigurationsklasse für die Django-App "group_preprocessing"
class GroupPreprocessingConfig(AppConfig):
    # Festlegen des Standard-Autofeld-Typs für die Modelle dieser App
    default_auto_field = 'django.db.models.BigAutoField'

    # Name der App, der zur Identifikation innerhalb des Django-Projekts verwendet wird
    name = 'group_preprocessing'
