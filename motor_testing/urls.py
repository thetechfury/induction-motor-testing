from django.urls import path

from .views import InductionMotorListingsView, TestsView, ReportView, GeneratePDF, DeleteReportView, ElectricFormSaveView, TemperatureFormSaveView

urlpatterns = [
    path("home/", InductionMotorListingsView.as_view(), name="home"),
    path("tests/<int:pk>", TestsView.as_view(), name="tests"),
    path("report/<int:id>", ReportView.as_view(), name="report"),
    path("report/<int:id>/delete", DeleteReportView.as_view(), name="delete-report"),
    path("electric-form/<int:id>", ElectricFormSaveView.as_view(), name="electric-form"),
    path("temperature-form/<int:id>", TemperatureFormSaveView.as_view(), name="temperature-form"),
    # path('pdf/<int:id>', GeneratePDF.as_view(), name='pdf'),
]
