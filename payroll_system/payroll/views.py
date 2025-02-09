from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Employee, Payroll, KPI
from .forms import *
from django.http import HttpResponse
from decimal import Decimal
from django.utils.timezone import now
import pandas as pd
from reportlab.pdfgen import canvas
import io

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect('dashboard')  # Redirect to the correct dashboard
    else:
        form = LoginForm()
    return render(request, 'payroll/login.html', {'form': form})


@login_required
def register_employee(request):
    if not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)  # Restrict to Admins only

    if request.method == "POST":
        form = EmployeeRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('select_employee')  # Redirect after successful registration
    else:
        form = EmployeeRegistrationForm()

    return render(request, 'payroll/register_employee.html', {'form': form})


@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect('select_employee')  # Admin Dashboard
    else:
        employee = Employee.objects.get(user=request.user)
        payroll = Payroll.objects.filter(employee=employee).order_by('-payroll_date').first()
        kpi = KPI.objects.filter(employee=employee).first()

        if payroll and kpi:
            calculated_data = calculate_payroll(payroll, kpi)
            return render(request, 'payroll/payroll_results.html', {
                'employee': employee,
                'payroll': payroll,
                'kpi': kpi,
                'calculated_data': calculated_data,
            })
        else:
            return render(request, 'payroll/no_payslip.html')  # Handle no payroll case

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


def select_employee(request):
    employees = Employee.objects.all()
    return render(request, 'payroll/select_employee.html', {'employees': employees})

def payroll_form(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)

    # Retrieve existing KPI record for this employee, or create a new one
    kpi, created = KPI.objects.get_or_create(employee=employee)
    payroll_form = PayrollForm()
    kpi_form = KPIForm(instance=kpi, employee=employee)

    if request.method == "POST":
        payroll_form = PayrollForm(request.POST)
        kpi_form = KPIForm(request.POST, instance=kpi, employee=employee)  # Use existing KPI instance

        if kpi_form.is_valid() and payroll_form.is_valid():
            kpi = kpi_form.save(commit=False)
            kpi.employee = employee
            kpi.save()  # Save without creating a duplicate

            payroll = payroll_form.save(commit=False)
            payroll.employee = employee
            payroll.save()

            return render(request, 'payroll/payroll_results.html', {
                'employee': employee,
                'kpi': kpi,
                'payroll': payroll,
                'calculated_data': calculate_payroll(payroll, kpi),
            })

    return render(request, 'payroll/payroll_form.html', {
        'employee': employee,
        'payroll_form': payroll_form,
        'kpi_form': kpi_form,
    })


