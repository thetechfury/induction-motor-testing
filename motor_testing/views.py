import os
from decimal import Decimal

import pdfkit
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError, models
from django.db.models import Case, When, BooleanField,Exists, OuterRef, Value, When,Subquery,CharField
from django.forms import formset_factory, model_to_dict
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, View, TemplateView
from django.views.generic.edit import FormMixin
from django.db.models import Exists, OuterRef

from django_pdfkit import PDFView

from mdb_parser import MDBParser, MDBTable
import platform
import pyodbc
import subprocess
import math
from datetime import datetime

from core_settings.settings import MDB_TO_CSV_EXE_LOCATION, WK_HTML_TO_PDF_PATH,POWER_FACTOR
from motor_testing.forms import (
    InitialForm, SearchForm, ElectricResistanceTestForm, TemperatureRiseTestForm, PerformanceDeterminationTestForm,
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm, PerformanceTestForm, LockRotorTestForm
)
from motor_testing.models import InductionMotor, PerformanceTest, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest, \
    PerformanceTestParameters, LockRotorTest, Configuration


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
        queryset = InductionMotor.objects.annotate(
            has_completed_performance_determination_test=Exists(
                PerformanceTest.objects.filter(
                    motor_id=OuterRef('pk'),
                    test_type='performance_determination_test',
                    status='COMPLETED'
                )
            )
        ).filter(status=InductionMotor.ACTIVE)

        if search_query:
            queryset = queryset.filter( status=InductionMotor.ACTIVE)

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
        all_motors = context['object_list']
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


