# Generated by Django 5.0.2 on 2024-03-13 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motor_testing', '0029_alter_performancetestparameters_slip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='performancetestparameters',
            name='cos',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=4, null=True),
        ),
        migrations.AlterField(
            model_name='performancetestparameters',
            name='efficiency',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
        migrations.AlterField(
            model_name='performancetestparameters',
            name='speed',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True),
        ),
    ]
