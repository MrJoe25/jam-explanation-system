from django.urls import path  # Importiert die 'path' Funktion aus Django's URL-Modul
from . import views  # Importiert alle View-Funktionen aus dem 'views' Modul des aktuellen Pakets

urlpatterns = [  # Definiert eine Liste von URL-Mustern für diese Django-App
    # path('', views.xgscores, name='xgscores'),
    path('', views.xgexplain, name='xgexplain'),  # Root-URL, die zur 'xgexplain' View-Funktion weiterleitet
    # path('download_report/<str:filename>/', views.download_report, name='download_report')
]