def get_performance_test_statuses(inductionMotorReport):
    test_statuses = PerformanceTest.objects.filter(motor=inductionMotorReport,
                                                   status__in=[PerformanceTest.PENDING, PerformanceTest.COMPLETED])
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
            context['status'] =  get_performance_test_statuses(inductionMotorReport)
            context['all_test_completed'] = all(value == 'COMPLETED' for value in context['status'].values())
            if(context['status'].get('performance_determination_test') == 'COMPLETED'):
                context['performance_determination_test_completed'] = 'complete'
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
                if not existing_test == 'COMPLETED' or not (
                        instance['routine'] or instance['type'] or instance['special']):
                    form.cleaned_data['status'] = PerformanceTest.PENDING if (
                            instance['routine'] or instance['type'] or instance[
                        'special']) else PerformanceTest.NOT_FOUND
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
            'withstand_voltage_ac_test', 'insulation_resistance_test', 'performance_tests', 'lock_rotor_test').first()
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
        config = pdfkit.configuration(wkhtmltopdf=WK_HTML_TO_PDF_PATH)
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
        statues = get_performance_test_statuses(motor_id)
        response_data = {
            'resistance_ohm_1': motor.electric_resistance_test.resistance_ohm_1,
            'resistance_ohm_2': motor.electric_resistance_test.resistance_ohm_2,
            'resistance_ohm_3': motor.electric_resistance_test.resistance_ohm_3,
            'ambient_temperature_C': motor.electric_resistance_test.ambient_temperature_C,
            'unbalance_percentage': motor.electric_resistance_test.unbalance_percentage,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())
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
        statues =  get_performance_test_statuses(motor_id)

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
        file_path = Configuration.objects.all().first().no_load_test
        date = ''
        date_str = request.POST.get('no_load_test-reported_date')
        if date_str:
            date = format_date(date_str)
        table_name = date
        serial_number = motor.serial_number
        try:
            csv_data = read_mdb_table(table_name, file_path)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': f'No record found against this date {date_str}'}, status=400)
        filtered_data = [item for item in csv_data if item[1] == serial_number]
        if filtered_data ==[]:
            return JsonResponse({'error': f'No record found against this serial number {serial_number}'}, status=400)

        # Initialize sums

        sum_rpm = 0
        sum_speed = 0
        sum_volt = 0
        sum_amp = 0
        avg_rpm = 0
        avg_speed = 0
        avg_volt = 0
        avg_amp = 0
        power = 0
        if len(filtered_data):
            # Number of entries
            num_entries = len(filtered_data)

            # Sum up the values
            for entry in filtered_data:
                sum_rpm += float(entry[5])
                sum_speed += float(entry[4])
                sum_volt += float(entry[3])
                sum_amp += float(entry[2])

            # Calculate averages
            avg_rpm = sum_rpm / num_entries
            avg_speed = sum_speed / num_entries
            avg_volt = sum_volt / num_entries
            avg_amp = sum_amp / num_entries

            PF = POWER_FACTOR

            power = avg_volt * avg_amp * PF * math.sqrt(3)

        default = Decimal('0.00')
        direction_of_rotation = request.POST.get('no_load_test-direction_of_rotation')
        motor.no_load_test.voltage = avg_volt if avg_volt else default
        motor.no_load_test.current = avg_amp if avg_amp else default
        motor.no_load_test.power = power if power else default
        motor.no_load_test.frequency = avg_speed if avg_speed else default
        motor.no_load_test.speed = avg_rpm if avg_rpm else default
        motor.no_load_test.mdb_data = filtered_data
        motor.no_load_test.report_date = table_name
        _formatted_date = format_date_to_ymd(date_str)
        motor.no_load_test.reported_date = _formatted_date
        motor.no_load_test.direction_of_rotation = direction_of_rotation if direction_of_rotation else NoLoadTest.CLOCKWISE
        PerformanceTest.objects.filter(motor=motor, test_type='no_load_test').update(status=PerformanceTest.COMPLETED)

        motor.no_load_test.save()
        statues =  get_performance_test_statuses(motor_id)

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
        statues =  get_performance_test_statuses(motor_id)

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
        statues = get_performance_test_statuses(motor_id)

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

        file_path = Configuration.objects.all().first().lock_rotor_test
        date = ''
        date_str = request.POST.get('lock_rotor_test-reported_date')
        if date_str:
            date = format_date(date_str)

        table_name = date
        serial_number = motor.serial_number
        try:
            csv_data = read_mdb_table(table_name, file_path)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': f'No record found against this date {date_str}'}, status=400)
        filtered_data = [item for item in csv_data if item[1] == serial_number]
        if filtered_data ==[]:
            return JsonResponse({'error': f'No record found against this serial number {serial_number}'}, status=400)

        # Initialize sums
        sum_speed = 0
        sum_amp = 0
        sum_volt = 0

        # Number of entries
        num_entries = len(filtered_data)

        # Sum up the values
        for entry in filtered_data:
            sum_speed += int(entry[4])
            sum_amp += float(entry[2])
            sum_volt += int(entry[3])

        # Calculate averages
        avg_speed = sum_speed / num_entries
        avg_amp = sum_amp / num_entries
        avg_volt = sum_volt / num_entries
        PF = POWER_FACTOR

        power = avg_volt * avg_amp * PF * math.sqrt(3)

        default = Decimal('0.00')

        vibration = request.POST.get('lock_rotor_test-vibration')
        noise = request.POST.get('lock_rotor_test-noise')
        temperature = request.POST.get('lock_rotor_test-temperature')

        # Update LockRotorTest object
        motor.lock_rotor_test.vibration = vibration if vibration else default
        motor.lock_rotor_test.noise = noise if noise else default
        motor.lock_rotor_test.temperature = temperature if temperature else default
        motor.lock_rotor_test.speed = avg_speed if avg_speed else default
        motor.lock_rotor_test.voltage = avg_volt if avg_volt else default
        motor.lock_rotor_test.current = avg_amp if avg_amp else default
        motor.lock_rotor_test.power = power if power else default
        motor.lock_rotor_test.report_date = table_name
        _formatted_date = format_date_to_ymd(date_str)
        motor.lock_rotor_test.reported_date = _formatted_date
        motor.lock_rotor_test.mdb_data = filtered_data
        PerformanceTest.objects.filter(motor=motor, test_type='lock_rotor_test').update(
            status=PerformanceTest.COMPLETED)

        motor.lock_rotor_test.save()
        statues = get_form_statuses(motor_id)

        response_data = {
            'vibration': vibration,
            'noise': noise,
            'temperature': temperature,
            'avg_amp': avg_amp,
            'avg_speed': avg_speed,
            'avg_volt': avg_volt,
            'power': power,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in statues.values())

        }

        return JsonResponse(response_data)


