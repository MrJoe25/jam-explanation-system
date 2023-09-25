# Importieren des 'path'-Moduls von Django zur Erstellung von URL-Mustern
from django.urls import path
# Importieren aller Ansichten aus dem aktuellen Verzeichnis
from .views import *

# Definition der URL-Muster für die Anwendung
urlpatterns = [
    # URL-Muster für die Gruppenverarbeitungsansicht
    path('group_processing/', group_processing, name='group_processing'),
    # URL-Muster für die Vorsegmentierungsansicht
    path('presegmentation/', presegmentation, name='presegmentation'),
    # URL-Muster für die Segmentierungsansicht
    path('segmentation/', segmentation, name='segmentation'),
    # URL-Muster für die Ansicht zum Löschen von Gruppen
    path('delete_group/', delete_group, name='delete_group')
]
