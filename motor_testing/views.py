from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
from django.forms import formset_factory, model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, View, TemplateView
from django.views.generic.edit import FormMixin

from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm, PerformanceTestForm
)
from motor_testing.models import InductionMotor, PerformanceTest, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest
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

    def get_performance_tests_forms(self, obj=None):
        PerformanceTestFormSet = formset_factory(PerformanceTestForm, extra=0)
        dataset = PerformanceTest.objects.filter(motor=obj)
        dataset = [model_to_dict(x, fields=['test_type', 'routine', 'type', 'special']) for x in dataset]
        formset = PerformanceTestFormSet(
            initial=dataset,
            data=self.request.POST if self.request and self.request.method == 'POST' else None
        )
        return formset

    def get_object(self):
        return InductionMotor.objects.filter(id=self.kwargs['pk'], status=InductionMotor.ACTIVE).first()

    def get(self, request, *args, **kwargs):
        inductionMotorReport = self.get_object()
        ElectricResistanceTest.objects.get_or_create(induction_motor=inductionMotorReport)
        TemperatureRiseTest.objects.get_or_create(induction_motor=inductionMotorReport)
        PerformanceDeterminationTest.objects.get_or_create(induction_motor=inductionMotorReport)
        NoLoadTest.objects.get_or_create(induction_motor=inductionMotorReport)
        WithstandVoltageACTest.objects.get_or_create(induction_motor=inductionMotorReport)
        InsulationResistanceTest.objects.get_or_create(induction_motor=inductionMotorReport)
        if not inductionMotorReport:
            return render(request, "registration/404.html")
        else:
            tests = PerformanceTest.objects.filter(motor_id=inductionMotorReport.id).filter(
                status=PerformanceTest.PENDING)
            test_types = []
            for test in tests:
                test_types.append(test.test_type)

            electric_resistance_form = ElectricResistanceTestForm(
                instance=inductionMotorReport.electric_resistance_test)
            temperature_rise_form = TemperatureRiseTestForm(instance=inductionMotorReport.temperature_rise_test)
            performance_determination_form = PerformanceDeterminationTestForm(
                initial={'parent': inductionMotorReport})
            no_load_form = NoLoadTestForm(instance=inductionMotorReport.no_load_test)
            withstand_voltage_form = WithstandVoltageACTestForm(instance=inductionMotorReport.withstand_voltage_ac_test)
            insulation_resistance_form = InsulationResistanceTestForm(
                instance=inductionMotorReport.insulation_resistance_test
            )

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

            context['inductionMotorReport'] = inductionMotorReport

            return render(request, "test_forms.html", context)

    def post(self, request, *args, **kwargs):
        form = InitialForm(data=self.request.POST)
        formset = self.get_performance_tests_forms()
        is_form_valid = form.is_valid()
        formset_valid = formset.is_valid()
        if is_form_valid and formset_valid:
            return self.form_valid(form, formset)
        else:
            return self.form_invalid(form, formset)

    def save_formset(self, formset, motor):
        for form in formset:
            if form.is_valid():
                instance = form.cleaned_data
                form.cleaned_data['status'] = PerformanceTest.PENDING if (
                        instance['routine'] or instance['type'] or instance['special']) else PerformanceTest.NOT_FOUND
                motor.performance_tests.update_or_create(
                    test_type=form.cleaned_data['test_type'], defaults=form.cleaned_data
                )

    def update_motor_report(self, form):
        return InductionMotor.objects.update_or_create(id=self.kwargs['pk'], defaults=form.cleaned_data)

    def form_valid(self, form, formset):
        form.instance.id = self.kwargs['pk']
        form.instance.user = self.request.user
        form.cleaned_data['status'] = InductionMotor.ACTIVE
        motor = self.update_motor_report(form)
        self.save_formset(formset, motor[0])
        return HttpResponseRedirect(reverse('tests', kwargs={"pk": motor[0].id}))

    def form_invalid(self, form, formset):
        return render(self.request, "test_forms.html", {"edit_form": form, "error": "error", "edit_formset": formset})


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


class ElectricFormSaveView(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated ElectricResistanceTest
        if not hasattr(motor, 'electric_resistance_test'):
            motor.electric_resistance_test = ElectricResistanceTest.objects.get_or_create(induction_motor=motor)

        motor.electric_resistance_test.resistance_ohm_1 = request.POST.get('electric_resistance_test-resistance_ohm_1')
        motor.electric_resistance_test.resistance_ohm_2 = request.POST.get('electric_resistance_test-resistance_ohm_2')
        motor.electric_resistance_test.resistance_ohm_3 = request.POST.get('electric_resistance_test-resistance_ohm_3')
        motor.electric_resistance_test.ambient_temperature_C = request.POST.get(
            'electric_resistance_test-ambient_temperature_C')
        motor.electric_resistance_test.unbalance_percentage = request.POST.get(
            'electric_resistance_test-unbalance_percentage')
        motor.electric_resistance_test.save()

        response_data = {
            'resistance_ohm_1': motor.electric_resistance_test.resistance_ohm_1,
            'resistance_ohm_2': motor.electric_resistance_test.resistance_ohm_2,
            'resistance_ohm_3': motor.electric_resistance_test.resistance_ohm_3,
            'ambient_temperature_C': motor.electric_resistance_test.ambient_temperature_C,
            'unbalance_percentage': motor.electric_resistance_test.unbalance_percentage
        }

        return JsonResponse(response_data)


class TemperatureFormSaveView(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated ElectricResistanceTest
        if not hasattr(motor, 'temperature_rise_test'):
            motor.temperature_rise_test = TemperatureRiseTest.objects.get_or_create(induction_motor=motor)

        motor.temperature_rise_test.voltage = request.POST.get('temp_rise_test-voltage')
        motor.temperature_rise_test.winding = request.POST.get('temp_rise_test-winding')
        motor.temperature_rise_test.frequency = request.POST.get('temp_rise_test-frequency')
        motor.temperature_rise_test.de_bearing = request.POST.get('temp_rise_test-de_bearing')
        motor.temperature_rise_test.nde_bearing = request.POST.get('temp_rise_test-nde_bearing')
        motor.temperature_rise_test.save()

        response_data = {
            'voltage': motor.temperature_rise_test.voltage,
            'winding': motor.temperature_rise_test.winding,
            'frequency': motor.temperature_rise_test.frequency,
            'de_bearing': motor.temperature_rise_test.de_bearing,
            'nde_bearing': motor.temperature_rise_test.nde_bearing
        }

        return JsonResponse(response_data)