class PerformanceDeterminationFormSave(View):
    list = []
    performancetest = {
        '25': {
            'load': 25,
            'current': 0,
            'slip': 0.0,
            'speed': 0,
            'efficiency': 0,
            'cos': 0
        },
        '50': {
            'load': 50,
            'current': 0,
            'slip': 0,
            'speed': 0,
            'efficiency': 0,
            'cos': 0
        },
        '75': {
            'load': 75,
            'current': 0,
            'slip': 0,
            'speed': 0,
            'efficiency': 0,
            'cos': 0
        },
        '100': {
            'load': 100,
            'current': 0,
            'slip': 0,
            'speed': 0,
            'efficiency': 0,
            'cos': 0
        }}

    def get_performance_tests_data(self, table_name):
        configuration = Configuration.objects.all().first()
        csv_data = read_mdb_table(table_name, configuration.performance_determination)
        return csv_data

    def align_load_data(self, motor_serial_number, csv_data):
        filtered_data = {
            '25': [],
            '50': [],
            '75': [],
            '100': [],
        }
        # for data in csv_data:
        for data in csv_data:
            csv_serial_number = data[3]
            csv_load_percentage = data[7]
            if csv_serial_number == motor_serial_number:
                filtered_data_key = csv_load_percentage.strip('%')  # Remove leading and trailing percentage signs
                filtered_data[filtered_data_key].append(data)
                # filtered_data[f'{data[7]}'].append(data)

        return filtered_data

    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        motor = get_object_or_404(InductionMotor, id=motor_id)

        if not hasattr(motor, 'performance_determination_test'):
            motor.performance_determination_test = PerformanceDeterminationTest(induction_motor=motor)

        table_name = ''
        date_str = request.POST.get('performance_determination_test-report_date')
        if date_str:
            table_name = format_date(date_str)

        performance_determination_test = motor.performance_determination_test
        default = Decimal('0.00')
        voltage = request.POST.get('performance_determination_test-voltage')
        frequency = request.POST.get('performance_determination_test-frequency')
        nominal_t = request.POST.get('performance_determination_test-nominal_t')
        performance_determination_test.voltage = voltage if voltage else default
        performance_determination_test.frequency = frequency if frequency else default
        performance_determination_test.nominal_t = nominal_t if nominal_t else default
        performance_determination_test.table_name = table_name
        # _formatted_date = format_date_to_ymd(date_str)
        performance_determination_test.report_date = date_str

        try:
            filtered_determine_data = self.align_load_data(motor.serial_number,
                                                           self.get_performance_tests_data(table_name))
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': f'No record found against this date {date_str}'}, status=400)
        if filtered_determine_data['25'] == [] and filtered_determine_data['50'] == [] and filtered_determine_data[
            '75'] == [] and filtered_determine_data['100'] == []:
            return JsonResponse({'error': f'No record found against this serial number {motor.serial_number}'}, status=400)


        # electric_resistance = ElectricResistanceTest.objects.filter(induction_motor=motor).first()
        electric_resistance_object = ElectricResistanceTest.objects.get(induction_motor = motor)
        if not electric_resistance_object.resistance_ohm_1:
            return JsonResponse({'error': 'Please fill Resistance 1 in  Electric Resistance Test'}, status=400)
        elif not electric_resistance_object.resistance_ohm_2:
            return JsonResponse({'error': 'Please fill Resistance 2 in  Electric Resistance Test'}, status=400)
        elif not electric_resistance_object.resistance_ohm_3:
            return JsonResponse({'error': 'Please fill Resistance 3 in  Electric Resistance Test'}, status=400)
        average_resistance = (electric_resistance_object.resistance_ohm_1 + electric_resistance_object.resistance_ohm_2 + electric_resistance_object.resistance_ohm_3)/3
        determine_data_list = self.convert_determine_data_in_list(filtered_determine_data)
        extended_determine_data_list = self.perform_calculation_and_extend_determine_data_list(determine_data_list,average_resistance)
        performance_determination_test.mdb_data = extended_determine_data_list
        performance_determination_test.save()
        self.save_performance_test_parameters(motor, performance_determination_test, filtered_determine_data,
                                                  electric_resistance_object)

        performance_test_statues = get_performance_test_statuses(motor_id)
        PerformanceTest.objects.filter(motor=motor, test_type='performance_determination_test').update(
            status=PerformanceTest.COMPLETED)

        response_data = {
            'voltage': motor.performance_determination_test.voltage,
            'frequency': motor.performance_determination_test.frequency,
            'nominal_t': motor.performance_determination_test.nominal_t,
            'status': 'completed',
            'all_test_completed': all(value == 'COMPLETED' for value in performance_test_statues.values())
        }

        return JsonResponse(response_data)

    def convert_determine_data_in_list(self,determine_dict):
        determine_list = [item for sublist in determine_dict.values() for item in sublist if len(item) > 0]
        return determine_list

    def perform_calculation_and_extend_determine_data_list(self,determine_data_list,avg_resistance):
            extended_list = []
            current_amp = 0
            speed_rpm = 0
            torque = 0
            for determine_data in determine_data_list:
                current_amp = float(determine_data[6])
                speed_rpm =   float(determine_data[4])
                voltage = float(determine_data[2])
                torque = float(determine_data[5])
                machainal_power = torque * speed_rpm
                loses = float(avg_resistance) * current_amp * current_amp
                electrical_power = current_amp * voltage
                efficiency = (machainal_power / (electrical_power + machainal_power + loses)) * 100
                horsepower = (torque* speed_rpm) / 5252
                watts_output = voltage * current_amp * POWER_FACTOR
                determine_data.append(horsepower)
                determine_data.append(watts_output)
                determine_data.append(efficiency)
                extended_list.append(determine_data)
            return extended_list


    def save_performance_test_parameters(self, motor, performance_determination_test, filtered_determine_data,electric_resistance):
        PerformanceTestParameters.objects.filter(
            performance_determination_test=performance_determination_test).delete()
        performance_objects = []

        avg_resistance = (
                                 electric_resistance.resistance_ohm_1 + electric_resistance.resistance_ohm_2 + electric_resistance.resistance_ohm_3) / 3
        for key in self.performancetest:
            performance_objects.append(
                self.create_performance_determination_obj(key, performance_determination_test,
                                                          filtered_determine_data.get(key), avg_resistance))

        PerformanceTestParameters.objects.bulk_create(performance_objects)

    def create_performance_determination_obj(self, key, performance_determination_test, filtered_determine_data,
                                             avg_resistance):
        performance_test_param = PerformanceTestParameters()
        performance_test_param.performance_determination_test = performance_determination_test

        if len(filtered_determine_data):
            current_amp = 0
            speed_rpm = 0
            hertz_freq = 0
            voltage = 0
            torque = 0
            for determine_data in filtered_determine_data:
                current_amp += float(determine_data[6])
                speed_rpm += int(determine_data[4])
                hertz_freq += int(determine_data[1])
                voltage += int(determine_data[2])
                torque += int(determine_data[5])
            avg_current = current_amp / len(filtered_determine_data)
            avg_speed_rpm = speed_rpm / len(filtered_determine_data)
            avg_hertz_freq = hertz_freq / len(filtered_determine_data)
            avg_voltage = voltage / len(filtered_determine_data)
            avg_torque = torque / len(filtered_determine_data)
            ns = (avg_hertz_freq * 120) / 2
            machainal_power = avg_torque * avg_speed_rpm
            loses = float(avg_resistance) * avg_current * avg_current
            electrical_power = avg_current * avg_voltage
            real_power = avg_voltage * avg_current * POWER_FACTOR * 1.732
            apperent_power = avg_voltage * avg_current * 1.732

            performance_test_param.load = self.performancetest.get(key)['load']
            performance_test_param.current = avg_current
            performance_test_param.slip = ((ns - avg_speed_rpm) / ns) * 100
            performance_test_param.speed = avg_speed_rpm
            performance_test_param.efficiency = (machainal_power / (electrical_power + machainal_power +loses )) * 100
            performance_test_param.cos = real_power / apperent_power
        else:
            performance_test_param.load = self.performancetest.get(key)['load']
            performance_test_param.current = self.performancetest.get(key)['current']
            performance_test_param.slip = self.performancetest.get(key)['slip']
            performance_test_param.speed = self.performancetest.get(key)['speed']
            performance_test_param.efficiency = self.performancetest.get(key)['efficiency']
            performance_test_param.cos = self.performancetest.get(key)['cos']
        return performance_test_param


