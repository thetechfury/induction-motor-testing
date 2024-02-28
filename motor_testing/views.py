from decimal import Decimal

import pdfkit
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import DatabaseError
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
    NoLoadTestForm, WithstandVoltageACTestForm, InsulationResistanceTestForm, PerformanceTestForm
)
from motor_testing.models import InductionMotor, PerformanceTest, ElectricResistanceTest, TemperatureRiseTest, \
    PerformanceDeterminationTest, NoLoadTest, WithstandVoltageACTest, InsulationResistanceTest, \
    PerformanceTestParameters


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
                instance=inductionMotorReport.performance_determination_test
            )
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

            context['edit_form'] = InitialForm(initial=model_to_dict(inductionMotorReport))
            context['edit_formset'] = self.get_performance_tests_forms(inductionMotorReport)

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
        selected_tests = PerformanceTest.objects.filter(motor_id=induction_motor.id, status=PerformanceTest.PENDING)
        all_tests = PerformanceTest.objects.filter(motor_id=induction_motor.id)
        if selected_tests:
            context['selected_tests'] = selected_tests
        if all_tests:
            context['all_tests'] = all_tests
        context['induction_motor'] = induction_motor
        return context


class GeneratePDF(PDFView):
    def get(self, request, *args, **kwargs):
        config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
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
        motor.temperature_rise_test.save()

        response_data = {
            'voltage': motor.temperature_rise_test.voltage,
            'winding': motor.temperature_rise_test.winding,
            'frequency': motor.temperature_rise_test.frequency,
            'de_bearing': motor.temperature_rise_test.de_bearing,
            'nde_bearing': motor.temperature_rise_test.nde_bearing
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
        motor.no_load_test.save()

        response_data = {
            'voltage': motor.no_load_test.voltage,
            'current': motor.no_load_test.current,
            'power': motor.no_load_test.power,
            'frequency': motor.no_load_test.frequency,
            'speed': motor.no_load_test.speed,
            'direction_of_rotation': motor.no_load_test.direction_of_rotation
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
        motor.withstand_voltage_ac_test.save()

        response_data = {
            'description': motor.withstand_voltage_ac_test.description,
            'voltage_kv': motor.withstand_voltage_ac_test.voltage_kv,
            'time_in_seconds': motor.withstand_voltage_ac_test.time_in_seconds
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
        motor.insulation_resistance_test.save()

        response_data = {
            'description': motor.insulation_resistance_test.description,
            'voltage': motor.insulation_resistance_test.voltage,
            'insulation_resistance': motor.insulation_resistance_test.insulation_resistance,
            'time_in_seconds': motor.insulation_resistance_test.time_in_seconds,
            'ambient_temperature_C': motor.insulation_resistance_test.ambient_temperature_C,
            'humidity_percentage': motor.insulation_resistance_test.humidity_percentage
        }

        return JsonResponse(response_data)


class PerformanceDeterminationFormSave(View):

    def handle_file(self, file, obj, load=0):
        file_path = settings.MEDIA_ROOT / file.name

        with open(file_path, 'wb') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        wb = load_workbook(file_path)
        sheet = wb.active

        total_sum_current = 0
        count_current = 0
        total_sum_slip = 0
        count_slip = 0
        total_sum_speed = 0
        count_speed = 0
        total_sum_efficiency = 0
        count_efficiency = 0
        total_sum_cos = 0
        count_cos = 0

        for row in sheet.iter_rows(min_row=2, values_only=True):
            try:
                current = row[1]
                slip = row[2]
                speed = row[3]
                efficiency = row[4]
                cos = row[5]
                total_sum_current += current
                count_current += 1
                total_sum_slip += slip
                count_slip += 1
                total_sum_speed += speed
                count_speed += 1
                total_sum_efficiency += efficiency
                count_efficiency += 1
                total_sum_cos += cos
                count_cos += 1
            except IndexError:
                pass

        parameter = PerformanceTestParameters.objects.get_or_create(
            performance_determination_test=obj, load=load
        )[0]
        if count_current > 0:
            average_current = total_sum_current / count_current
            parameter.current = round(average_current, 2)
        else:
            parameter.current = Decimal('0.00')
        if count_slip > 0:
            average_slip = total_sum_slip / count_slip
            parameter.slip = round(average_slip, 4)
        else:
            parameter.slip = Decimal('0.0000')
        if count_speed > 0:
            average_speed = total_sum_speed / count_speed
            parameter.speed = round(average_speed, 2)
        else:
            parameter.speed = Decimal('0.00')
        if count_efficiency > 0:
            average_efficiency = total_sum_efficiency / count_efficiency
            parameter.efficiency = round(average_efficiency, 2)
        else:
            parameter.efficiency = Decimal('0.00')
        if count_cos > 0:
            average_cos = total_sum_cos / count_cos
            parameter.cos = round(average_cos, 2)
        else:
            parameter.cos = Decimal('0.00')
        parameter.load = load
        parameter.save()

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
        performance_determination_test.save()
        parent_obj = performance_determination_test
        file_1 = request.FILES.get('performance_determination_test-file_1')
        file_2 = request.FILES.get('performance_determination_test-file_2')
        file_3 = request.FILES.get('performance_determination_test-file_3')
        file_4 = request.FILES.get('performance_determination_test-file_4')
        if file_1:
            self.handle_file(file_1, parent_obj, 25)
        if file_2:
            self.handle_file(file_2, parent_obj, 50)
        if file_3:
            self.handle_file(file_3, parent_obj, 75)
        if file_4:
            self.handle_file(file_4, parent_obj, 100)

        response_data = {
            'voltage': motor.performance_determination_test.voltage,
            'frequency': motor.performance_determination_test.frequency,
            'nominal_t': motor.performance_determination_test.nominal_t,
        }
        if file_1:
            response_data['file_1'] = str(settings.MEDIA_ROOT / file_1.name or None)
        if file_2:
            response_data['file_2'] = str(settings.MEDIA_ROOT / file_2.name or None)
        if file_3:
            response_data['file_3'] = str(settings.MEDIA_ROOT / file_3.name or None)
        if file_4:
            response_data['file_4'] = str(settings.MEDIA_ROOT / file_4.name or None)

        return JsonResponse(response_data)


class ChartView(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'graph.html')