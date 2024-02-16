from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, View, TemplateView
from django.views.generic.edit import FormMixin

from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm, PerformanceTestForm
)
from motor_testing.models import InductionMotor, PerformanceTest


class InductionMotorListingsView(LoginRequiredMixin, ListView, FormMixin):
    form_class = InitialForm
    model = InductionMotor
    template_name = "listings.html"
    paginate_by = 10
    context_object_name = 'inductionmotor_list'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        formset = self.get_formset()
        is_form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        if is_form_valid and formset_valid:
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        queryset = InductionMotor.objects.all()
        if search_query:
            queryset = InductionMotor.objects.filter(serial_number__icontains=search_query)
        return queryset.order_by("-updated_on")

    def get_formset(self):
        PerformanceTestFormSet = formset_factory(PerformanceTestForm, extra=0)
        dataset = [{'test_type': d, 'routine': False, 'type': False, 'special': False} for d in
                   PerformanceTest.PERFORMANCE_TEST_CHOICES]
        formset = PerformanceTestFormSet(
            initial=dataset, data=self.request.POST if self.request and self.request.method == 'POST' else None
        )
        return formset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        context['formset'] = self.get_formset()
        return context

    def save_formset(self, formset, motor):
        for form in formset:
            if form.is_valid():
                instance = form.save(commit=False)
                instance.motor = motor
                instance.page_number = 1
                instance.status = PerformanceTest.PENDING if (
                            instance.routine or instance.type or instance.special) else PerformanceTest.NOT_FOUND
                instance.save()

    def form_valid(self, form, formset):
        form.instance.user = self.request.user
        form.save()
        motor = form.instance
        self.save_formset(formset, motor)
        return HttpResponseRedirect(reverse_lazy("tests"))

    def form_invalid(self, form, formset):
        return render(self.request, "listings.html", {"form": form, "error": "error"})


class TestsView(LoginRequiredMixin, View):
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


class ReportView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['induction_motor'] = InductionMotor.objects.get(id=self.kwargs['id'])
        return context
