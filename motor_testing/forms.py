from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

from motor_testing.models import InductionMotor, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest


class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["password"].widget.attrs["class"] = "form-control"


class MotorInductionForm(ModelForm):
    class Meta:
        model = InductionMotor
        fields = '__all__'


class SearchForm(forms.Form):
    search = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["search"].widget.attrs["class"] = "datatable-input"
        self.fields["search"].widget.attrs["placeholder"] = "Search..."
        self.fields["search"].widget.attrs["type"] = "search"


class ElectricResistanceTestForm(forms.ModelForm):
    prefix = 'electric_resistance_test'
    class Meta:
        model = ElectricResistanceTest
        fields = '__all__'


class TemperatureRiseTestForm(forms.ModelForm):
    prefix = 'temperature_rise_test'
    class Meta:
        model = TemperatureRiseTest
        fields = '__all__'


class PerformanceDeterminationTestForm(forms.ModelForm):
    prefix = 'performance_determination_test'
    class Meta:
        model = PerformanceDeterminationTest
        fields = '__all__'


class NoLoadTestForm(forms.ModelForm):
    prefix = 'no_load_test'
    class Meta:
        model = NoLoadTest
        fields = '__all__'


class WithstandVoltageACTestForm(forms.ModelForm):
    prefix = 'withstand_voltage_ac_test'
    class Meta:
        model = WithstandVoltageACTest
        fields = '__all__'


class InsulationResistanceTestForm(forms.ModelForm):
    prefix = 'insulation_resistance_test'
    class Meta:
        model = InsulationResistanceTest
        fields = '__all__'

