from django.contrib import admin
from .models import Employee, KPI, Payroll

admin.site.register(Employee)
admin.site.register(KPI)
admin.site.register(Payroll)