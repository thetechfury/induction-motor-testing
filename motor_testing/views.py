from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, FormView

from motor_testing.forms import MotorInductionForm, SearchForm
from motor_testing.models import InductionMotor


class InductionMotorListingsView(ListView):
    model = InductionMotor
    queryset = InductionMotor.objects.all().order_by("-updated_on")
    template_name = "listings.html"
    paginate_by = 10

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(serial_number__icontains=search_query)
        return queryset


class InductionMotorFormView(LoginRequiredMixin, FormView):
    form_class = MotorInductionForm
    template_name = "main_form.html"
