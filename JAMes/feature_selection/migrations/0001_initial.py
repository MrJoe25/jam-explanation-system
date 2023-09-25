# Generated by Django 4.0.6 on 2023-01-09 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Featureselection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('equity_ratio', models.BooleanField()),
                ('working_capital_ratio', models.BooleanField()),
                ('return_on_total_assets', models.BooleanField()),
                ('return_on_equity', models.BooleanField()),
                ('asset_coverage_ratio', models.BooleanField()),
                ('second_degree_liquidity', models.BooleanField()),
                ('short_term_debt_ratio', models.BooleanField()),
            ],
        ),
    ]
