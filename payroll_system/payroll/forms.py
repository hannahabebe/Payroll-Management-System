from django import forms
from django.contrib.auth.models import User
from .models import Payroll, KPI, Employee

# Form for employee account creation
class EmployeeRegistrationForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = Employee
        fields = ['name', 'position', 'tin_number', 'employment_date', 'basic_salary']

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            is_staff=False  # Employees are not admins
        )
        employee = super().save(commit=False)
        employee.user = user
        if commit:
            employee.save()
        return employee

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

# Form for Payroll model, excluding employee and payroll_date fields
class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        exclude = ['employee', 'payroll_date']  # These fields are handled separately
        widgets = {
            # Applying Bootstrap and placeholders styles to input fields
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter basic salary'}),
            'overtime': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter overtime hours'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter bonus amount'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styles to all fields dynamically
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm', 'style': 'max-width: 250px;'})  # Add Bootstrap small class & width

# Form for KPI model, excluding employee and attendance fields
class KPIForm(forms.ModelForm):
    class Meta:
        model = KPI
        exclude = ['employee', 'attendance']  # These fields are handled separately
        widgets = {
            # Applying Bootstrap and placeholders styles to input fields
            'call_flow_input': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter call flow score'}),
            'aht_input': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter AHT score'}),
            'pickup_input': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter pickup score'}),
            'impv_input': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'style': 'max-width: 250px;', 'placeholder': 'Enter improvement score'}),
        }

    def __init__(self, *args, **kwargs):
        employee = kwargs.pop('employee', None) # Extract employee instance if provided
        super().__init__(*args, **kwargs)

        # Remove specific KPI fields for employees who are not Call Agents
        if employee and employee.position != 'Call Agent':
            self.fields.pop('call_flow_input', None)
            self.fields.pop('aht_input', None)
            self.fields.pop('pickup_input', None)
            self.fields.pop('impv_input', None)

        # Apply Bootstrap styles to all fields dynamically
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm', 'style': 'max-width: 250px;'})  
