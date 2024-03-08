import os
from decimal import Decimal

import pdfkit
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, models
from django.db.models import Case, When, BooleanField
from django.forms import formset_factory, model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, View, TemplateView
from django.views.generic.edit import FormMixin
from django_pdfkit import PDFView
from openpyxl import load_workbook

from core_settings import settings
from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm, PerformanceTestForm, LockRotorTestForm
)
from motor_testing.models import InductionMotor, PerformanceTest, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest, \
    PerformanceTestParameters, LockRotorTest


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
            queryset = InductionMotor.objects.filter(serial_number__icontains=search_query,
                                                     status=InductionMotor.ACTIVE)
        return queryset.annotate(
            report_status=Case(When(
                report_link__isnull=False, then=models.Value(True)), default=False, output_field=BooleanField())
        ).order_by("-updated_on")

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


def get_form_statuses(inductionMotorReport):
    test_statuses = PerformanceTest.objects.filter(motor=inductionMotorReport,status__in=[PerformanceTest.PENDING,PerformanceTest.COMPLETED])
    tests = {test.test_type: test.status for test in test_statuses}
    return tests


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

    # def get_performance_files(self, obj):
    #     return {
    #         'file_25': obj.performance_25 if obj.performance_25 else None,
    #         'file_25_name': os.path.basename(obj.performance_25.name) if obj.performance_25 else None,
    #         'file_50': obj.performance_50 if obj.performance_50 else None,
    #         'file_50_name': os.path.basename(obj.performance_50.name) if obj.performance_50 else None,
    #         'file_75': obj.performance_75 if obj.performance_75 else None,
    #         'file_75_name': os.path.basename(obj.performance_75.name) if obj.performance_75 else None,
    #         'file_100': obj.performance_100 if obj.performance_100 else None,
    #         'file_100_name': os.path.basename(obj.performance_100.name) if obj.performance_100 else None
    #     }

    def get(self, request, *args, **kwargs):
        inductionMotorReport = self.get_object()
        ElectricResistanceTest.objects.get_or_create(induction_motor=inductionMotorReport)
        TemperatureRiseTest.objects.get_or_create(induction_motor=inductionMotorReport)
        PerformanceDeterminationTest.objects.get_or_create(induction_motor=inductionMotorReport)
        NoLoadTest.objects.get_or_create(induction_motor=inductionMotorReport)
        WithstandVoltageACTest.objects.get_or_create(induction_motor=inductionMotorReport)
        InsulationResistanceTest.objects.get_or_create(induction_motor=inductionMotorReport)
        LockRotorTest.objects.get_or_create(induction_motor=inductionMotorReport)
        if not inductionMotorReport:
            return render(request, "registration/404.html")
        else:
            tests = PerformanceTest.objects.filter(motor_id=inductionMotorReport.id,
                                                   status__in=[PerformanceTest.COMPLETED, PerformanceTest.PENDING])
            test_types = []
            for test in tests:
                test_types.append(test.test_type)

            electric_resistance_form = ElectricResistanceTestForm(
                instance=inductionMotorReport.electric_resistance_test)
            temperature_rise_form = TemperatureRiseTestForm(instance=inductionMotorReport.temperature_rise_test)
            performance_determination_form = PerformanceDeterminationTestForm(
                instance=inductionMotorReport.performance_determination_test
            )
            no_load_form = NoLoadTestForm(instance=inductionMotorReport.no_load_test)
            withstand_voltage_form = WithstandVoltageACTestForm(instance=inductionMotorReport.withstand_voltage_ac_test)
            insulation_resistance_form = InsulationResistanceTestForm(
                instance=inductionMotorReport.insulation_resistance_test
            )
            lock_rotor_test_form = LockRotorTestForm(
                instance=inductionMotorReport.lock_rotor_test
            )

            forms = {
                'electric_resistance_form': electric_resistance_form,
                'temperature_rise_form': temperature_rise_form,
                'performance_determination_form': performance_determination_form,
                'no_load_form': no_load_form,
                'withstand_voltage_form': withstand_voltage_form,
                'insulation_resistance_form': insulation_resistance_form,
                'lock_rotor_test_form': lock_rotor_test_form
            }

            context = {}
            for key, form in forms.items():
                if form.prefix in test_types:
                    context[form.prefix] = form
            context['all_forms'] = forms.items()
            context['inductionMotorReport'] = inductionMotorReport
            context['edit_form'] = InitialForm(initial=model_to_dict(inductionMotorReport))
            context['edit_formset'] = self.get_performance_tests_forms(inductionMotorReport)
            context['status'] = get_form_statuses(inductionMotorReport)
            context['all_test_completed'] = all(value == 'COMPLETED' for value in context['status'].values())
            # context['files'] = self.get_performance_files(inductionMotorReport.performance_determination_test)
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
                existing_test = motor.performance_tests.filter(test_type=form.cleaned_data['test_type']).first().status
                if not existing_test == 'COMPLETED' or not (instance['routine'] or instance['type'] or instance['special']):
                    form.cleaned_data['status'] = PerformanceTest.PENDING if (
                            instance['routine'] or instance['type'] or instance['special']) else PerformanceTest.NOT_FOUND
                else:
                    form.cleaned_data['status'] = 'COMPLETED'
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


