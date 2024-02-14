from django.urls import path

from .views import InductionMotorFormView

urlpatterns = [
    path("home/", InductionMotorFormView.as_view(), name="home"),
]
