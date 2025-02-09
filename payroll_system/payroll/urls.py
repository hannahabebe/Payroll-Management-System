from django.urls import path
from . import views

urlpatterns = [
    path('select_employee/', views.select_employee, name='select_employee'),
    path('payroll/<int:employee_id>/', views.payroll_form, name='payroll_form'),
    path('payroll/all/', views.all_payroll, name='all_payroll'), 
    path('export/excel/', views.export_excel, name='export_excel'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),

    path('', views.user_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register_employee/', views.register_employee, name='register_employee'),
]
