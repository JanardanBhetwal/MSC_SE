# Generated by Django 2.1.7 on 2019-08-18 06:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        #('college', '0002_auto_20240707_2216'),
        ('thesis', '0004_remove_coordinator_programname'),
    ]

    operations = [
        migrations.AddField(
            model_name='coordinator',
            name='programName',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='college.Programme'),
        ),
    ]
