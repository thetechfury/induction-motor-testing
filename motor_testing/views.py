from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, View, TemplateView
from django.views.generic.edit import FormMixin

from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm
)
from motor_testing.models import InductionMotor


class InductionMotorListingsView(ListView, FormMixin):
    form_class = InitialForm
    model = InductionMotor
    template_name = "listings.html"
    paginate_by = 10
    context_object_name = 'inductionmotor_list'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        queryset = InductionMotor.objects.all()
        if search_query:
            queryset = InductionMotor.objects.filter(serial_number__icontains=search_query)
        return queryset.order_by("-updated_on")

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        return HttpResponseRedirect(reverse_lazy("tests"))

    def form_invalid(self, form):
        return render(self.request, "listings.html", {"form": form, "error": "error"})


class TestsView(View):
    def get(self, request, *args, **kwargs):
        electric_resistance_form = ElectricResistanceTestForm(request.POST or None)
        temperature_rise_form = TemperatureRiseTestForm(request.POST or None)
        performance_determination_form = PerformanceDeterminationTestForm(request.POST or None)
        no_load_form = NoLoadTestForm(request.POST or None)
        withstand_voltage_form = WithstandVoltageACTestForm(request.POST or None)
        insulation_resistance_form = InsulationResistanceTestForm(request.POST or None)
        context = {
            'electric_resistance_form': electric_resistance_form,
            'temperature_rise_form': temperature_rise_form,
            'performance_determination_form': performance_determination_form,
            'no_load_form': no_load_form,
            'withstand_voltage_form': withstand_voltage_form,
            'insulation_resistance_form': insulation_resistance_form
        }

        return render(request, "test_forms.html", context)


class ReportView(TemplateView):
    template_name = "index.html"
