# Importieren der Django-Formularbibliothek
from django import forms
# Importieren aller Modelle und Ansichten aus dem aktuellen Verzeichnis
from .models import *
from .views import *

# Definition der Klasse für das Formular
class GroupForm(forms.Form):
    # Verborgenes Textfeld für den Dateinamen
    file = forms.CharField(widget=forms.HiddenInput())
    # Auswahlmenü für die Gruppenauswahl mit dynamischen Auswahlmöglichkeiten
    group_choice = forms.ChoiceField(choices=[], widget=forms.Select(attrs={'class': 'form-control border border-primary rounded-pill'}))
    # Texteingabefeld für den Gruppennamen
    group_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control border border-primary rounded-pill'}))
    # Zahlenfeld für die untere Grenze
    lower_bound = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control border border-primary rounded-pill'}))
    # Zahlenfeld für die obere Grenze
    upper_bound = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'form-control border border-primary rounded-pill'}))

    # Methode zur Überprüfung der Gültigkeit der Gruppenauswahl
    def clean_group_choice(self):
        # Abrufen der bereinigten Daten für die Gruppenauswahl
        group_choice = self.cleaned_data['group_choice']
        # Abrufen der bereinigten Daten für die Datei
        file = self.cleaned_data['file']
        # Überprüfen, ob bereits eine Gruppe mit der gleichen Gruppenauswahl für diese Datei existiert
        if Group.objects.filter(file_name=file, group_choice=group_choice).exists():
            # Wenn ja, einen Validierungsfehler auslösen
            raise forms.ValidationError("Group choice already exists for this file.")
        # Rückgabe der bereinigten Gruppenauswahl
        return group_choice
