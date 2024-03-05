# Generated by Django 5.0.2 on 2024-03-05 06:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("motor_testing", "0009_performancedeterminationtest_performance_100_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lockrotortest",
            name="current",
        ),
        migrations.RemoveField(
            model_name="lockrotortest",
            name="frequency",
        ),
        migrations.RemoveField(
            model_name="lockrotortest",
            name="power",
        ),
        migrations.RemoveField(
            model_name="lockrotortest",
            name="voltage",
        ),
        migrations.RemoveField(
            model_name="performancedeterminationtest",
            name="performance_100",
        ),
        migrations.RemoveField(
            model_name="performancedeterminationtest",
            name="performance_25",
        ),
        migrations.RemoveField(
            model_name="performancedeterminationtest",
            name="performance_50",
        ),
        migrations.RemoveField(
            model_name="performancedeterminationtest",
            name="performance_75",
        ),
        migrations.AddField(
            model_name="performancedeterminationtest",
            name="is_current_date",
            field=models.BooleanField(default=False, verbose_name="Use current date"),
        ),
        migrations.AddField(
            model_name="performancedeterminationtest",
            name="test_date",
            field=models.DateField(blank=True, null=True, verbose_name="Test Date"),
        ),
        migrations.AlterField(
            model_name="performancetest",
            name="test_type",
            field=models.CharField(
                choices=[
                    ("electric_resistance_test", "Electric Resistance Test"),
                    ("temperature_rise_test", "Temperature Rise Test"),
                    (
                        "performance_determination_test",
                        "Performance Determination Test",
                    ),
                    ("no_load_test", "No Load Test"),
                    ("withstand_voltage_ac_test", "Withstand Voltage AC Test"),
                    ("insulation_resistance_test", "Insulation Resistance Test"),
                    ("lock_roter_test", "LOCK ROTOR TEST"),
                ],
                max_length=50,
            ),
        ),
    ]
