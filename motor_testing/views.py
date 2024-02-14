from django.shortcuts import render
from django.views.generic import ListView, View
from motor_testing.models import InductionMotor

from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm
)


class InductionMotorListingsView(ListView):
    model = InductionMotor
    queryset = InductionMotor.objects.all().order_by("-updated_on")
    template_name = "listings.html"
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        context['form'] = InitialForm
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(serial_number__icontains=search_query)
        return queryset


class TestsView(View):
    def get(self, request, *args, **kwargs):
        electric_resistance_form = ElectricResistanceTestForm(request.POST or None)
        temperature_rise_form = TemperatureRiseTestForm(request.POST or None)
        performance_determination_form = PerformanceDeterminationTestForm(request.POST or None)
        no_load_form = NoLoadTestForm(request.POST or None)
        withstand_voltage_form = WithstandVoltageACTestForm(request.POST or None)
        insulation_resistance_form = InsulationResistanceTestForm(request.POST or None)
        forms = [
            electric_resistance_form, temperature_rise_form, performance_determination_form, no_load_form,
            withstand_voltage_form, insulation_resistance_form
        ]
        context = {
            "forms": forms,
        }
        return render(request, "test_forms.html", context)
