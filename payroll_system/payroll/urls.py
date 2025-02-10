from django.urls import path
from . import views

urlpatterns = [
    path('select_employee/', views.select_employee, name='select_employee'),
    path('payroll/<int:employee_id>/', views.payroll_form, name='payroll_form'),
    path('payroll/all/', views.all_payroll, name='all_payroll'),

    path('export/all_payroll/excel/', views.export_all_payroll_excel, name='export_all_payroll_excel'),
    path('export/all_payroll/pdf/', views.export_all_payroll_pdf, name='export_all_payroll_pdf'),
    path('export/payroll/<int:employee_id>/excel/', views.export_employee_payroll_excel, name='export_employee_payroll_excel'),
    path('export/payroll/<int:employee_id>/pdf/', views.export_employee_payroll_pdf, name='export_employee_payroll_pdf'),

    path('', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register_employee/', views.register_employee, name='register_employee'),
]