def format_date(date_str):
    # Try to detect the format and convert to datetime object
    try:
        # If the date is in 'DD/MM/YYYY' format
        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
    except ValueError:
        try:
            # If the date is in 'YYYY-MM-DD' format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            # If the date format is unknown
            return None

    # Format the date to remove leading zeros from day and month, and then concatenate
    day = str(date_obj.day)
    month = str(date_obj.month)
    year = str(date_obj.year)

    formatted_date = day + month + year  # Assuming you want to drop the century from the year
    return formatted_date


def format_date_to_ymd(date_str):
    # Try to determine the format based on the position of the year in the string
    if date_str.count('/') == 2:  # Likely 'MM/DD/YYYY' or 'DD/MM/YYYY'
        splitter = date_str.split('/')
        if len(splitter[2]) == 4:
            # If the last part is 4 digits long, assume 'MM/DD/YYYY'
            try_format = "%m/%d/%Y"
        else:
            # Otherwise, it might be in a different format or invalid
            try_format = None
    elif date_str.count('-') == 2:
        # If the string contains hyphens, assume 'YYYY-MM-DD'
        try_format = "%Y-%m-%d"
    else:
        # Unknown or unsupported format
        try_format = None

    if try_format:
        try:
            # Try to parse the date string with the determined format
            date_object = datetime.strptime(date_str, try_format)
            formatted_date = date_object.strftime("%Y-%m-%d")
            return formatted_date
        except ValueError:
            pass  # Parsing failed, the format might have been guessed incorrectly

    return None


