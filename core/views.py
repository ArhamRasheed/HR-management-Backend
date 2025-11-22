from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
from django.http import JsonResponse
from .models import Employee, EmployeeInsurance, Payroll, Department, Designation, Attendance, LeaveApplication, LeaveType, InsurancePlan, InterviewedCandidate, Complaint, MonthlyCompanyReport, MonthlyEmployeeReport
from django.contrib.auth.hashers import check_password
from datetime import date, timedelta, datetime
import secrets
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from .decorators import hr_required
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.hashers import make_password
from django.db.models import Count, Sum
import random


allowed_positions_for_departments = {
    'IT': ['Software Engineer', 'CTO', 'System Administrator', 'CEO', 'Manager'],
    'HR': ['Manager', 'Recruiter', 'CEO'],
    'Finance': ['Accountant', 'Financial Analyst', 'CEO', 'Manager'],
    'Sales': ['Sales Executive', 'Manager', 'CEO'],
    'Marketing': ['Marketing Executive', 'Manager', 'CEO'],
}

salaries = {
    'Software Engineer': 80000,
    'CTO': 150000, 
    'System Administrator' : 60000, 
    'CEO': 2500000, 
    'Manager': 100000,
    'Recruiter': 40000,
    'Accountant': 30000, 
    'Financial Analyst': 120000,
    'Sales Executive': 55000,
    'Marketing Executive': 65000
}

def make_active_inactive():
    active_plans = EmployeeInsurance.objects.filter(
        end_date__lt=date.today(), 
        status='active')
    active_plans.update(status='inactive')
    inactive_employee_plans = EmployeeInsurance.objects.exclude(
        employee__employment_status='active'
    )

    inactive_employee_plans.update(status='inactive')
    
    

def add_employee(full_name, phone, applied_position, department):
    if applied_position.designation_name == 'CEO':
        ceos = Employee.objects.filter(designation__designation_name='CEO', employment_status='active')
        if ceos.exists():
            return False
    if applied_position.designation_name == 'CTO' and (not department.department_name == 'IT' or Employee.objects.filter(designation__designation_name='CTO').exists()):
        return False
    if applied_position.designation_name not in allowed_positions_for_departments.get(department.department_name, []):
        return False
    if Employee.objects.get(email=full_name.replace(" ", "_").lower() + "@example.com").exists():
        return False
    if department.department_name == 'HR':
        pass_word = make_password(full_name.split()[0].lower())
    else:
        pass_word = None
    employee = Employee.objects.create(
        full_name=full_name, 
        email=full_name.replace(" ", "_").lower() + "@example.com",
        phone=phone, 
        password_hash=pass_word,
        department=department, 
        employment_status="active",
        designation=applied_position,
        joining_date=timezone.now().date(),
        basic_salary=salaries[applied_position.designation_name]
    )
    if (department.manager is None or department.manager.employment_status != 'active') and applied_position.designation_name == 'Manager':
        department.manager = employee
        department.manager_start_date = timezone.now().date()
        department.save()
    return True

@api_view(['DELETE'])
@permission_classes([AllowAny])
@hr_required
def delete_employee(request, employee_id):
    try:
        Employee.objects.filter(id=employee_id).delete()
        return JsonResponse({'message': 'Employee deleted successfully.'})
    except Employee.DoesNotExist:
        return JsonResponse({'message': 'Employee not found'})
    


@api_view(['PUT', 'GET'])
@permission_classes([AllowAny])
@hr_required
def update_employee(request, employee_id): #update
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if not to_update or not new_val:
        return JsonResponse({'message': 'No data provided for update.'}, status=400)
    try:
        emp = Employee.objects.get(id=employee_id, employment_status='active')
    except Employee.DoesNotExist:
        return JsonResponse({'message': 'Invalid ID for update.'}, status=400)
    if to_update == 'phone':
        emp.phone=new_val
        emp.save()
        return JsonResponse({'message': 'Employee phone updated successfully.'})
    elif to_update == 'designation':
        if not Designation.objects.filter(designation_name=new_val).exists():
            return JsonResponse({'message': 'Designation does not exist.'}, status=400)
        if new_val == 'CEO':
            ceo_designation = Designation.objects.get(designation_name='CEO')

            ceos = Employee.objects.filter(
            designation=ceo_designation,
            employment_status='active'
            )
            if ceos.exists():
                return JsonResponse({'message': 'CEO already exists.'}, status=400)
        elif new_val == 'CTO' and not Employee.objects.filter(id=employee_id).first().department.department_name == 'IT':
            return JsonResponse({'message': 'Only IT department can have CTO designation.'}, status=400)
        elif new_val == 'CTO' and Employee.objects.filter(designation__designation_name='CTO', employment_status='active').exists():
            return JsonResponse({'message': 'CTO already exists.'}, status=400)
        if new_val not in Designation.objects.values_list('designation_name', flat=True):
            return JsonResponse({'message': 'Designation does not exist.'}, status=400)
        if new_val not in allowed_positions_for_departments.get(
            emp.department.department_name, []
            ):
            return JsonResponse ({"message": "Invalid Designation"})
        new_designation = Designation.objects.get(designation_name=new_val)
        emp.designation = new_designation
        if new_designation.designation_name == 'Manager' and emp.department.manager.employment_status in ['fired', 'terminated', 'resigned']:
            emp.department.manager = emp
        emp.save()
        return JsonResponse({'message': 'Employee designation updated successfully.'})
    elif to_update == 'status':
        if new_val in ['fired', 'terminated', 'resigned']:
            if emp.employment_status == 'active':
                emp.employment_status = new_val
                emp.termination_date = date.today()
                emp.save()
                active_insurances = EmployeeInsurance.objects.filter(employee=emp, status='active')
                active_insurances.update(status='inactive')
                open_com = Complaint.objects.filter(employee=emp, status='open')
                open_com.update(status='closed')
                return JsonResponse({'message': 'Employee status updated successfully.'})
            else:
                return JsonResponse({'message': "Inactive employees can't be updated"})
    elif to_update == 'salary':
        if Decimal(new_val) <= Decimal('0.00'):
            return JsonResponse({'message': "Salary can't be less than or equal to 0"}, status=404)
        if Decimal(new_val) < Decimal(salaries[emp.designation.designation_name]):
            return JsonResponse({'message': "Minimum Salary is defined"}, status=404)
        emp.basic_salary = new_val
        emp.save()
        return JsonResponse({'message': "Salary updated successfully"},status=200)

