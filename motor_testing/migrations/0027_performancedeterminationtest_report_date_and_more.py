# Generated by Django 5.0.2 on 2024-03-13 05:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("motor_testing", "0026_lockrotortest__report_date")]

    operations = [
        migrations.AddField(
            model_name="performancedeterminationtest",
            name="report_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="performancedeterminationtest",
            name="table_name",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
