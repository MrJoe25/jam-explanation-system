# Importierung von notwendigen Modulen aus Django
from django import forms
from .models import Featureselection

# Definition der Form-Klasse für die Feature-Auswahl
class FeatureselectionForm(forms.Form):
  # Erstellung von Boolean-Feldern für verschiedene Finanzkennzahlen, alle optional
  equity_ratio = forms.BooleanField(required=False)
  working_capital_ratio = forms.BooleanField(required=False)
  return_on_total_assets = forms.BooleanField(required=False)
  return_on_equity = forms.BooleanField(required=False)
  asset_coverage_ratio = forms.BooleanField(required=False)
  second_degree_liquidity = forms.BooleanField(required=False)
  short_term_debt_ratio = forms.BooleanField(required=False)
  
  # Definition der 'save'-Methode zum Speichern der ausgewählten Features in der Datenbank
  def save(self):
    # Reinigung der Formulardaten
    data = self.cleaned_data
    
    # Erstellung eines neuen Featureselection-Objekts und Speicherung in der Datenbank
    featureselection = Featureselection.objects.create(
      equity_ratio=data['equity_ratio'],
      working_capital_ratio=data['working_capital_ratio'],
      return_on_total_assets=data['return_on_total_assets'],
      return_on_equity=data['return_on_equity'],
      asset_coverage_ratio=data['asset_coverage_ratio'],
      second_degree_liquidity=data['second_degree_liquidity'],
      short_term_debt_ratio=data['short_term_debt_ratio'],
    )
    
    # Speichern des neuen Objekts in der Datenbank
    featureselection.save()
