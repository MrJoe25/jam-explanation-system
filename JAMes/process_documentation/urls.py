from django.urls import path  # Importiert die 'path'-Funktion aus dem Django URL-Modul
from . import views  # Importiert alle Views aus dem aktuellen Verzeichnis (.)

urlpatterns = [  # Erstellt eine Liste von URL-Mustern, die in diesem Fall nur ein Element enthält
    path('', views.process_documentation, name='process_documentation'),  # Erstellt ein URL-Muster, das auf die 'process_documentation'-Funktion in den Views zeigt. Wenn die Basis-URL (d. h., '') aufgerufen wird, wird diese Funktion ausgeführt.
]
