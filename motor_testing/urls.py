from django.urls import path

from .views import InductionMotorListingsView, TestsView, ReportView, GeneratePdf

urlpatterns = [
    path("home/", InductionMotorListingsView.as_view(), name="home"),
    path("tests/<int:pk>", TestsView.as_view(), name="tests"),
    path("report/<int:id>", ReportView.as_view(), name="report"),
    path('pdf/', GeneratePdf.as_view(), name='pdf'),
]
