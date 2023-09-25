from django.urls import path  # Importiert die 'path' Funktion aus Django's URL-Modul
from bankrupt_company_search.views import search_company, filter_company, filter_bankrupt, filter_predicted_bankrupt, filter_bankrupt_and_predicted, save_predictions_to_csv  
# Importiert spezifische View-Funktionen aus dem 'views' Modul der Anwendung 'bankrupt_company_search'

app_name = 'bankrupt_company_search'  # Gibt dem URL-Muster einen Namespace, nützlich für die Unterscheidung von URLs in verschiedenen Apps

urlpatterns = [  # Eine Liste der URL-Muster, die diese App verwaltet
    path('', search_company, name='search_company'),  # Root-URL, die zur 'search_company' View-Funktion leitet
    path('filter_company/', filter_company, name='filter_company'),  # URL für die 'filter_company' View-Funktion
    path('filter_bankrupt/', filter_bankrupt, name='filter_bankrupt'),  # URL für die 'filter_bankrupt' View-Funktion
    path('filter_predicted_bankrupt', filter_predicted_bankrupt, name='filter_predicted_bankrupt'),  # URL für die 'filter_predicted_bankrupt' View-Funktion
    path('filter_bankrupt_and_predicted', filter_bankrupt_and_predicted, name='filter_bankrupt_and_predicted'),  # URL für die 'filter_bankrupt_and_predicted' View-Funktion
    path('save_predictions_to_csv', save_predictions_to_csv, name='save_predictions_to_csv'),  # URL für die 'save_predictions_to_csv' View-Funktion
]
