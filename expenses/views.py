from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View
from django.views.generic.list import ListView
from expenses.forms import ExpenseForm
from expenses.models import Expense


# Create your views here.


class Index(ListView):
    model = Expense
    template_name = 'test.html'
    context_object_name = 'expenses'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ExpenseForm()
        return context


class AddExpense(View):
    def post(self, request):
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect('index')


class UpdateExpense(View):

    def get(self, request, id):
        expense = Expense.objects.get(id=id)
        form = ExpenseForm(request.POST, instance=expense)
        serialized_expense = {
            'id': expense.id,
            'title': expense.title,
            'amount': expense.amount,
            'date': expense.date,
        }
        return JsonResponse({'expense': serialized_expense})

    def post(self, request, id):
        expense = Expense.objects.get(id=id)
        form = ExpenseForm(request.POST, instance=expense)

        if form.is_valid():
            form.save()
        return redirect('index')


class DeleteExpense(View):
    def post(self, request, id):
        expense = Expense.objects.get(id=id)
        expense.delete()
        return redirect('index')
