from . import views  # Importiert alle Views aus dem aktuellen Verzeichnis
from django.urls import path  # Importiert das 'path' Modul aus den Django-URLs

app_name = 'usermanagement'  # Definiert den Namen der App, um sie in Templates und anderen Apps leichter referenzieren zu können

urlpatterns = [  # Eine Liste von URL-Mustern, die dieser App zugeordnet sind
    path('personal_dashboard', views.personal_dashboard, name='personal_dashboard'),
    # Ein URL-Muster, das die URL 'personal_dashboard' mit der View-Funktion 'personal_dashboard' in 'views' verbindet.
    # Der Name 'personal_dashboard' wird als Referenz für diese spezielle URL verwendet.
]
