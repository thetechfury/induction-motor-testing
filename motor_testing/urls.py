from django.urls import path

from .views import InductionMotorListingsView, TestsView, ReportView, GeneratePDF, DeleteReportView

urlpatterns = [
    path("home/", InductionMotorListingsView.as_view(), name="home"),
    path("tests/<int:pk>", TestsView.as_view(), name="tests"),
    path("report/<int:id>", ReportView.as_view(), name="report"),
    path("report/<int:id>/delete", DeleteReportView.as_view(), name="delete-report"),
    # path('pdf/<int:id>', GeneratePDF.as_view(), name='pdf'),
]