@api_view(['POST'])
@permission_classes([AllowAny])
@hr_required
def add_department(request):
    data = json.loads(request.body)
    department_name = data.get('department_name')
    if not department_name:
        return JsonResponse({'message': 'No department name provided.'}, status=400)
    if Department.objects.filter(department_name=department_name).exists():
        return JsonResponse({'message': 'Department already exists.'}, status=400)
    Department.objects.create(department_name=department_name)
    return JsonResponse({'message': 'Department added successfully.'})

# @api_view(['DELETE'])
# @permission_classes([AllowAny])
# @hr_required
# def delete_department(request, department_name):
#     Department.objects.filter(department_name=department_name).delete()
#     return JsonResponse({'message': 'Department deleted successfully.'})

@api_view(['PUT', 'GET'])
@permission_classes([AllowAny])
@hr_required
def update_department(request, department_name): #update
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if to_update == 'department_name':
        if Department.objects.filter(department_name=new_val).exists():
            return JsonResponse({'message': 'Department already exists.'}, status=400)
        dep = Department.objects.get(department_name=department_name)
        dep.department_name=new_val
        dep.save()
        return JsonResponse ({'message': 'Department name updated successfully.'})

# @api_view(['POST'])
# @permission_classes([AllowAny])
# @hr_required
# def add_designation(request):
#     data = json.loads(request.body)
#     designation_name = data.get('designation_name')
#     if not designation_name:
#         return JsonResponse({'message': 'No designation name provided.'}, status=400)
#     if Designation.objects.filter(designation_name=designation_name).exists():
#         return JsonResponse({'message': 'Designation already exists.'}, status=400)
#     Designation.objects.create(designation_name=designation_name)
#     return JsonResponse({'message': 'Designation added successfully.'})


# @api_view(['DELETE'])
# @permission_classes([AllowAny])
# @hr_required
# def delete_designation(request, designation_name):
#     Designation.objects.filter(designation_name=designation_name).delete()
#     return JsonResponse({'message': 'Designation deleted successfully.'})