class ChartView(View):
    def get(self, request, *args, **kwargs):
        performance_determination_data= PerformanceDeterminationTest.objects.get(id= kwargs['id']).mdb_data
        torque_values = []
        speed_values = []
        amplitude_values = []
        efficiency_values = []
        horsepower_values = []
        watts_out_values = []
        for data in performance_determination_data:
            current_amp = data[6]
            speed_rpm = int(data[4])
            torque = data[5]
            horsepower = data[8]
            watts_out = data[9]
            efficiency = data[10]
            speed_values.append(speed_rpm)
            amplitude_values.append(current_amp)
            torque_values.append(torque)
            efficiency_values.append(efficiency)
            horsepower_values.append(horsepower)
            watts_out_values.append(watts_out)

        context = {
            'torque':torque_values,
            'amplitude':amplitude_values,
            'speed':speed_values,
            'efficiency':efficiency_values,
            'horse_power':horsepower_values,
            'watts_out': watts_out_values
        }

        return render(request, 'graph.html',context)


class Remarks(View):
    def post(self, request, *args, **kwargs):
        motor_id = kwargs['id']
        remarks = request.POST.get('remarks')
        motor = get_object_or_404(InductionMotor, id=motor_id)
        motor.remarks = remarks
        motor.save()

        return JsonResponse({'success': True})


def mdb_to_csv_conversion(input_file_path, csv_output_path):
    """
    Export a table from an MDB file to CSV format.
    """
    command = [os.path.join(MDB_TO_CSV_EXE_LOCATION, "mdb2csv.exe"),
               input_file_path, f'-output={csv_output_path}', '-silent']
    process = subprocess.run(command)
    return process.stdout


def read_mdb_table(table_name, file_path):
    system = platform.system()
    data = []
    if system == "Windows":
        print("Running on Windows")
        # Establish connection to the MDB file
        conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=' + file_path + ';'
        conn = pyodbc.connect(conn_str)
        # Create a cursor to execute SQL queries
        cursor = conn.cursor()
        sql_query = 'SELECT * FROM {}'.format(table_name)
        cursor.execute(sql_query)

        # Fetch and print the results
        for row in cursor.fetchall():
            data.append(row)
        # Close cursor and connection
        cursor.close()
        conn.close()
    elif system == "Linux":
        print("Running on Linux")
        table = MDBTable(file_path=file_path, table=table_name)
        data.append(table.columns)
        for row in table:
            data.append(row)
    else:
        print(f"Running on {system}")

    return data