def calculate_payroll(payroll, kpi):
    daily_pay = Decimal(payroll.employee.basic_salary) / Decimal(30)
    scheduled_working_day = payroll.scheduled_working_days_input - payroll.unjustified + payroll.working_day_adjustment
    total_overtime_days = Decimal((payroll.work_days * 1.5) + (payroll.sunday * 2) + (payroll.holiday * 2.5))
    total_absence_days = Decimal((payroll.justified) + (payroll.unjustified * 3) + (payroll.tardiness_vl * 0.5))
    paid_salary = daily_pay * Decimal(scheduled_working_day)

    non_taxable_transport_allowance = Decimal(2200) if (scheduled_working_day * daily_pay) > Decimal(8800) else (scheduled_working_day * daily_pay) / Decimal(4)
    overtime_payment = daily_pay * total_overtime_days
    deduction = total_absence_days * daily_pay

    attendance_bonus = Decimal(833.14) if payroll.tardiness_l == 0 and payroll.tardiness_vl == 0 else Decimal(0)
    misconduct_penalty = kpi.misconduct * Decimal(1000)

    # KPI Fields (Only for Call Agent)
    call_flow = aht = pickup = improvement = Decimal(0)
    if payroll.employee.position == "Call Agent":
        if kpi.call_flow_input and kpi.call_flow_input <= 2.8:
            call_flow = Decimal(0)
        elif kpi.call_flow_input <= 2.84:
            call_flow = Decimal(416.57)
        elif kpi.call_flow_input <= 2.94:
            call_flow = Decimal(833.14)
        else:
            call_flow = Decimal(1249.71)

        if kpi.aht_input and kpi.aht_input <= 5:
            aht = Decimal(1249.71)
        
        if kpi.pickup_input == 0 or kpi.pickup_input > 20:
            pickup = Decimal(0)
        else:
            pickup = Decimal(1249.71)

        if kpi.impv_input and kpi.impv_input > 0:
            improvement = Decimal(624.86)

    bonus = call_flow + aht + pickup + attendance_bonus + improvement - misconduct_penalty
    gross_income = bonus - deduction + overtime_payment + non_taxable_transport_allowance + paid_salary
    gross_taxable_income = gross_income - non_taxable_transport_allowance

    # Tax Calculation
    tax_brackets = [
        (600, 0, 0), (1650, 0.1, 60), (3200, 0.15, 142.5), (5250, 0.2, 302.5),
        (7800, 0.25, 565), (10900, 0.3, 955), (float('inf'), 0.35, 1500)
    ]
    income_tax = Decimal(0)
    for limit, rate, deduction_amount in tax_brackets:
        if gross_taxable_income <= Decimal(limit):
            income_tax = (Decimal(rate) * gross_taxable_income) - Decimal(deduction_amount)
            break

    employee_pension = paid_salary * Decimal(0.07)
    employer_pension = paid_salary * Decimal(0.11)
    total_pension = employee_pension + employer_pension
    total_deduction = income_tax + employee_pension
    net_salary = gross_income - total_deduction
    
    # Only include Call Agent KPI fields if employee is a Call Agent
    if payroll.employee.position == "Call Agent":
        call_agent_kpi = {
            'call_flow': round(call_flow, 2),
            'aht': round(aht, 2),
            'pickup': round(pickup, 2),
            'improvement': round(improvement, 2),
        }
    else:
        call_agent_kpi = {}  # Hide these fields for other positions

    return {
        'daily_pay': round(daily_pay, 2),
        'scheduled_working_day': round(scheduled_working_day, 2),
        'total_overtime_days': round(total_overtime_days, 2),
        'total_absence_days': round(total_absence_days, 2),
        'paid_salary': round(paid_salary, 2),
        'overtime_payment': round(overtime_payment, 2),
        'non_taxable_transport_allowance': round(non_taxable_transport_allowance, 2),
        'deduction': round(deduction, 2),
        'attendance_bonus': round(attendance_bonus, 2),
        'bonus': round(bonus, 2),
        'gross_income': round(gross_income, 2),
        'gross_taxable_income': round(gross_taxable_income, 2),
        'income_tax': round(income_tax, 2),
        'employee_pension': round(employee_pension, 2),
        'employer_pension': round(employer_pension, 2),
        'total_pension': round(total_pension, 2),
        'total_deduction': round(total_deduction, 2),
        'net_salary': round(net_salary, 2),
        **call_agent_kpi,  # Merges Call Agent KPI fields if applicable
}


def all_payroll(request):
    employees = Employee.objects.all()
    payroll_data = []
    
    # Get current month and year
    current_month = now().strftime("%B")
    current_year = now().year

    for employee in employees:
        # Fetch the latest payroll record for each employee (if exists)
        payroll = Payroll.objects.filter(employee=employee).order_by('-payroll_date').first()
        kpi = KPI.objects.filter(employee=employee).first()

        if payroll and kpi:
            calculated_data = calculate_payroll(payroll, kpi)
        else:
            calculated_data = None  # No payroll record found

        payroll_data.append({
            'employee': employee,
            'payroll': payroll,
            'kpi': kpi,
            'calculated_data': calculated_data
        })

    return render(request, 'payroll/all_payroll.html', {
        'payroll_data': payroll_data,
        'current_month': current_month,
        'current_year': current_year,
    })


def export_excel(request):
    employees = Employee.objects.all()
    df = pd.DataFrame(list(employees.values('name', 'position', 'basic_salary')))
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="payroll.xlsx"'
    df.to_excel(response, index=False)
    return response

def export_pdf(request):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Payroll Report")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')