@api_view(['PUT', 'GET'])
@permission_classes([AllowAny])
@hr_required
def update_designation(request, designation_name): #update
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if to_update == 'designation_name':
        if Designation.objects.filter(designation_name=new_val).exists():
            return JsonResponse({'message': 'Designation already exists.'}, status=400)
        des = Designation.objects.get(designation_name=designation_name)
        des.designation_name=new_val
        des.save()
        return JsonResponse ({'message': 'Designation name updated successfully.'})

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint to verify API is running.
    """
    return Response({
        'status': 'healthy',
        'message': 'HRMS API is running successfully',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)

    
@api_view(['GET'])
@permission_classes([AllowAny])
def check_session_view(request):
    if not request.session.get('employee_id'):
        return JsonResponse({"authenticated": False})
    return JsonResponse({
        "authenticated": True,
        "user": {
            "id": request.session.get('employee_id'),
            "email": request.session.get('email'),
            "full_name": request.session.get('full_name'),
            "department": request.session.get('department'),
            "designation": request.session.get('designation')
        }
    })



@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({
                'success': False,
                'message': 'Email and password are required'
            }, status=400)
        try:
            employee = Employee.objects.get(email=email, employment_status='active')
        except Employee.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)

        if not employee.password_hash:
            return JsonResponse({
                'success': False,
                'message': 'Access denied. Only HR employees can login.'
            }, status=403)

        if check_password(password, employee.password_hash):
            request.session['employee_id'] = employee.id
            request.session['full_name'] = employee.full_name
            request.session['email'] = employee.email
            request.session['department'] = employee.department.department_name if employee.department else None
            request.session['designation'] = employee.designation.designation_name if employee.designation else None
            request.session.set_expiry(0)
            request.session.save()
            return JsonResponse({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': employee.id,
                    'email': employee.email,
                    'full_name': employee.full_name,
                    'department': employee.department.department_name if employee.department else None,
                    'designation': employee.designation.designation_name if employee.designation else None
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Invalid credentials'
            }, status=401)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)
    

@api_view(['GET'])
@permission_classes([AllowAny])
def logout_view(request):
    request.session.flush()
    return JsonResponse({
        'success': True,
        'message': 'Logged out successfully'
    })
    

@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def dashboard_view(request):
    make_active_inactive()
    total_active_employees = Employee.objects.filter(employment_status="active").count()

    present_today = Attendance.objects.filter(status="present").count()
    absent_today = Attendance.objects.filter(status="absent").count()
    total_attendance = present_today + absent_today

    if total_attendance > 0:
        presence_ratio = round(present_today / total_attendance, 2)
        absence_ratio = round(absent_today / total_attendance, 2)
    else:
        presence_ratio = 0
        absence_ratio = 0

    unresolved_complaints = Complaint.objects.filter(status="open").count()

    total_insurances = EmployeeInsurance.objects.count()
    
    today = date.today()
    start_of_month = today.replace(day=1)

    new_hires = Employee.objects.filter(joining_date__gte=start_of_month, joining_date__lte=today).count()

    total_departments = Department.objects.count()

    employees_per_department = Employee.objects.values('department__department_name').annotate(
        count=Count('id')
    )

    pending_leaves = LeaveApplication.objects.filter(status="pending").count()

    total_payroll = Payroll.objects.aggregate(
        total=Sum('net_salary')
    )['total'] or 0

    dept_emp_list = [
        {"department": d['department__department_name'], "employee_count": d['count']}
        for d in employees_per_department
    ]

    return JsonResponse({
        "total_active_employees": total_active_employees,
        "presence_ratio": presence_ratio,
        "absence_ratio": absence_ratio,
        "unresolved_complaints": unresolved_complaints,
        "total_insurances": total_insurances,
        "new_hires_this_month": new_hires,
        "total_departments": total_departments,
        "employees_per_department": dept_emp_list,
        "pending_leaves": pending_leaves,
        "total_payroll": float(total_payroll)
    }, status=200)

@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def employee_list_view(request):
    employees = Employee.objects.all()
    employee_data = [
        {
            'id': emp.id,
            'full_name': emp.full_name,
            'email': emp.email,
            'phone_number': emp.phone,
            'employment_status': emp.employment_status,
            'joining_date': emp.joining_date,
            'termination_date': emp.termination_date if emp.termination_date else 'N/A'
        }
        for emp in employees
    ]
    return JsonResponse({'employees': employee_data})
    
@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def employee_detail_view(request):
    employee_id = request.GET.get('employee_id')
    if not employee_id:
        return JsonResponse({'message': 'No employee ID provided.'}, status=400)
    employee = Employee.objects.filter(id=employee_id).first()
    if not employee:
        return JsonResponse({'message': 'Employee not found.'}, status=404)
    return JsonResponse({
        'full_name': employee.full_name,
        'email': employee.email,
        'phone_number': employee.phone,
        'department': employee.department.department_name if employee.department else None,
        'designation': employee.designation.designation_name if employee.designation else None,
        'employment_status': employee.employment_status,
        'joining_date': employee.joining_date,
        'termination_date': employee.termination_date if employee.termination_date else 'N/A'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def department_list_view(request):
    departments = Department.objects.all()
    department_data = [
        {
            'id': dept.id,
            'department_name': dept.department_name,
        }
        for dept in departments
    ]
    return JsonResponse({'departments': department_data})   



@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def designation_list_view(request):
    designations = Designation.objects.all()
    designation_data = [
        {
            'id': desig.id,
            'designation_name': desig.designation_name,
        }
        for desig in designations
    ]
    return JsonResponse({'designations': designation_data})

@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def shortlisted_candidate_list_view(request):
    candidates = InterviewedCandidate.objects.filter(status='shortlisted')
    candidate_data = [
        {
            'id': candidate.id,
            'full_name': candidate.full_name,
            'email': candidate.email,
            'phone_number': candidate.phone,
            'position_applied': candidate.applied_position.designation_name if candidate.applied_position else None,
            'interview_date': candidate.interview_date,
            'status': candidate.status,
            'remarks': candidate.remarks,
            'department': candidate.department.department_name if candidate.department else None,
            'interviewer': candidate.interviewer.full_name if candidate.interviewer else None
        }
        for candidate in candidates
    ]
    return JsonResponse({'shortlisted_candidates': candidate_data})

@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def candidate_list_view(request):
    candidates = InterviewedCandidate.objects.all()
    candidate_data = [
        {
            'id': candidate.id,
            'full_name': candidate.full_name,
            'email': candidate.email,
            'phone_number': candidate.phone,
            'position_applied': candidate.applied_position.designation_name if candidate.applied_position else None,
            'interview_date': candidate.interview_date,
            'status': candidate.status,
            'remarks': candidate.remarks,
            'department': candidate.department.department_name if candidate.department else None,
            'interviewer': candidate.interviewer.full_name if candidate.interviewer else None
        }
        for candidate in candidates
    ]
    return JsonResponse({'all_candidates': candidate_data})

@api_view(['POST'])
@permission_classes([AllowAny])
@hr_required
def hire_employee_view(request):
    data = json.loads(request.body)
    candidate_id = data.get('candidate_id')
    if not candidate_id:
        return JsonResponse({'message': 'No candidate ID provided.'}, status=400)
    candidate = InterviewedCandidate.objects.filter(id=candidate_id, status='shortlisted').first()
    if not candidate:
        return JsonResponse({'message': 'Candidate not found or not shortlisted.'}, status=404)
    if(add_employee(candidate.full_name, candidate.phone, candidate.applied_position, candidate.department)):
        candidate.delete()
        return JsonResponse({'message': 'Employee hired successfully.'})
    else:
        return JsonResponse({'message': 'Something went wrong.'}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def reports_view(request):
    doc_type = request.GET.get('doc_type')
    month = request.GET.get('month')
    year = request.GET.get('year')
    if 'company_report' in doc_type and 'employee_report' in doc_type:
        if month and year:
            c_reports = MonthlyCompanyReport.objects.filter(month=month, year=year)
            e_reports = MonthlyEmployeeReport.objects.filter(month=month, year=year)
        else:
            c_reports = MonthlyCompanyReport.objects.all()
            e_reports = MonthlyEmployeeReport.objects.all()
        return JsonResponse({
            'company_reports': list(c_reports.values()),
            'employee_reports': list(e_reports.values())
        })
    elif 'company_report' in doc_type:
        if month and year:
            c_reports = MonthlyCompanyReport.objects.filter(month=month, year=year)
        else:
            c_reports = MonthlyCompanyReport.objects.all()
        return JsonResponse({
            'company_reports': list(c_reports.values())
        })
    elif 'employee_report' in doc_type:
        if month and year:
            e_reports = MonthlyEmployeeReport.objects.filter(month=month, year=year)
        else:
            e_reports = MonthlyEmployeeReport.objects.all()
        return JsonResponse({
            'employee_reports': list(e_reports.values())
        })
    else:
        return JsonResponse({
            'message': 'Invalid document type requested.'
        }, status=400)
    
@api_view(['GET'])
@permission_classes([AllowAny])
def department_view(request):
    department_name = request.GET.get('department_name')
    if not department_name:
        return JsonResponse({'message': 'No department name provided.'}, status=400)
    department = Department.objects.filter(department_name=department_name).first()
    if not department:
        return JsonResponse({'message': 'Department not found.'}, status=404)
    employees = [
            {
                'full_name': emp.full_name,
                'email': emp.email,
                'phone_number': emp.phone,
                'designation': emp.designation.designation_name if emp.designation else None,
                'employment_status': emp.employment_status,
                'joining_date': emp.joining_date,
                'termination_date': emp.termination_date if emp.termination_date else 'N/A'
            }
            for emp in Employee.objects.filter(department=department, employment_status='active')   
        ]
    return JsonResponse({
        'department_name': department.department_name,
        'total_employees': Employee.objects.filter(department=department).count(),
        'employees': employees
    })


@api_view(['GET'])
@permission_classes([AllowAny])
@hr_required
def old_employee_records_view(request):
    old_employees = Employee.objects.filter(termination_date__isnull=False)
    old_employees_data = [
        {
            'full_name': emp.full_name,
            'email': emp.email,
            'phone_number': emp.phone,
            'department': emp.department.department_name if emp.department else None,
            'designation': emp.designation.designation_name if emp.designation else None,
            'joining_date': emp.joining_date,
            'termination_date': emp.termination_date
        }
        for emp in old_employees
    ]
    return JsonResponse({'old_employees': old_employees_data})

    
def generate_payroll_view(request):
    month = int(request.GET.get('month', timezone.now().month))
    year = int(request.GET.get('year', timezone.now().year))
    
    employees = Employee.objects.all()
    payrolls_data = []

    for employee in employees:
        if employee.employment_status != 'active':
            continue
        total_deductions = Decimal('0.00')

        
        absences = Attendance.objects.filter(
            employee=employee,
            attendance_date__month=month,
            attendance_date__year=year,
            status='absent'
        )
        for absence in absences:
            leave_exists = LeaveApplication.objects.filter(
                employee=employee,
                status='approved',
                leave_type__is_paid=True,
                start_date__lte=absence.attendance_date,
                end_date__gte=absence.attendance_date
            ).exists()

            if leave_exists:
                continue
            total_deductions += employee.basic_salary / 30

        
        insurances = EmployeeInsurance.objects.filter(
            employee=employee,
            end_date__gte=date(year, month, 1),
        )
        for insurance in insurances:
            total_deductions += insurance.monthly_deduction

        
        today = date.today()
        tenure_years = max(0, today.year - employee.joining_date.year - ((today.month, today.day) < (employee.joining_date.month, employee.joining_date.day)))
        bonus_percentage = min(tenure_years, 10)  # optional cap
        bonus = (employee.basic_salary * Decimal(bonus_percentage) / Decimal(100))
        attendances = Attendance.objects.filter(
            employee=employee,
            attendance_date__month=month,
            attendance_date__year=year,
            status='present'
        )

        for attendance in attendances:
            if attendance.check_in_time and attendance.check_out_time:
                work_duration = datetime.combine(today, attendance.check_out_time) - datetime.combine(today, attendance.check_in_time)
                if work_duration > timedelta(hours=8):
                        bonus += employee.basic_salary * Decimal('0.5') / Decimal(100)
                    
        payroll, created = Payroll.objects.get_or_create(
            employee=employee,
            month=month,
            year=year,
            defaults={
                'basic_salary': employee.basic_salary,
                'bonuses': bonus,
                'bonus_reason': f'{bonus_percentage}% tenure bonus and overtime',
                'deductions': total_deductions,
                'deduction_reason': 'Absences/Leaves/Insurance',
                'net_salary': employee.basic_salary + bonus - total_deductions,
                'status': 'pending'  
            }
        )

        if created:
            payroll.net_salary = payroll.basic_salary + payroll.bonuses - payroll.deductions
            payroll.save()

        payrolls_data.append({
            'employee_id': employee.id,
            'employee_name': employee.full_name,
            'month': month,
            'year': year,
            'basic_salary': str(payroll.basic_salary),
            'bonuses': str(payroll.bonuses),
            'bonus_reason': payroll.bonus_reason,
            'deductions': str(payroll.deductions),
            'deduction_reason': payroll.deduction_reason,
            'net_salary': str(payroll.net_salary),
            'status': payroll.status
        })

    return JsonResponse({'status': 'success', 'payrolls': payrolls_data})
    
def payroll_history_view(request):
    payrolls = Payroll.objects.all()
    payroll_data = [
        {
            "employee" : p.employee.full_name,
            "net salary" : p.net_salary,
            "month" : p.month,
            "year": p.year,
            "status": p.status
        }
        for p in payrolls
    ]
    return JsonResponse ({"Payrolls" : payroll_data})


# @api_view(['POST'])
# @permission_classes([AllowAny])
# def add_department_view(request):
#     data = json.loads(request.body)
#     department_name = data.get('department_name')
#     if not department_name:
#         return JsonResponse({'message': 'No department name provided.'}, status=400)
#     deps = Department.objects.filter(department_name=department_name)
#     if deps.exists():
#         return JsonResponse({'message': 'Department already exists.'}, status=400)
#     add_department(department_name)
#     return JsonResponse({'message': 'Department added successfully.'})


# @api_view(['DELETE'])
# @permission_classes([AllowAny])
# def delete_department_view(request):
#     data = json.loads(request.body)
#     department_name = data.get('department_name')
#     if not department_name:
#         return JsonResponse({'message': 'No department name provided.'}, status=400)
#     deps = Department.objects.filter(department_name=department_name)
#     if not deps.exists():
#         return JsonResponse({'message': 'Department not found.'}, status=404)
#     delete_department(department_name)
#     return JsonResponse({'message': 'Department deleted successfully.'})

# @api_view(['DELETE'])
# @permission_classes([AllowAny])
# @hr_required
# def delete_designation_view(request):
#     data = json.loads(request.body)
#     designation_name = data.get('designation_name')
#     if not designation_name:    
#         return JsonResponse({'message': 'No designation name provided.'}, status=400)
#     desigs = Designation.objects.filter(designation_name=designation_name)
#     if not desigs.exists():
#         return JsonResponse({'message': 'Designation not found.'}, status=404)
#     delete_designation(designation_name)
#     return JsonResponse({'message': 'Designation deleted successfully.'})


@csrf_exempt
@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def generate_report_view(request):
    report_type = request.GET.get("report_type")   # "employee" or "company"
    month = int(request.GET.get("month"))
    year = int(request.GET.get("year"))

    if report_type == "employee":
        return generate_employee_reports(month, year)

    elif report_type == "company":
        return generate_company_report(month, year)

    return JsonResponse({"error": "Invalid report_type"}, status=400)

@csrf_exempt
@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def generate_employee_reports(month, year):

    employees = Employee.objects.all()
    results = []

    base_folder = os.path.join(settings.MEDIA_ROOT, "employee_reports")
    os.makedirs(base_folder, exist_ok=True)

    for emp in employees:

        
        exists = MonthlyEmployeeReport.objects.filter(
            employee=emp,
            month=month,
            year=year
        ).first()

        if exists:
            results.append({
                "employee_id": emp.id,
                "file_path": exists.file_path,
                "status": "already_exists"
            })
            continue

        
        attendance = Attendance.objects.filter(
            employee=emp,
            attendance_date__month=month,
            attendance_date__year=year
        )
        present_days = attendance.filter(status="present").count()
        absent_days = attendance.filter(status="absent").count()

        
        leaves = LeaveApplication.objects.filter(
            employee=emp,
            status="approved",
            start_date__month=month,
            start_date__year=year
        ).count()

        
        insurance_exp = EmployeeInsurance.objects.filter(
            employee=emp,
            end_date__month=month,
            end_date__year=year
        ).count()

        
        total_comp = Complaint.objects.filter(employee=emp).count()
        resolved_comp = Complaint.objects.filter(employee=emp, status="resolved").count()
        unresolved_comp = total_comp - resolved_comp

        
        content = f"""
