from django.urls import path

from .views import InductionMotorListingsView, TestsView, ReportView, GeneratePDF, DeleteReportView, \
    ElectricFormSaveView, TemperatureFormSaveView, NoLoadFormSaveView, WithStandVoltageFormSaveView, \
    InsulationFormSaveView, PerformanceDeterminationFormSave

urlpatterns = [
    path("home/", InductionMotorListingsView.as_view(), name="home"),
    path("tests/<int:pk>", TestsView.as_view(), name="tests"),
    path("report/<int:id>", ReportView.as_view(), name="report"),
    path("report/<int:id>/delete", DeleteReportView.as_view(), name="delete-report"),
    path("electric-form/<int:id>", ElectricFormSaveView.as_view(), name="electric-form"),
    path("temperature-form/<int:id>", TemperatureFormSaveView.as_view(), name="temperature-form"),
    path("noload-form/<int:id>", NoLoadFormSaveView.as_view(), name="noload-form"),
    path("withstand-form/<int:id>", WithStandVoltageFormSaveView.as_view(), name="withstand-form"),
    path("insulation-form/<int:id>", InsulationFormSaveView.as_view(), name="insulation-form"),
    path("performance-form/<int:id>", PerformanceDeterminationFormSave.as_view(), name="performance-form"),
    path('pdf/<int:id>', GeneratePDF.as_view(), name='pdf'),
]
