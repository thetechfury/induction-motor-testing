from django.urls import path
from expenses import views

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('add_expense', views.AddExpense.as_view(), name='add-expense'),
    path('edit_expense/<int:id>', views.UpdateExpense.as_view(), name='edit-expense'),
    path('delete_expense/<int:id>', views.DeleteExpense.as_view(), name='delete-expense'),
]