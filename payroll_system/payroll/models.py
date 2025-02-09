from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    POSITION_CHOICES = [
        ('Software Developer', 'Software Developer'),
        ('IT Support', 'IT Support'),
        ('Call Agent', 'Call Agent'),
        ('Supervisor', 'Supervisor'),
    ]

    name = models.CharField(max_length=255)
    position = models.CharField(max_length=50, choices=POSITION_CHOICES)
    tin_number = models.CharField(max_length=20, unique=True)
    employment_date = models.DateField(default=now)
    separation_date = models.DateField(null=True, blank=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.position}"

class KPI(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE)
    attendance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    misconduct = models.IntegerField(default=0)

    # Only for Call Agents
    call_flow_input = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    aht_input = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pickup_input = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    impv_input = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"KPI for {self.employee.name}"

class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    payroll_date = models.DateField(default=now)
    scheduled_working_days_input = models.IntegerField(default=30, verbose_name="Scheduled Working Days")
    working_day_adjustment = models.IntegerField(default=0)
    work_days = models.IntegerField(default=0)
    sunday = models.IntegerField(default=0)
    holiday = models.IntegerField(default=0)
    justified = models.IntegerField(default=0)
    unjustified = models.IntegerField(default=0)
    tardiness_l = models.IntegerField(default=0)
    tardiness_vl = models.IntegerField(default=0)

    def __str__(self):
        return f"Payroll for {self.employee.name} - {self.payroll_date}"
