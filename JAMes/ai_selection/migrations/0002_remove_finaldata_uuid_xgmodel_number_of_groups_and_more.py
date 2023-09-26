# Generated by Django 4.1.2 on 2023-03-19 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ai_selection', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='finaldata',
            name='uuid',
        ),
        migrations.AddField(
            model_name='xgmodel',
            name='number_of_groups',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='finaldata',
            name='company_id',
            field=models.FileField(upload_to='final_table/'),
        ),
    ]