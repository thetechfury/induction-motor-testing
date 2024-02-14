from django.shortcuts import render
from django.views.generic import ListView
from motor_testing.models import InductionMotor

# Create your views here.


class InductionMotorListingsView(ListView):
    model = InductionMotor
    queryset = InductionMotor.objects.all().order_by("-updated_on")
    template_name = "listings.html"
    paginate_by = 10
