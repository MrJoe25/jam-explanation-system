from django.apps import AppConfig  # Importieren der AppConfig-Klasse aus dem Django-Framework

# Definition einer neuen Klasse UsermanagementConfig, die von AppConfig erbt
class UsermanagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Standard-Autofeldtyp für die Django-Datenbank ist BigAutoField
    name = 'usermanagement'  # Der Name der App wird auf 'usermanagement' gesetzt

    # Definition einer Methode namens ready
    def ready(self):
        import usermanagement.signals  # Importiert die Signale aus dem usermanagement-Modul, sobald die App bereit ist
