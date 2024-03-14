from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.forms import ModelForm

from motor_testing.models import InductionMotor, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest, PerformanceTest, \
    LockRotorTest


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
            if field == "unbalance_percentage":
                self.fields[field].widget.attrs["readonly"] = True

            self.fields[field].widget.attrs["class"] = "form-control resistance"
            self.fields[field].widget.attrs["id"] = field


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
    # file_format = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
    # file_1 = forms.FileField()
    # file_2 = forms.FileField()
    # file_3 = forms.FileField()
    # file_4 = forms.FileField()
    prefix = 'performance_determination_test'
    #
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
             if field == "report_date":
                self.fields[field].widget=forms.DateInput(attrs={'class': 'form-control col-8 datepicker','placeholder':'yyyy-mm-dd'})
             else:
                 self.fields[field].widget.attrs["class"] = "form-control"
 

    class Meta:
        model = PerformanceDeterminationTest
        fields = ['voltage', 'frequency', 'nominal_t','is_current_date', 'report_date']
        
        


class NoLoadTestForm(forms.ModelForm):
    prefix = 'no_load_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field == "reported_date":
                self.fields[field].widget=forms.DateInput(attrs={'class': 'form-control col-8 datepicker','placeholder':'yyyy-mm-dd'})

            else:
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


class LockRotorTestForm(forms.ModelForm):
    prefix = 'lock_rotor_test'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field == "reported_date":
                self.fields[field].widget=forms.DateInput(attrs={'class': 'form-control col-8 datepicker','placeholder':'yyyy-mm-dd'})
            else:
                self.fields[field].widget.attrs["class"] = "form-control"

    class Meta:
        model = LockRotorTest
        exclude = ('induction_motor',)


