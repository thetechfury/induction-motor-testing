from django.urls import path

from .views import InductionMotorListingsView, TestsView

urlpatterns = [
    path("listings/", InductionMotorListingsView.as_view(), name="listings"),
    path("tests/", TestsView.as_view(), name="tests"),
]
