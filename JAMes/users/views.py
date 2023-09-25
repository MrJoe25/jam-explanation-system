# Importieren der "render"-Funktion von Django, die das Rendern von HTML-Templates ermöglicht
from django.shortcuts import render

# Importieren der HttpResponse-Klasse von Django, um HTTP-Antworten zu erzeugen
from django.http import HttpResponse

# Importieren generischer Django-Klassenansichten für Listen- und Detailansichten
from django.views.generic import ListView, DetailView

# Ansichtsfunktion für die Homepage
def home(request):
    # Verwenden der "render"-Funktion, um das "homepage.html"-Template zu rendern und als HttpResponse zurückzugeben
    return render(request, 'users/homepage.html')  # Der Kontext "context" wurde im Originalcode auskommentiert und ist hier daher nicht enthalten

# Ansichtsfunktion für die About-Seite
def about(request):
    # Verwenden der "render"-Funktion, um das "about.html"-Template zu rendern
    # Zusätzlich wird ein Dictionary mit dem Schlüssel "title" und dem Wert "About" als Kontext übergeben
    return render(request, 'users/about.html', {'title': 'About'})
