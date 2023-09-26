# Generated by Django 4.1.2 on 2023-01-30 14:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('group_representation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupsplit',
            name='file_name',
            field=models.CharField(default='test', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groupsplit',
            name='file_1',
            field=models.FileField(upload_to=''),
        ),
        migrations.AlterField(
            model_name='groupsplit',
            name='file_2',
            field=models.FileField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='groupsplit',
            name='file_3',
            field=models.FileField(blank=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='groupsplit',
            name='file_4',
            field=models.FileField(blank=True, upload_to=''),
        ),
    ]