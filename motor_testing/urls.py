from django.urls import path

from .views import InductionMotorListingsView, TestsView, ReportView

urlpatterns = [
    path("home/", InductionMotorListingsView.as_view(), name="home"),
    path("tests/", TestsView.as_view(), name="tests"),
    path("report/<int:id>", ReportView.as_view(), name="report"),
]
