# Generated by Django 5.0.2 on 2024-03-12 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("motor_testing", "0025_noloadtest__report_date")]

    operations = [
        migrations.AddField(
            model_name="lockrotortest",
            name="_report_date",
            field=models.DateField(blank=True, null=True),
        )
    ]
