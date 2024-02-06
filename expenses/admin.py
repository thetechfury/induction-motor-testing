from django.contrib import admin
from django.contrib.admin import register

from expenses.models import Expense


# Register your models here.

@register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'date', 'created_at', 'updated_at')
