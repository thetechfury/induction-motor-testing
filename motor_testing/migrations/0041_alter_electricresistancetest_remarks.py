# Generated by Django 5.0.2 on 2024-05-14 09:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("motor_testing", "0040_alter_noloadtest_direction_of_rotation")]

    operations = [
        migrations.AlterField(
            model_name="electricresistancetest",
            name="remarks",
            field=models.TextField(blank=True, max_length=250, null=True),
        )
    ]
