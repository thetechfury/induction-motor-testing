from django.contrib import admin
from motor_testing.models import InductionMotor, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest
from django.contrib.admin.decorators import register


# Register your models here.


@register(InductionMotor)
class InductionMotorAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'created_on', 'updated_on', 'status', 'user')


@register(ElectricResistanceTest)
class ElectricResistanceTestAdmin(admin.ModelAdmin):
    list_display = (
    'induction_motor', 'resistance_ohm_1', 'resistance_ohm_2', 'resistance_ohm_3', 'ambient_temperature_C',
    'unbalance_percentage')


@register(TemperatureRiseTest)
class TemperatureRiseTestAdmin(admin.ModelAdmin):
    list_display = ('induction_motor', 'voltage', 'winding', 'frequency', 'de_bearing', 'nde_bearing')


@register(PerformanceDeterminationTest)
class PerformanceDeterminationTestAdmin(admin.ModelAdmin):
    list_display = ('induction_motor', 'voltage', 'frequency', 'nominal_t', 'load', 'current', 'slip', 'speed', 'efficiency', 'cos')


@register(NoLoadTest)
class NoLoadTestAdmin(admin.ModelAdmin):
    list_display = ('induction_motor', 'voltage', 'current', 'power', 'frequency', 'speed', 'direction_of_rotation')


@register(WithstandVoltageACTest)
class WithstandVoltageACTestAdmin(admin.ModelAdmin):
    list_display = ('induction_motor', 'description', 'voltage_kv', 'time_in_seconds')


@register(InsulationResistanceTest)
class InsulationResistanceTestAdmin(admin.ModelAdmin):
    list_display = ('induction_motor', 'description', 'voltage', 'insulation_resistance', 'time_in_seconds', 'ambient_temperature_C', 'humidity_percentage')
