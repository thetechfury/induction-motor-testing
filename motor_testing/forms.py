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
        exclude = ('motor', 'page_number', 'status',)
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
        self.fields["search"].widget.attrs["class"] = "datatable-input form-control"
        self.fields["search"].widget.attrs["placeholder"] = "Search..."
        self.fields["search"].widget.attrs["type"] = "search"


class ElectricResistanceTestForm(forms.ModelForm):
    prefix = 'electric_resistance_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

    class Meta:
        model = ElectricResistanceTest
        exclude = ('induction_motor',)


class TemperatureRiseTestForm(forms.ModelForm):
    prefix = 'temperature_rise_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

    class Meta:
        model = TemperatureRiseTest
        exclude = ('induction_motor',)


class PerformanceDeterminationTestForm(forms.ModelForm):
    file_1 = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    file_2 = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    file_3 = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    file_4 = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': False}), required=False)
    prefix = 'performance_determination_test'

    class Meta:
        model = PerformanceDeterminationTest
        fields = ['voltage', 'frequency', 'nominal_t', 'file_1', 'file_2', 'file_3', 'file_4']
        widgets = {
            'voltage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Voltage (V)'}),
            'frequency': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Frequency (Hz)'}),
            'nominal_t': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nominal T (N.m)'}),
            'file_1': forms.FileInput(attrs={'class': 'form-control'}),
            'file_2': forms.FileInput(attrs={'class': 'form-control'}),
            'file_3': forms.FileInput(attrs={'class': 'form-control'}),
            'file_4': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'voltage': 'Voltage (V)',
            'frequency': 'Frequency (Hz)',
            'nominal_t': 'Nominal T (N.m)',
            'file_1': 'File 1 with Load at 25%',
            'file_2': 'File 2 with Load at 50%',
            'file_3': 'File 3 with Load at 75%',
            'file_4': 'File 4 with Load at 100%',
        }

    def clean_file_1(self):
        file_1 = self.cleaned_data.get('file_1')
        if file_1:
            if not file_1.name.endswith('.xlsx'):
                raise forms.ValidationError("Only .xlsx files are allowed.")
        return file_1

    def clean_file_2(self):
        file_2 = self.cleaned_data.get('file_2')
        if file_2:
            if not file_2.name.endswith('.xlsx'):
                raise forms.ValidationError("Only .xlsx files are allowed.")
        return file_2

    def clean_file_3(self):
        file_3 = self.cleaned_data.get('file_3')
        if file_3:
            if not file_3.name.endswith('.xlsx'):
                raise forms.ValidationError("Only .xlsx files are allowed.")
        return file_3

    def clean_file_4(self):
        file_4 = self.cleaned_data.get('file_4')
        if file_4:
            if not file_4.name.endswith('.xlsx'):
                raise forms.ValidationError("Only .xlsx files are allowed.")
        return file_4


class NoLoadTestForm(forms.ModelForm):
    prefix = 'no_load_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

    class Meta:
        model = NoLoadTest
        exclude = ('induction_motor',)


class WithstandVoltageACTestForm(forms.ModelForm):
    prefix = 'withstand_voltage_ac_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

    class Meta:
        model = WithstandVoltageACTest
        exclude = ('induction_motor',)


class InsulationResistanceTestForm(forms.ModelForm):
    prefix = 'insulation_resistance_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs["class"] = "form-control"

    class Meta:
        model = InsulationResistanceTest
        exclude = ('induction_motor',)