Employee Monthly Report
=======================

Employee Name: {emp.full_name}
Employee ID: {emp.id}
Month: {month}-{year}

Attendance
----------
Present: {present_days}
Absent: {absent_days}

Leaves Approved: {leaves}

Insurance Expiring This Month: {insurance_exp}

Complaints:
  Total: {total_comp}
  Resolved: {resolved_comp}
  Unresolved: {unresolved_comp}
"""

        
        file_name = f"employee_{emp.id}_{month}_{year}.txt"
        file_path = os.path.join(base_folder, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        db_path = f"employee_reports/{file_name}"

        
        MonthlyEmployeeReport.objects.create(
            employee=emp,
            month=month,
            year=year,
            report_file=db_path
        )

        results.append({
            "employee_id": emp.id,
            "file_path": db_path,
            "status": "created"
        })

    return JsonResponse({"status": "success", "employee_reports": results})

@csrf_exempt
@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def generate_company_report(month, year):

    exists = MonthlyCompanyReport.objects.filter(
        month=month,
        year=year
    ).first()

    if exists:
        return JsonResponse({
            "status": "already_exists",
            "file_path": exists.file_path
        })

    #
    total_employees = Employee.objects.filter(employment_status='active').count()

    presents = Attendance.objects.filter(
        attendance_date__month=month,
        attendance_date__year=year,
        status="present"
    ).count()

    absents = Attendance.objects.filter(
        attendance_date__month=month,
        attendance_date__year=year,
        status="absent"
    ).count()

    leaves = LeaveApplication.objects.filter(
        status="approved",
        start_date__month=month,
        start_date__year=year
    ).count()

    insurance_expiring = EmployeeInsurance.objects.filter(
        end_date__month=month,
        end_date__year=year
    ).count()

    total_complaints = Complaint.objects.count()
    resolved = Complaint.objects.filter(status="resolved").count()
    unresolved = total_complaints - resolved

   
    content = f"""
