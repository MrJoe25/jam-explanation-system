# Importieren der notwendigen Bibliotheken und Module
from django.db import models
from django.core.files.base import ContentFile
import pandas as pd
import xgboost as xgb
import pickle

# Erstellen des Models FinalData
class FinalData(models.Model):
    # Datetime-Feld, das automatisch den Zeitpunkt der Erstellung des Datensatzes speichert
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # Zeichenkettenfelder zur Speicherung des Superusers und des normalen Benutzers
    superuser = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    # Zeichenkettenfelder für den Dateinamen, den Gruppennamen und die KI-Methode
    file_name = models.CharField(max_length=255)
    group_name = models.CharField(max_length=255)
    ai_method = models.CharField(max_length=255)
    # Zeichenkettenfeld für die Bayesian-Optimierung, Standardwert ist 'no'
    bayesian_optimization = models.CharField(max_length=255, default='no')
    # Zeichenkettenfeld für die Aufteilung von Trainings-, Test- und Validierungsdatensätzen
    train_test_validation_split = models.CharField(max_length=255)
    # Optionales Zeichenkettenfeld für die Sampling-Methode
    sampling_technique = models.CharField(max_length=255, blank=True, null=True)
    # Dateifelder für die Speicherung von Trainings-, Test- und Validierungsdatensätzen sowie der Unternehmens-ID
    train_set = models.FileField(upload_to='final_table/')
    test_set = models.FileField(upload_to='final_table/')
    company_id = models.FileField(upload_to='final_table/')
    validation_set = models.FileField(upload_to='final_table/', null=True, blank=True)
    
    # String-Repräsentation des Modells
    def __str__(self):
        return f'Uploaded {self.uploaded_at}, User {self.user}, Group name {self.group_name}, Sampling technique {self.sampling_technique}, Split{self.train_test_validation_split}'

# Erstellen des Models XGModel
class XGModel(models.Model):
    # Ähnliche Felder wie im Modell FinalData, aber für das XGBoost-Modell
    uploaded_at = models.DateTimeField(auto_now_add=True)
    superuser = models.CharField(max_length=100)
    user = models.CharField(max_length=100)
    file_name = models.CharField(max_length=100)
    number_of_groups = models.IntegerField()
    group_name = models.CharField(max_length=100)
    ai_method = models.CharField(max_length=100)
    train_test_validation_split = models.CharField(max_length=100)
    sampling_technique = models.CharField(max_length=100, blank=True, null=True)
    bayesian_optimization = models.CharField(max_length=255, default='no')
    # Dateifelder für das Modell und die Trainings-/Testdatensätze
    model_file = models.FileField(upload_to='xg_model/')
    train_x_set = models.FileField(upload_to='xg_sets/')
    train_y_set = models.FileField(upload_to='xg_sets/')
    test_x_set = models.FileField(upload_to='xg_sets/')
    test_y_set = models.FileField(upload_to='xg_sets/')
    # Textfelder für die besten Hyperparameter und die Versuchsdaten
    best_params = models.TextField(blank=True, null=True)
    trials = models.TextField(blank=True, null=True)
    
    # String-Repräsentation des Modells
    def __str__(self):
        return f'Uploaded {self.uploaded_at}, User {self.user}, Group name {self.group_name}, Model File {self.model_file}'
