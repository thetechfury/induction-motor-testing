from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

from motor_testing.models import InductionMotor, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest, PerformanceTest


class UserLoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["password"].widget.attrs["class"] = "form-control"


class InitialForm(ModelForm):
    class Meta:
        model = InductionMotor
        exclude = ('user',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"


class PerformanceTestForm(ModelForm):
    class Meta:
        model = PerformanceTest
        exclude = ('motor', 'page_number', 'status', )
        readonly_fields = ['test_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['test_type'].widget.attrs["class"] = "form-control"
        self.fields['test_type'].widget.attrs['disabled'] = True
        # Set widgets for routine, type, and special fields
        self.fields['routine'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        self.fields['type'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        self.fields['special'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})


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
        fields = ['resistance_ohm_1', 'resistance_ohm_2', 'resistance_ohm_3', 'ambient_temperature_C', 'unbalance_percentage']
        widgets = {
            'resistance_ohm_1': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Resistance Value 1 (mOhms)'}),
            'resistance_ohm_2': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Resistance Value 2 (mOhms)'}),
            'resistance_ohm_3': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Resistance Value 3 (mOhms)'}),
            'ambient_temperature_C': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ambient Temperature (Celsius)'}),
            'unbalance_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Unbalance Percentage (%)'}),
        }


class TemperatureRiseTestForm(forms.ModelForm):
    prefix = 'temperature_rise_test'

    class Meta:
        model = TemperatureRiseTest
        fields = ['voltage', 'winding', 'frequency', 'de_bearing', 'nde_bearing']
        widgets = {
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Voltage (V)'}),
            'winding': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Winding (V)'}),
            'frequency': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Frequency (Hz)'}),
            'de_bearing': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'De-Bearing (V)'}),
            'nde_bearing': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'NDe-Bearing (V)'}),
        }


class PerformanceDeterminationTestForm(forms.ModelForm):
    prefix = 'performance_determination_test'

    class Meta:
        model = PerformanceDeterminationTest
        fields = ['voltage', 'frequency', 'nominal_t', 'load', 'current', 'slip', 'speed', 'efficiency', 'cos']
        widgets = {
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Voltage (V)'}),
            'frequency': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Frequency (Hz)'}),
            'nominal_t': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nominal T (N.m)'}),
            'load': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Load (%)'}),
            'current': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current (A)'}),
            'slip': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Slip (%)'}),
            'speed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Speed (rpm)'}),
            'efficiency': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Efficiency (%)'}),
            'cos': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'COS Ø'}),
        }
        labels = {
            'slip': 'Slip (%)',
            'speed': 'Speed (rpm)',
            'efficiency': 'Efficiency (%)',
            'cos': 'COS Ø',
            'frequency': 'Frequency (Hz)',
            'current': 'Current (A)',
            'voltage': 'Voltage (V)',
            'nominal_t': 'Nominal T (N.m)',
            'load': 'Load (%)',
        }


class NoLoadTestForm(forms.ModelForm):
    prefix = 'no_load_test'

    class Meta:
        model = NoLoadTest
        fields = ['voltage', 'current', 'power', 'frequency', 'speed', 'direction_of_rotation']
        widgets = {
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Voltage (V)'}),
            'current': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Current (A)'}),
            'power': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Power (W)'}),
            'frequency': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Frequency (Hz)'}),
            'speed': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Speed (rpm)'}),
            'direction_of_rotation': forms.Select(attrs={'class': 'form-select', 'placeholder': 'Direction of Rotation'}),
        }
        labels = {
            'voltage': 'Voltage (V)',
            'current': 'Current (A)',
            'power': 'Power (W)',
            'frequency': 'Frequency (Hz)',
            'speed': 'Speed (rpm)',
            'direction_of_rotation': 'Direction of Rotation',
        }


class WithstandVoltageACTestForm(forms.ModelForm):
    prefix = 'withstand_voltage_ac_test'

    class Meta:
        model = WithstandVoltageACTest
        fields = ['description', 'voltage_kv', 'time_in_seconds']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'voltage_kv': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Voltage (V)'}),
            'time_in_seconds': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Time (s)'}),
        }


class InsulationResistanceTestForm(forms.ModelForm):
    prefix = 'insulation_resistance_test'

    class Meta:
        model = InsulationResistanceTest
        fields = ['description', 'voltage', 'insulation_resistance', 'time_in_seconds', 'ambient_temperature_C', 'humidity_percentage']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Voltage (V)'}),
            'insulation_resistance': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Insulation Resistance (MΩ)'}),
            'time_in_seconds': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Time (s)'}),
            'ambient_temperature_C': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ambient Temperature (C)'}),
            'humidity_percentage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Humidity (%)'}),
        }