Company Monthly Report
======================

Month: {month}-{year}

Total Employees: {total_employees}

Attendance Summary:
  Present: {presents}
  Absent: {absents}

Approved Leaves: {leaves}

Insurance Expiring This Month: {insurance_expiring}

Complaints:
  Total: {total_complaints}
  Resolved: {resolved}
  Unresolved: {unresolved}
"""

    
    folder = os.path.join(settings.MEDIA_ROOT, "company_reports")
    os.makedirs(folder, exist_ok=True)

    file_name = f"company_report_{month}_{year}.txt"
    file_path = os.path.join(folder, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    db_path = f"company_reports/{file_name}"

    
    MonthlyCompanyReport.objects.create(
        month=month,
        year=year,
        file_path=db_path
    )

    return JsonResponse({
        "status": "created",
        "file_path": db_path
    })


@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def leave_list_view(request):
    leaves = LeaveType.objects.all()
    leave_data = [
        {
            'id': leave.id,
            'leave_type_name': leave.leave_type_name,
            'description': leave.policy_description,
            'max_days_allowed': leave.max_days_per_year,
        }
        for leave in leaves
    ]
    return JsonResponse({'leave_types': leave_data})


@hr_required
@api_view(['POST'])
@permission_classes([AllowAny])
def add_leave_view(request):
    data = json.loads(request.body)
    leave_type_name = data.get('leave_type_name')
    description = data.get('description')
    max_days_per_year = data.get('max_days_allowed')
    if not leave_type_name:
        return JsonResponse({'message': 'No leave type name provided.'}, status=400)
    leaves = LeaveType.objects.filter(leave_type_name=leave_type_name)
    if leaves.exists():
        return JsonResponse({'message': 'Leave type already exists.'}, status=400)
    LeaveType.objects.create(
        leave_type_name=leave_type_name,
        description=description,
        max_days_per_year=max_days_per_year
    )
    return JsonResponse({'message': 'Leave type added successfully.'})

@hr_required
@api_view(['PUT', 'GET'])
@permission_classes([AllowAny])
def update_leave_status(request, leave_type_name):
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if not to_update or not new_val:
        return JsonResponse({'message': 'All Parameters are not provided'}, status=400)
    if to_update == 'description':
        LeaveType.objects.filter(leave_type_name=leave_type_name).update(description=new_val)
        return JsonResponse ({'message': 'Leave type description updated successfully.'})
    elif to_update == 'max_days_allowed':
        le = LeaveType.objects.get(leave_type_name=leave_type_name)
        le.max_days_per_year=new_val
        le.save()
        return JsonResponse ({'message': 'Leave type max days allowed updated successfully.'})
    return JsonResponse ({'message': "updating a non-existing field"}, status=400)

@hr_required
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_leave(request, leave_type_name):
    LeaveType.objects.filter(leave_type_name=leave_type_name).delete()
    return JsonResponse ({'message': "Deleted Successfully"}, status=200)

@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def insured_employees_view(request):
    insurances = InsurancePlan.objects.all().prefetch_related(
        'employee_insurances__employee'
    )

    result = []

    for insurance in insurances:
        employees_list = [
            {
                "employee_id": ei.employee.id,
                "employee_name": ei.employee.full_name,
                "insurance_id": ei.insurance_plan.id,
                "insurance_name": ei.insurance_plan.plan_name,
                "status": ei.status,
                "start_date": ei.start_date,
                "end_date": ei.end_date,
                "monthly_deduction": ei.monthly_deduction,
            }
            for ei in insurance.employee_insurances.all()
        ]

        result.append({
            "insurance_name": insurance.plan_name,
            "employees": employees_list
        })
    return JsonResponse({"insurances": result}, safe=False)

@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def view_attendance_view(request):
    attendances = Attendance.objects.select_related('employee').all()

    result = [
        {
            "employee_id": att.employee.id,
            "employee_name": att.employee.full_name,
            "date": att.attendance_date,
            "check_in_time": att.check_in_time,
            "check_out_time": att.check_out_time,
            "status": att.status,
        }
        for att in attendances
    ]

    return JsonResponse({"attendances": result}, safe=False)

@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def insurance_view(request):
    insurances = InsurancePlan.objects.all()
    data = [
        {
            'id': insurance.id,
            'plan_name': insurance.plan_name,
            'coverage': str(insurance.coverage_amount),  # include any other fields you want
            'premium': str(insurance.premium_amount),  # convert Decimal to string for JSON
            'policy terms' : insurance.policy_terms
        }
        for insurance in insurances
    ]
    return JsonResponse({'insurances': data})


@hr_required
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def add_insurance_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            plan_name = data.get("plan_name")
            coverage = data.get("coverage")
            premium = data.get("premium")
            policy_term = data.get("policy_terms")  # new field

            if not plan_name or not coverage or premium is None or policy_term is None:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            insurance = InsurancePlan.objects.create(
                plan_name=plan_name,
                coverage_amount=coverage,
                premium_amount=premium,
                policy_terms=policy_term
            )

            return JsonResponse({
                "message": "Insurance added successfully",
                "insurance": {
                    "id": insurance.id,
                    "plan_name": insurance.plan_name,
                    "coverage": str(insurance.coverage_amount),
                    "premium": str(insurance.premium_amount),
                    "policy_term": insurance.policy_terms
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@hr_required
@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_insurance(request, insurance_id):
    try:
        insurance = InsurancePlan.objects.get(id=insurance_id)
        insurance.delete()
        return JsonResponse({"message": "Insurance deleted successfully"})
    except InsurancePlan.DoesNotExist:
            return JsonResponse({"error": "Insurance not found"}, status=404)
@hr_required
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_insurance(request, insurance_id):
    try:
        insurance = InsurancePlan.objects.get(id=insurance_id)
    except InsurancePlan.DoesNotExist:
        return JsonResponse({'message': 'Insurance plan not found.'}, status=404)

    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')

    if not to_update or new_val is None:
        return JsonResponse({'message': 'No data provided for update.'}, status=400)

    if to_update == 'plan_name':
        if InsurancePlan.objects.filter(plan_name=new_val).exclude(id=insurance_id).exists():
            return JsonResponse({'message': 'Insurance plan name already exists.'}, status=400)
        insurance.plan_name = new_val
        insurance.save()
        return JsonResponse({'message': 'Insurance plan name updated successfully.'})

    elif to_update == 'coverage_amount':
        try:
            insurance.coverage_amount = Decimal(new_val)
            insurance.save()
            return JsonResponse({'message': 'Insurance coverage amount updated successfully.'})
        except (ValueError, TypeError):
            return JsonResponse({'message': 'Invalid coverage amount.'}, status=400)

    elif to_update == 'premium_amount':
        try:
            insurance.premium_amount = Decimal(new_val)
            insurance.save()
            return JsonResponse({'message': 'Insurance premium amount updated successfully.'})
        except (ValueError, TypeError):
            return JsonResponse({'message': 'Invalid premium amount.'}, status=400)

    elif to_update == 'policy_terms':
        insurance.policy_terms = new_val
        insurance.save()
        return JsonResponse({'message': 'Insurance policy terms updated successfully.'})

    else:
        return JsonResponse({'message': 'Invalid field to update.'}, status=400)


@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def employee_leave(request):
    leave_applications = LeaveApplication.objects.select_related('employee', 'leave_type').all()

    result = [
        {
            'id': la.id,
            'employee_id': la.employee.id,
            'full_name': la.employee.full_name,           
            'leave_id': la.leave_type.id,
            'leave_type_name': la.leave_type.leave_type_name,
            'start_date': la.start_date,
            'end_date': la.end_date,
            'total_days': la.total_days,
            'status': la.status,
            'applied_date': la.applied_date,
        }
        for la in leave_applications
    ]

    return JsonResponse({'leave_applications': result}, safe=False)

@hr_required
@api_view(['PUT', 'GET'])
@permission_classes([AllowAny])
def edit_insurances_view(request, employee_id):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    insurance_id = data.get("insurance_id")
    new_status = data.get("status")
    extend_end_date = data.get("extend_end_date")  # YYYY-MM-DD
    deduction = data.get('new_deduction')
    try:
        employee = Employee.objects.get(id=employee_id, employment_status="active")
    except Employee.DoesNotExist:
        return JsonResponse({"message": "Invalid Employee"}, status=404)

    if not insurance_id:
        return JsonResponse({"message": "insurance_id is required"}, status=400)

    try:
        emp_ins = EmployeeInsurance.objects.get(employee=employee, insurance_plan_id=insurance_id)
    except EmployeeInsurance.DoesNotExist:
        return JsonResponse({"message": "Insurance record not found for this employee"}, status=404)
    try:
        if new_status:
            if new_status not in ["active", "inactive"]:
                return JsonResponse({"message": "Status must be 'active' or 'inactive'"}, status=400)
            emp_ins.status = new_status

        if extend_end_date:
            try:
                new_end_date = datetime.strptime(extend_end_date, "%Y-%m-%d").date()
            except:
                return JsonResponse({"message": "Invalid date format. Use YYYY-MM-DD"}, status=400)

            if new_end_date < emp_ins.end_date:
                return JsonResponse({"message": "New end date cannot be earlier than existing end date"}, status=400)
            emp_ins.end_date = new_end_date

        if deduction and Decimal(deduction) > Decimal('0.00'):
            emp_ins.monthly_deduction = Decimal(deduction)

        emp_ins.save()
        return JsonResponse({
        "message": "Insurance updated successfully",
        "insurance_record": {
            "id": emp_ins.id,
            "employee": employee.full_name,
            "insurance_plan": emp_ins.insurance_plan.plan_name,
            "status": emp_ins.status,
            "start_date": emp_ins.start_date,
            "end_date": emp_ins.end_date,
        }
    }, status=200)
    except:
        return JsonResponse ({}, status=501)

    

    
    
@api_view(['POST'])
@hr_required
@permission_classes([AllowAny])
def mark_attendance(request, employee_id):

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    att_date_str = data.get('attendance_date')
    check_in_time = data.get('check_in_time')
    check_out_time = data.get('check_out_time')
    status = data.get('status')

    if not att_date_str:
        return JsonResponse({'message': "Attendance date is required"}, status=400)
    try:
        att_date = datetime.strptime(att_date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'message': "Invalid date format, use YYYY-MM-DD"}, status=400)

    if att_date > date.today():
        return JsonResponse({'message': "Attendance date cannot be in the future"}, status=400)
    
    if status == 'present' and (not check_in_time or not check_out_time):
        return JsonResponse({'message': "Check-in and Check-out time required for present status"}, status=400)
    try:
        check_in_time = datetime.strptime(check_in_time, "%H:%M:%S").time()
        check_out_time = datetime.strptime(check_out_time, "%H:%M:%S").time()
    except:
        return JsonResponse({'message': "Invalid time format, use HH:MM:SS"}, status=400)
    
    try:
        emp = Employee.objects.get(id=employee_id, employment_status = 'active')
    except Employee.DoesNotExist:
        return JsonResponse({'message': "Employee not found"}, status=404)

    
    existing_attendance = Attendance.objects.filter(employee=emp, attendance_date=att_date).first()
    if existing_attendance:
        return JsonResponse({'message': "Attendance already marked for this date"}, status=409)

    
    att = Attendance.objects.create(
        employee=emp,
        attendance_date=att_date,
        check_in_time=check_in_time if status == "present" else None,
        check_out_time=check_out_time if status == "present" else None,
        status=status
    )

    return JsonResponse({
        "message": "Attendance marked successfully",
        "attendance": {
            "id": att.id,
            "employee_id": emp.id,
            "employee_name": emp.full_name,
            "date": att.attendance_date,
            "check_in": att.check_in_time,
            "check_out": att.check_out_time,
            "status": att.status
        }
    }, status=201)


@api_view(['PUT', 'GET'])
@hr_required
@permission_classes([AllowAny])
def edit_leaves_view(request, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({"message": "Invalid Employee"}, status=404)

    data = json.loads(request.body)

    leave_id = data.get("leave_application_id")
    new_status = data.get("status")

    if not leave_id:
        return JsonResponse({"message": "leave_id is required"}, status=400)

    try:
        leave_record = LeaveApplication.objects.get(id=leave_id, employee=employee)
    except LeaveApplication.DoesNotExist:
        return JsonResponse({"message": "Leave record not found"}, status=404)

    today = date.today()
    if leave_record.start_date <= today:
        return JsonResponse({
            "message": "Cannot modify leave after or on start date"
        }, status=400)

    if new_status:
        if new_status not in ["approved", "rejected"]:
            return JsonResponse({"message": "Invalid status"}, status=400)
        if new_status == "approved":
            approved_days = LeaveApplication.objects.filter(
                employee=employee,
                leave_type=leave_record.leave_type,
                status="approved",
                start_date__year=date.today().year
            ).aggregate(total_days=Sum('total_days'))['total_days'] or 0
            if approved_days + leave_record.total_days > leave_record.leave_type.max_days_per_year:
                leave_record.status = "rejected"
                leave_record.save()
                return JsonResponse({
                    "message": f"Leave exceeds allowed {leave_record.leave_type.max_days_per_year} days per year. Leave automatically rejected."
                }, status=200)

        leave_record.status = new_status
        leave_record.save()
    return JsonResponse({
        "message": "Leave updated successfully",
        "leave": {
            "id": leave_record.id,
            "employee": employee.full_name,
            "start_date": leave_record.start_date,
            "end_date": leave_record.end_date,
            "status": leave_record.status,
            "is_paid": leave_record.leave_type.is_paid
        }
    }, status=200)

@api_view(['POST'])
@hr_required
@permission_classes([AllowAny])
def apply_insurences(request, employee_id):
    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"message": "Invalid JSON"}, status=400)

    insurance_name = data.get("insurance_name")

    if not insurance_name:
        return JsonResponse({"message": "insurance_name is required"}, status=400)

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({"message": "Invalid employee"}, status=404)

    try:
        insurance = InsurancePlan.objects.get(plan_name__iexact=insurance_name)
    except InsurancePlan.DoesNotExist:
        return JsonResponse({"message": "Insurance not found"}, status=404)

    active_count = EmployeeInsurance.objects.filter(employee=employee, status="active").count()
    if active_count >= 3:
        return JsonResponse({"message": "Employee already has maximum of 3 active insurances"}, status=400)

    exists = EmployeeInsurance.objects.filter(employee=employee, insurance_plan=insurance, status="active").exists()
    if exists:
        return JsonResponse({"message": "This insurance is already active for the employee"}, status=409)
    
    deduction = employee.basic_salary * Decimal("0.001")

    today = date.today()
    end_date = today + timedelta(days=365)

    emp_ins = EmployeeInsurance.objects.create(
        employee=employee,
        insurance_plan=insurance,
        status="active",
        start_date=today,
        end_date=end_date,
        monthly_deduction=deduction
    )

    return JsonResponse({
        "message": "Insurance applied successfully",
        "insurance_record": {
            "id": emp_ins.id,
            "employee": employee.full_name,
            "insurance": insurance.plan_name,
            "status": emp_ins.status,
            "deduction": str(emp_ins.deduction),
            "start_date": emp_ins.start_date,
            "end_date": emp_ins.end_date
        }
    }, status=201)

@api_view(['POST'])
@hr_required
@permission_classes([AllowAny])
def apply_leaves(request, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id, employment_status='active')
    except Employee.DoesNotExist:
        return JsonResponse({"message": "Invalid Employee"}, status=404)

    data = json.loads(request.body)

    start_date = data.get("start_date")       # YYYY-MM-DD
    end_date = data.get("end_date")           # YYYY-MM-DD
    leave_type = data.get("leave_type")       # sick, casual, annual, etc.
    is_paid = data.get("is_paid", False)

    
    if not start_date or not end_date or not leave_type:
        return JsonResponse({"message": "start_date, end_date, and leave_type are required"}, status=400)

    
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        e_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"message": "Invalid date format. Use YYYY-MM-DD"}, status=400)

    today = date.today()

    
    if s_date > e_date:
        return JsonResponse({"message": "start_date cannot be after end_date"}, status=400)

    
    if s_date < today:
        return JsonResponse({"message": "Cannot apply for leave in the past"}, status=400)

    overlapping = LeaveApplication.objects.filter(
        employee=employee,
        start_date__lte=e_date,
        end_date__gte=s_date,
        status__in=["pending", "approved"]
    ).exists()

    if overlapping:
        return JsonResponse({"message": "This leave overlaps with an existing request"}, status=409)
    
    le = LeaveType.objects.filter(leave_type_name__iexact=leave_type)
    if not le.exists():
        return JsonResponse ({'message': 'Leave Type not found'})
    
    leave = LeaveApplication.objects.create(
        employee=employee,
        leave_type=le.first(),
        start_date=s_date,
        end_date=e_date,
        total_days=(e_date - s_date).days + 1,
        status="pending"
    )

    return JsonResponse({
        "message": "Leave request submitted successfully",
        "leave": {
            "id": leave.id,
            "employee": employee.full_name,
            "leave_type": leave.leave_type.leave_type_name,
            "start_date": str(leave.start_date),
            "end_date": str(leave.end_date),
            "status": leave.status,
            "is_paid": leave.leave_type.is_paid
        }
    }, status=201)

@api_view(['GET'])
@permission_classes([AllowAny])
def all_complaints_view(request):
    complaints = Complaint.objects.all().select_related("employee")

    result = []

    for c in complaints:
        result.append({
            "id": c.id,
            "employee_id": c.employee.id,
            "employee_name": c.employee.full_name,
            "title": c.subject,
            "description": c.description,
            "status": c.status,
            "created_at": c.filed_date
        })

    return JsonResponse ({"complaints": result}, status=200)


@api_view(['POST'])
@permission_classes([AllowAny])
def add_complaint_view(request):
    data = json.loads(request.body)

    email = data.get("email")
    title = data.get("title")
    description = data.get("description")

    
    if not email or not title or not description:
        return JsonResponse({"message": "employee_id, title and description are required"}, status=400)

    
    try:
        employee = Employee.objects.get(email=email, employment_status='active')
    except Employee.DoesNotExist:
        return JsonResponse({"message": "Invalid employee"}, status=404)

    
    complaint = Complaint.objects.create(
        employee=employee,
        subject=title,
        description=description,
        status="open"   
    )

    return JsonResponse({
        "message": "Complaint submitted successfully",
        "complaint": {
            "id": complaint.id,
            "employee_id": employee.id,
            "employee_name": employee.full_name,
            "title": complaint.subject,
            "description": complaint.description,
            "status": complaint.status,
            "created_at": complaint.filed_date
        }
    }, status=201)

    
@api_view(['DELETE'])
@hr_required
@permission_classes([AllowAny])
def delete_complain(request, complain_id):
    try:
        complain = Complaint.objects.get(id=complain_id)
    except Complaint.DoesNotExist:
        return JsonResponse({'message': 'Complaint not found'}, status=404)

    complain.delete()
    return JsonResponse({'message': 'Complaint deleted successfully'}, status=200)

@api_view(['PUT', 'GET'])
@hr_required
@permission_classes([AllowAny])
def update_complain(request, complain_id):
    
    allowed_statuses = ['resolved', 'closed']

    try:
        complain = Complaint.objects.get(id=complain_id)
    except Complaint.DoesNotExist:
        return JsonResponse({'message': 'Complaint not found'}, status=404)

    data = json.loads(request.body)
    new_status = data.get('status')

    if not new_status:
        return JsonResponse({'message': 'Status is required'}, status=400)

    if new_status not in allowed_statuses:
        return JsonResponse({
            'message': f"Invalid status. Allowed values: {allowed_statuses}"
        }, status=400)


    complain.status = new_status
    if new_status == 'resolved':
        complain.resolved_date = date.today()
    complain.save()

    return JsonResponse({
        'message': 'Complaint status updated successfully',
        'complaint_id': complain_id,
        'new_status': new_status
    }, status=200)

@api_view(['POST'])
@csrf_exempt
@hr_required
@permission_classes([AllowAny])
def add_interviewed(request):
    try:
        data = json.loads(request.body)

        full_name = data.get("full_name")
        email = data.get("email")
        phone = data.get("phone")
        department_id = data.get("department_id")
        position_id = data.get("position_id")
        # interviewer_id = data.get("interviewer_id")
        remarks = data.get("remarks", "")

        if not full_name or not email:
            return JsonResponse({"message": "Full name and email are required"}, status=400)
        
        department = None
        if department_id:
            department = Department.objects.filter(id=department_id).first()
            if not department:
                return JsonResponse({"message": "Invalid department"}, status=400)

        
        position = None
        if position_id:
            position = Designation.objects.filter(id=position_id).first()
            if not position:
                return JsonResponse({"message": "Invalid applied position"}, status=400)

        
        interviewer = None
        interviewers = Employee.objects.filter(
            department__id=department_id, 
            employment_status='active')
        if interviewers.exists():
            interviewer = random.choice(list(interviewers))
        else:
            interviewers = Employee.objects.filter(
            department__department_name='HR', 
            employment_status='active')
            if interviewers.exists():
                interviewer = random.choice(list(interviewers))
        

        today = timezone.now().date()

        candidate = InterviewedCandidate.objects.create(
            full_name=full_name,
            email=email,
            phone=phone,
            department=department,
            applied_position=position,
            interviewer=interviewer,
            interview_date=today,
            remarks=remarks,
        )

        return JsonResponse({
            "message": "Interviewed candidate created successfully",
            "candidate_id": candidate.id
        }, status=201)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)
    
@api_view(['PUT', 'GET'])
@hr_required
@permission_classes([AllowAny])
def shortlist_or_reject(request):
    data = json.loads(request.body)
    c_id = data.get('candidate_id')
    new = data.get('status')
    if c_id and new:
        try:
            can = InterviewedCandidate.objects.filter(id=c_id).first()
        except Exception as e:
            return JsonResponse ({'message': f"{e}"}, status=404)
        if can.status == 'pending' and new in ["shortlisted", "rejected"]:
            can.status = new
            can.save()
            return JsonResponse({'message': f"candidate updated with new status: {new}"}, status=200)
        return JsonResponse ({'message': f"candidate is already {can.status}"}, status=404)
    return JsonResponse ({'message': "Parameters not found"}, status=404)

@api_view(['GET'])
@hr_required
@permission_classes([AllowAny])
def allowed_roles(request):
    d_id = request.GET.get('department_id')
    if d_id:
        try:
            dep = Department.objects.filter(id=d_id).first()
        except Exception as e:
            return JsonResponse ({'message': f"{e}"}, status=404)
        return JsonResponse ({'designations': list(allowed_positions_for_departments[dep.department_name])}, status=200)
    return JsonResponse (
        {
            'message': "department id is needed"
        }, status=400
    )