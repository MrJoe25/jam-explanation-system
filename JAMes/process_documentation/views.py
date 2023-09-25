# Importiere die "render"-Funktion aus dem "django.shortcuts"-Modul
from django.shortcuts import render

# Definiere die Funktion "process_documentation", die einen HTTP-Request als Parameter nimmt
def process_documentation(request):
    # Verwende die "render"-Funktion, um die HTML-Vorlage "process_documentation.html" zu rendern und als HTTP-Response zurückzugeben
    return render(request, 'process_documentation.html')
