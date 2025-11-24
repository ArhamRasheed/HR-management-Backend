from django.db import models

# Create your models here.
# HRMS models will be added in future phases

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password


class Designation(models.Model):
    designation_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'designations'
        ordering = ['designation_name']

    def __str__(self):
        return self.designation_name


class Department(models.Model):
    department_name = models.CharField(max_length=255)
    manager = models.ForeignKey('Employee', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_department')
    manager_start_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'
        ordering = ['department_name']

    def __str__(self):
        return self.department_name


class Employee(models.Model):
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', 'Active'),
        ('terminated', 'Terminated'),
        ('resigned', 'Resigned'),
        ('fired', 'Fired'),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True, related_name='employees')
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, blank=True, related_name='employees')
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    password_hash = models.CharField(max_length=255, blank=True, null=True, help_text="Only for HR department employees")
    joining_date = models.DateField()
    termination_date = models.DateField(null=True, blank=True)
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='active')
    basic_salary = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        db_table = 'employees'
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} - {self.designation}"

    def set_password(self, raw_password):
        """Hash and set password for HR employees"""
        self.password_hash = make_password(raw_password)


class LeaveType(models.Model):
    leave_type_name = models.CharField(max_length=100)
    max_days_per_year = models.IntegerField()
    is_paid = models.BooleanField(default=True)
    policy_description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'leave_types'
        ordering = ['leave_type_name']

    def __str__(self):
        return f"{self.leave_type_name} ({self.max_days_per_year} days)"


class LeaveApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='applications')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_date = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'leave_applications'
        ordering = ['-applied_date']
        indexes = [
            models.Index(fields=['employee']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.leave_type_name} ({self.start_date} to {self.end_date})"


class InsurancePlan(models.Model):
    plan_name = models.CharField(max_length=255)
    coverage_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    premium_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    policy_terms = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'insurance_plans'
        ordering = ['plan_name']

    def __str__(self):
        return self.plan_name


class EmployeeInsurance(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='insurances')
    insurance_plan = models.ForeignKey(InsurancePlan, on_delete=models.PROTECT, related_name='employee_insurances')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    monthly_deduction = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'employee_insurance'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.insurance_plan.plan_name}"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='complaints')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    filed_date = models.DateField(auto_now_add=True)
    resolved_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'complaints'
        ordering = ['-filed_date']
        indexes = [
            models.Index(fields=['employee']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.subject}"


class Payroll(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='payrolls', null=True)
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    bonuses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    bonus_reason = models.TextField(blank=True, null=True)
    deductions = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    deduction_reason = models.TextField(blank=True, null=True)
    net_salary = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'payroll'
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']
        indexes = [
            models.Index(fields=['employee']),
            models.Index(fields=['month', 'year']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.month}/{self.year}"

    def calculate_net_salary(self):
        """Calculate net salary: basic + bonuses - deductions"""
        self.net_salary = self.employee.basic_salary + self.bonuses - self.deductions
        return self.net_salary


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late')
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    attendance_date = models.DateField()
    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present')

    class Meta:
        db_table = 'attendance'
        unique_together = ['employee', 'attendance_date']
        ordering = ['-attendance_date']
        indexes = [
            models.Index(fields=['employee']),
            models.Index(fields=['attendance_date']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.attendance_date}"

    def calculate_working_hours(self):
        """Calculate working hours from check_in and check_out times"""
        if self.check_in_time and self.check_out_time:
            from datetime import datetime, timedelta
            check_in = datetime.combine(datetime.today(), self.check_in_time)
            check_out = datetime.combine(datetime.today(), self.check_out_time)
            delta = check_out - check_in
            return delta.total_seconds() / 3600  # Return hours
        return 0


class MonthlyEmployeeReport(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='monthly_reports')
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    report_file = models.TextField(blank=True, null=True, help_text="File path for .txt report")
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_employee_reports'
        unique_together = ['employee', 'month', 'year']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.employee.full_name} - {self.month}/{self.year}"


class MonthlyCompanyReport(models.Model):
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    year = models.IntegerField()
    report_file = models.TextField(blank=True, null=True, help_text="File path for .txt report")
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'monthly_company_reports'
        unique_together = ['month', 'year']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"Company Report - {self.month}/{self.year}"


class InterviewedCandidate(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected')
    ]

    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    applied_position = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='candidates')
    interview_date = models.DateField(null=True, blank=True)
    interviewer = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name='conducted_interviews')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    remarks = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'interviewed_candidates'
        ordering = ['-interview_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['department']),
            models.Index(fields=['applied_position']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.applied_position}"