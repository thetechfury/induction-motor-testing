from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import ListView, View, TemplateView
from django.views.generic.edit import FormMixin

from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm, PerformanceTestForm
)
from motor_testing.models import InductionMotor, PerformanceTest
from django.http import HttpResponse
from django.views.generic import View
from django.template.loader import get_template
from xhtml2pdf import pisa


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
        queryset = InductionMotor.objects.filter(status=InductionMotor.ACTIVE)
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
        return HttpResponseRedirect(reverse('tests', kwargs={"pk": motor.id}))

    def form_invalid(self, form, formset):
        return render(self.request, "listings.html", {"form": form, "error": "error", "formset": formset})


class TestsView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):

        inductionMotorReport = InductionMotor.objects.filter(id=kwargs['pk'], status=InductionMotor.ACTIVE).first()
        if not inductionMotorReport:
            return render(request, "registration/404.html")
        else:
            tests = PerformanceTest.objects.filter(motor_id=inductionMotorReport.id).filter(
                status=PerformanceTest.PENDING)
            test_types = []
            for test in tests:
                test_types.append(test.test_type)
            electric_resistance_form = ElectricResistanceTestForm(request.POST or None)
            temperature_rise_form = TemperatureRiseTestForm(request.POST or None)
            performance_determination_form = PerformanceDeterminationTestForm(request.POST or None)
            no_load_form = NoLoadTestForm(request.POST or None)
            withstand_voltage_form = WithstandVoltageACTestForm(request.POST or None)
            insulation_resistance_form = InsulationResistanceTestForm(request.POST or None)
            forms = {
                'electric_resistance_form': electric_resistance_form,
                'temperature_rise_form': temperature_rise_form,
                'performance_determination_form': performance_determination_form,
                'no_load_form': no_load_form,
                'withstand_voltage_form': withstand_voltage_form,
                'insulation_resistance_form': insulation_resistance_form
            }
            context = {}
            for key, form in forms.items():
                if form.prefix in test_types:
                    context[form.prefix] = form
                else:
                    context[form.prefix] = None

            return render(request, "test_forms.html", context)


class ReportView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['induction_motor'] = InductionMotor.objects.get(id=self.kwargs['id'])
        return context


class GeneratePDF(View):
    def get(self, request, *args, **kwargs):
        template = get_template('exp.html')
        html = template.render(
            {'induction_motor': InductionMotor.objects.get(id=self.kwargs['id'])})  # Pass any context variables here

        # Create a PDF file
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="output.pdf"'

        # Generate PDF
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('PDF generation error!', status=500)

        return response


class DeleteReportView(LoginRequiredMixin, View):

    def get(self, request, *args, **kwargs):

        try:
            InductionMotor.objects.filter(pk=kwargs['id']).update(status=InductionMotor.DELETE)
        except DatabaseError:
            return HttpResponse('Record Deleted', status=401)
        return HttpResponse('Record Deleted', status=200)
