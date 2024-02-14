from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, FormView

from motor_testing.forms import MotorInductionForm
from motor_testing.models import InductionMotor


class InductionMotorListingsView(ListView):
    model = InductionMotor
    queryset = InductionMotor.objects.all().order_by("-updated_on")
    template_name = "listings.html"
    paginate_by = 10


class InductionMotorFormView(LoginRequiredMixin, FormView):
    form_class = MotorInductionForm
    template_name = "main_form.html"
