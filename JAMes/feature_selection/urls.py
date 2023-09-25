from django.urls import path  # Importiert die 'path'-Funktion aus dem Django-Modul für URL-Mapping
from . import views  # Importiert alle Views aus dem aktuellen Verzeichnis

# Liste der URL-Mappings für diese Django-App
urlpatterns = [
    path('', views.featureselection, name='featureselection'),  # Leitet die Basis-URL an die 'featureselection'-View um
    path('datacleaning/', views.datacleaning, name='datacleaning'),  # Leitet '/datacleaning/' an die 'datacleaning'-View um
    path('cleaned_data/', views.cleaned_data, name='cleaned_data'),  # Leitet '/cleaned_data/' an die 'cleaned_data'-View um
    path('featurestat/', views.featurestat, name='featurestat'),  # Leitet '/featurestat/' an die 'featurestat'-View um
]
