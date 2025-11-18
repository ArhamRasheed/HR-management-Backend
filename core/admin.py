from django.contrib import admin
from .models import *

# Register your models here.
# HRMS admin registrations will be added in future phases

admin.site.register(Department)
admin.site.register(Designation)
admin.site.register(Employee)
admin.site.register(LeaveType)
admin.site.register(LeaveApplication)
admin.site.register(InsurancePlan)
admin.site.register(EmployeeInsurance)
admin.site.register(Complaint)
admin.site.register(Payroll)
admin.site.register(Attendance)
admin.site.register(MonthlyCompanyReport)
admin.site.register(MonthlyEmployeeReport)
admin.site.register(InterviewedCandidate)