class ReportView(TemplateView):
    template_name = "induction_report.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        induction_motor = InductionMotor.objects.filter(id=self.kwargs['id']).prefetch_related(
            'electric_resistance_test', 'temperature_rise_test', 'performance_determination_test', 'no_load_test',
            'withstand_voltage_ac_test', 'insulation_resistance_test', 'performance_tests').first()
        if hasattr(induction_motor, 'performance_determination_test'):
            performance_test = induction_motor.performance_determination_test
            context['parameters'] = PerformanceTestParameters.objects.filter(
                performance_determination_test=performance_test)
        selected_tests = PerformanceTest.objects.filter(motor_id=induction_motor.id, status=PerformanceTest.COMPLETED)
        all_tests = PerformanceTest.objects.filter(motor_id=induction_motor.id)
        if selected_tests:
            context['selected_tests'] = selected_tests
        if all_tests:
            context['all_tests'] = all_tests
        context['induction_motor'] = induction_motor
        if selected_tests.filter(test_type='lock_rotor_test').first() in selected_tests:
            context['lock_rotor_test'] = True
        return context


class GeneratePDF(PDFView):
    def get(self, request, *args, **kwargs):
        config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')
        induction_motor = InductionMotor.objects.get(id=kwargs['id'])
        report_url = request.build_absolute_uri(reverse('report', kwargs={'id': kwargs['id']}))
        report_link = f'./generatedReports/{induction_motor.customer_name}-{induction_motor.serial_number}.pdf'
        pdf = pdfkit.from_url(report_url, report_link, configuration=config)
        if pdf:
            InductionMotor.objects.filter(id=kwargs['id']).update(report_link=report_link)
        with open(report_link, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline;filename=mypdf.pdf'
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

        default = Decimal('0.00')
        resistance_ohm_1 = request.POST.get('electric_resistance_test-resistance_ohm_1')
        resistance_ohm_2 = request.POST.get('electric_resistance_test-resistance_ohm_2')
        resistance_ohm_3 = request.POST.get('electric_resistance_test-resistance_ohm_3')
        ambient_temperature_C = request.POST.get('electric_resistance_test-ambient_temperature_C')
        unbalance_percentage = request.POST.get('electric_resistance_test-unbalance_percentage')
        motor.electric_resistance_test.resistance_ohm_1 = resistance_ohm_1 if resistance_ohm_1 else default
        motor.electric_resistance_test.resistance_ohm_2 = resistance_ohm_2 if resistance_ohm_2 else default
        motor.electric_resistance_test.resistance_ohm_3 = resistance_ohm_3 if resistance_ohm_3 else default
        motor.electric_resistance_test.ambient_temperature_C = ambient_temperature_C if ambient_temperature_C else default
        motor.electric_resistance_test.unbalance_percentage = unbalance_percentage if unbalance_percentage else default
        PerformanceTest.objects.filter(motor=motor, test_type='electric_resistance_test').update(
            status=PerformanceTest.COMPLETED)
        motor.electric_resistance_test.save()
        statues = get_form_statuses(motor_id)
        response_data = {
            'resistance_ohm_1': motor.electric_resistance_test.resistance_ohm_1,
            'resistance_ohm_2': motor.electric_resistance_test.resistance_ohm_2,
            'resistance_ohm_3': motor.electric_resistance_test.resistance_ohm_3,
            'ambient_temperature_C': motor.electric_resistance_test.ambient_temperature_C,
            'unbalance_percentage': motor.electric_resistance_test.unbalance_percentage,
            'status': 'completed',
            'all_test_completed':all(value == 'COMPLETED' for value in statues.values())
        }

        return JsonResponse(response_data)


class TemperatureFormSaveView(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated ElectricResistanceTest
        if not hasattr(motor, 'temperature_rise_test'):
            motor.temperature_rise_test = TemperatureRiseTest.objects.get_or_create(induction_motor=motor)

        default = Decimal('0.00')
        voltage = request.POST.get('temperature_rise_test-voltage')
        winding = request.POST.get('temperature_rise_test-winding')
        frequency = request.POST.get('temperature_rise_test-frequency')
        de_bearing = request.POST.get('temperature_rise_test-de_bearing')
        nde_bearing = request.POST.get('temperature_rise_test-nde_bearing')
        motor.temperature_rise_test.voltage = voltage if voltage else default
        motor.temperature_rise_test.winding = winding if winding else default
        motor.temperature_rise_test.frequency = frequency if frequency else default
        motor.temperature_rise_test.de_bearing = de_bearing if de_bearing else default
        motor.temperature_rise_test.nde_bearing = nde_bearing if nde_bearing else default
        PerformanceTest.objects.filter(motor=motor, test_type='temperature_rise_test').update(
            status=PerformanceTest.COMPLETED)
        motor.temperature_rise_test.save()
        statues = get_form_statuses(motor_id)

        response_data = {
            'voltage': motor.temperature_rise_test.voltage,
            'winding': motor.temperature_rise_test.winding,
            'frequency': motor.temperature_rise_test.frequency,
            'de_bearing': motor.temperature_rise_test.de_bearing,
            'nde_bearing': motor.temperature_rise_test.nde_bearing,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class NoLoadFormSaveView(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated ElectricResistanceTest
        if not hasattr(motor, 'no_load_test'):
            motor.no_load_test = NoLoadTest.objects.get_or_create(induction_motor=motor)

        default = Decimal('0.00')
        voltage = request.POST.get('no_load_test-voltage')
        current = request.POST.get('no_load_test-current')
        power = request.POST.get('no_load_test-power')
        frequency = request.POST.get('no_load_test-frequency')
        speed = request.POST.get('no_load_test-speed')
        direction_of_rotation = request.POST.get('no_load_test-direction_of_rotation')
        motor.no_load_test.voltage = voltage if voltage else default
        motor.no_load_test.current = current if current else default
        motor.no_load_test.power = power if power else default
        motor.no_load_test.frequency = frequency if frequency else default
        motor.no_load_test.speed = speed if speed else default
        motor.no_load_test.direction_of_rotation = direction_of_rotation if direction_of_rotation else NoLoadTest.CLOCKWISE
        PerformanceTest.objects.filter(motor=motor, test_type='no_load_test').update(status=PerformanceTest.COMPLETED)

        motor.no_load_test.save()
        statues = get_form_statuses(motor_id)

        response_data = {
            'voltage': motor.no_load_test.voltage,
            'current': motor.no_load_test.current,
            'power': motor.no_load_test.power,
            'frequency': motor.no_load_test.frequency,
            'speed': motor.no_load_test.speed,
            'direction_of_rotation': motor.no_load_test.direction_of_rotation,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class WithStandVoltageFormSaveView(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated ElectricResistanceTest
        if not hasattr(motor, 'withstand_voltage_ac_test'):
            motor.withstand_voltage_ac_test = WithstandVoltageACTest.objects.get_or_create(induction_motor=motor)

        description = request.POST.get('withstand_voltage_ac_test-description')
        voltage_kv = request.POST.get('withstand_voltage_ac_test-voltage_kv')
        time_in_seconds = request.POST.get('withstand_voltage_ac_test-time_in_seconds')
        motor.withstand_voltage_ac_test.description = description if description else ''
        motor.withstand_voltage_ac_test.voltage_kv = voltage_kv if voltage_kv else Decimal('0.00')
        motor.withstand_voltage_ac_test.time_in_seconds = time_in_seconds if time_in_seconds else 0
        PerformanceTest.objects.filter(motor=motor, test_type='withstand_voltage_ac_test').update(
            status=PerformanceTest.COMPLETED)

        motor.withstand_voltage_ac_test.save()
        statues = get_form_statuses(motor_id)

        response_data = {
            'description': motor.withstand_voltage_ac_test.description,
            'voltage_kv': motor.withstand_voltage_ac_test.voltage_kv,
            'time_in_seconds': motor.withstand_voltage_ac_test.time_in_seconds,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class InsulationFormSaveView(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated ElectricResistanceTest
        if not hasattr(motor, 'insulation_resistance_test'):
            motor.insulation_resistance_test = InsulationResistanceTest.objects.get_or_create(induction_motor=motor)

        default = Decimal('0.00')
        description = request.POST.get('insulation_resistance_test-description')
        voltage = request.POST.get('insulation_resistance_test-voltage')
        insulation_resistance = request.POST.get('insulation_resistance_test-insulation_resistance')
        time_in_seconds = request.POST.get('insulation_resistance_test-time_in_seconds')
        ambient_temperature_C = request.POST.get('insulation_resistance_test-ambient_temperature_C')
        humidity_percentage = request.POST.get('insulation_resistance_test-humidity_percentage')
        motor.insulation_resistance_test.description = description if description else ''
        motor.insulation_resistance_test.voltage = voltage if voltage else default
        motor.insulation_resistance_test.insulation_resistance = insulation_resistance if insulation_resistance else default
        motor.insulation_resistance_test.time_in_seconds = time_in_seconds if time_in_seconds else 0
        motor.insulation_resistance_test.ambient_temperature_C = ambient_temperature_C if ambient_temperature_C else default
        motor.insulation_resistance_test.humidity_percentage = humidity_percentage if humidity_percentage else default
        PerformanceTest.objects.filter(motor=motor, test_type='insulation_resistance_test').update(
            status=PerformanceTest.COMPLETED)

        motor.insulation_resistance_test.save()
        statues = get_form_statuses(motor_id)

        response_data = {
            'description': motor.insulation_resistance_test.description,
            'voltage': motor.insulation_resistance_test.voltage,
            'insulation_resistance': motor.insulation_resistance_test.insulation_resistance,
            'time_in_seconds': motor.insulation_resistance_test.time_in_seconds,
            'ambient_temperature_C': motor.insulation_resistance_test.ambient_temperature_C,
            'humidity_percentage': motor.insulation_resistance_test.humidity_percentage,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class LockRotorFormSave(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        # Check if the InductionMotor instance has an associated LockRotorTest
        if not hasattr(motor, 'lock_rotor_test'):
            motor.lock_rotor_test = LockRotorTest.objects.create(induction_motor=motor)

        default = Decimal('0.00')
        vibration = request.POST.get('lock_rotor_test-vibration')
        noise = request.POST.get('lock_rotor_test-noise')
        temperature = request.POST.get('lock_rotor_test-temperature')

        # Update LockRotorTest object
        motor.lock_rotor_test.vibration = vibration if vibration else default
        motor.lock_rotor_test.noise = noise if noise else default
        motor.lock_rotor_test.temperature = temperature if temperature else default
        PerformanceTest.objects.filter(motor=motor, test_type='lock_rotor_test').update(
            status=PerformanceTest.COMPLETED)

        motor.lock_rotor_test.save()
        statues = get_form_statuses(motor_id)

        response_data = {
            'vibration': vibration,
            'noise': noise,
            'temperature': temperature,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class PerformanceDeterminationFormSave(View):

    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        if not hasattr(motor, 'performance_determination_test'):
            motor.performance_determination_test = PerformanceDeterminationTest(induction_motor=motor)
        performance_determination_test = motor.performance_determination_test
        default = Decimal('0.00')
        voltage = request.POST.get('performance_determination_test-voltage')
        frequency = request.POST.get('performance_determination_test-frequency')
        nominal_t = request.POST.get('performance_determination_test-nominal_t')
        performance_determination_test.voltage = voltage if voltage else default
        performance_determination_test.frequency = frequency if frequency else default
        performance_determination_test.nominal_t = nominal_t if nominal_t else default


        PerformanceTest.objects.filter(motor=motor, test_type='performance_determination_test').update(
            status=PerformanceTest.COMPLETED)
        performance_determination_test.save()
        statues = get_form_statuses(motor_id)


        response_data = {
            'voltage': motor.performance_determination_test.voltage,
            'frequency': motor.performance_determination_test.frequency,
            'nominal_t': motor.performance_determination_test.nominal_t,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class ChartView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'graph.html')

class Remarks(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        remarks = request.POST.get('remarks')
        motor = get_object_or_404(InductionMotor, id=motor_id)
        motor.remarks = remarks
        motor.save()

        return JsonResponse({'success': True})

# import subprocess
#
# def read_table(table_name):
#     cmd = ['mdb-export', '/home/thetechfury/Downloads/3.3.mdb', table_name]
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     if result.returncode == 0:
#         print(result.stdout)
#     else:
#         print("Error reading table:", result.stderr)
#
# read_table('732024')
#
# import subprocess
# import csv
# from io import StringIO
#
# def mdb_to_csv(table_name, mdb_path):
#     """
#     Export a table from an MDB file to CSV format.
#     """
#     command = ['mdb-export', mdb_path, table_name]
#     process = subprocess.run(command, capture_output=True, text=True, check=True)
#     return process.stdout
#
# def read_mdb_table(table_name, mdb_path):
#     """
#     Read data from an MDB file table and return a list of dictionaries.
#     """
#     csv_data = mdb_to_csv(table_name, mdb_path)
#     csv_reader = csv.DictReader(StringIO(csv_data))
#     return list(csv_reader)
#
# read_mdb_table('732024', '/home/thetechfury/Downloads/3.3.mdb')