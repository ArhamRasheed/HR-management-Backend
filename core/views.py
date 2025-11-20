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

allowed_positions_for_departments = {
    'IT': ['Software Engineer', 'CTO', 'System Administrator', 'CEO', 'Manager'],
    'HR': ['Manager', 'Recruiter', 'CEO'],
    'Finance': ['Accountant', 'Financial Analyst', 'CEO'],
    'Sales': ['Sales Executive', 'Manager', 'CEO'],
    'Marketing': ['Marketing Executive', 'Manager', 'CEO'],
}

def add_employee(full_name, email, phone, applied_position, department, password):
    if department.department_name == 'HR' and not password:
        return False
    if applied_position.designation_name == 'CEO':
        ceos = Employee.objects.filter(designation__designation_name='CEO', employment_status='active')
        if ceos.exists():
            return False
    if applied_position.designation_name == 'CTO' and (not department == 'IT' or Employee.objects.filter(designation__designation_name='CTO').exists()):
        return False
    if applied_position not in allowed_positions_for_departments.get(department.department_name, []):
        return False
    Employee.objects.create(
        full_name=full_name, 
        email=email, 
        phone=phone, 
        password=make_password(password),
        department=department, 
        employment_status="active",
        designation=applied_position)
    return True

@api_view(['DELETE'])
@permission_classes([AllowAny])
@hr_required
def delete_employee(employee_id):
    Employee.objects.filter(id=employee_id).delete()
    return JsonResponse({'message': 'Employee deleted successfully.'})


@api_view(['PUT'])
@permission_classes([AllowAny])
@hr_required
def update_employee(request, employee_id): #update
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if not to_update or not new_val:
        return JsonResponse({'message': 'No data provided for update.'}, status=400)
    if to_update == 'full_name':
        Employee.objects.filter(id=employee_id).update(full_name=new_val)
        return JsonResponse({'message': 'Employee name updated successfully.'})
    elif to_update == 'email':
        Employee.objects.filter(id=employee_id).update(email=new_val)
        return JsonResponse({'message': 'Employee email updated successfully.'})
    elif to_update == 'phone':
        Employee.objects.filter(id=employee_id).update(phone=new_val)
        return JsonResponse({'message': 'Employee phone updated successfully.'})
    elif to_update == 'department_name':
        if new_val not in Department.objects.values_list('department_name', flat=True):
            return JsonResponse({'message': 'Department does not exist.'}, status=400)
        Employee.objects.filter(id=employee_id).update(department_id=Department.objects.get(department_name=new_val).id)
        return JsonResponse({'message': 'Employee department updated successfully.'})
    elif to_update == 'designation_name':
        if new_val == 'CEO':
            ceos = Employee.objects.filter(designation__designation_name='CEO', employment_status='active')
            if ceos.exists():
                return JsonResponse({'message': 'CEO already exists.'}, status=400)
        elif new_val == 'CTO' and not Employee.objects.filter(employee_id=employee_id).department.department_name == 'IT':
            return JsonResponse({'message': 'Only IT department can have CTO designation.'}, status=400)
        elif new_val == 'CTO' and Employee.objects.filter(designation__designation_name='CTO').exists():
            return JsonResponse({'message': 'CTO already exists.'}, status=400)
        if new_val not in Designation.objects.values_list('designation_name', flat=True):
            return JsonResponse({'message': 'Designation does not exist.'}, status=400)
        Employee.objects.filter(id=employee_id).update(designation_id=Designation.objects.get(designation_name=new_val).id)
        return JsonResponse({'message': 'Employee designation updated successfully.'})

@api_view(['PUT'])
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

@api_view(['DELETE'])
@permission_classes([AllowAny])
@hr_required
def delete_department(request, department_name):
    Department.objects.filter(department_name=department_name).delete()
    return JsonResponse({'message': 'Department deleted successfully.'})

@api_view(['PUT'])
@permission_classes([AllowAny])
@hr_required
def update_department(request, department_name): #update
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if to_update == 'department_name':
        if Department.objects.filter(department_name=new_val).exists():
            return JsonResponse({'message': 'Department already exists.'}, status=400)
        Department.objects.filter(department_name=department_name).update(department_name=new_val)
        return JsonResponse ({'message': 'Department name updated successfully.'})

@api_view(['POST'])
@permission_classes([AllowAny])
@hr_required
def add_designation(request):
    data = json.loads(request.body)
    designation_name = data.get('designation_name')
    if not designation_name:
        return JsonResponse({'message': 'No designation name provided.'}, status=400)
    if Designation.objects.filter(designation_name=designation_name).exists():
        return JsonResponse({'message': 'Designation already exists.'}, status=400)
    Designation.objects.create(designation_name=designation_name)
    return JsonResponse({'message': 'Designation added successfully.'})


@api_view(['DELETE'])
@permission_classes([AllowAny])
@hr_required
def delete_designation(request,designation_name):
    Designation.objects.filter(designation_name=designation_name).delete()
    return JsonResponse({'message': 'Designation deleted successfully.'})


@api_view(['PUT'])
@permission_classes([AllowAny])
@hr_required
def update_designation(request, designation_name): #update
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if to_update == 'designation_name':
        if Designation.objects.filter(designation_name=new_val).exists():
            return JsonResponse({'message': 'Designation already exists.'}, status=400)
        Designation.objects.filter(designation_name=designation_name).update(designation_name=new_val)
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
def dashboard_view(request):
    employee_id = request.session.get('employee_id')
    if not employee_id:
        return JsonResponse({'message': 'Employee not found in session'}, status=404)
    employee = Employee.objects.filter(id=employee_id).first()
    if not employee:
        return JsonResponse({
            'message': 'Employee not found.'
        }, status=404)
    insurances = EmployeeInsurance.objects.filter(employee=employee)
    leaves = LeaveApplication.objects.filter(employee=employee)
    attendances = Attendance.objects.filter(employee=employee)
    complaints = Complaint.objects.filter(employee=employee)
    insurances_data = [
        {
            'plan_name': insurance.insurance_plan.plan_name,
            'coverage_amount': insurance.insurance_plan.coverage_amount,
            'premium': insurance.insurance_plan.premium_amount,
            'start_date': insurance.start_date,
            'end_date': insurance.end_date,
            'status': insurance.status,
            'monthly_deduction': insurance.monthly_deduction,
        }
        for insurance in insurances
    ]
    leaves_data = [
        {
            'leave_type': leave.leave_type.leave_type_name,
            'start_date': leave.start_date,
            'end_date': leave.end_date,
            'total_days': leave.total_days,
            'status': leave.status,
            'applied_on': leave.applied_date
        }
        for leave in leaves
    ]
    attendance_data = [
        {
            'check_in': attendance.check_in_time,
            'check_out': attendance.check_out_time,
            'attendance_date': attendance.attendance_date,
            'status': attendance.status
        }
        for attendance in attendances
    ]
    complaints_data = [
        {       
            'subject': complaint.subject,
            'description': complaint.description,
            'status': complaint.status,
            'filed_on': complaint.filed_date
        }
        for complaint in complaints
    ]
    return JsonResponse({
        'full_name': employee.full_name,    
        'department': employee.department.department_name if employee.department else None,
        'designation': employee.designation.designation_name if employee.designation else None,
        'date_of_joining': employee.joining_date,
        'leaves': leaves_data,
        'insurances': insurances_data,
        'attendances': attendance_data,
        'complaints': complaints_data
    })

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
            'department': emp.department.department_name if emp.department else None,
            'designation': emp.designation.designation_name if emp.designation else None,
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
    data = json.loads(request.body)
    employee_id = data.get('employee_id')
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
    password  = data.get('password')
    if not candidate_id:
        return JsonResponse({'message': 'No candidate ID provided.'}, status=400)
    candidate = InterviewedCandidate.objects.filter(id=candidate_id, status='shortlisted').first()
    if not candidate:
        return JsonResponse({'message': 'Candidate not found or not shortlisted.'}, status=404)
    if(add_employee(candidate.full_name, candidate.email, candidate.phone, candidate.applied_position, candidate.department, password)):
        return JsonResponse({'message': 'Employee hired successfully.'})
    else:
        return JsonResponse({'message': 'Something went wrong.'}, status=404)

@api_view(['GET'])
@permission_classes([AllowAny])
def reports_view(request):
    data = json.loads(request.body)
    doc_type = data.get('doc_type')
    month = data.get('month')
    year = data.get('year')
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
    data = json.loads(request.body)
    department_name = data.get('department_name')
    if not department_name:
        return JsonResponse({'message': 'No department name provided.'}, status=400)
    departemnt = Department.objects.filter(department_name=department_name).first()
    if not departemnt:
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
            for emp in Employee.objects.filter(department=departemnt)   
        ]
    return JsonResponse({
        'department_name': departemnt.department_name,
        'total_employees': Employee.objects.filter(department=departemnt).count(),
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

    
def generate_payroll_view(request, employee_id):
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
            attendance_date__moth=month,
            attendance_date__year=year,
            status='absent'
        )
        for absence in absences:
            total_deductions += employee.basic_salary / 30

        
        leaves = LeaveApplication.objects.filter(
            employee=employee,
            start_date__month=month,
            start_date__year=year,
            approved=True,
            paid=False
        )
        for leave in leaves:
            total_deductions += employee.basic_salary / 30 * leave.days_count()

        
        insurances = EmployeeInsurance.objects.filter(
            employee=employee,
            end_date__gte=date(year, month, 1),
            paid=False
        )
        for insurance in insurances:
            total_deductions += insurance.monthly_deduction

        
        today = date.today()
        tenure_years = max(0, today.year - employee.join_date.year - ((today.month, today.day) < (employee.join_date.month, employee.join_date.day)))
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
    # Implementation of payroll history view
    pass


@api_view(['POST'])
@permission_classes([AllowAny])
def add_department_view(request):
    data = json.loads(request.body)
    department_name = data.get('department_name')
    if not department_name:
        return JsonResponse({'message': 'No department name provided.'}, status=400)
    deps = Department.objects.filter(department_name=department_name)
    if deps.exists():
        return JsonResponse({'message': 'Department already exists.'}, status=400)
    add_department(department_name)
    return JsonResponse({'message': 'Department added successfully.'})

@api_view(['POST'])
@permission_classes([AllowAny])
def add_designation_view(request):
    data = json.loads(request.body)
    designation_name = data.get('designation_name')
    if not designation_name:
        return JsonResponse({'message': 'No designation name provided.'}, status=400)
    desigs = Designation.objects.filter(designation_name=designation_name)
    if desigs.exists():
        return JsonResponse({'message': 'Designation already exists.'}, status=400)
    add_designation(designation_name)
    return JsonResponse({'message': 'Designation added successfully.'})

@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_department_view(request):
    data = json.loads(request.body)
    department_name = data.get('department_name')
    if not department_name:
        return JsonResponse({'message': 'No department name provided.'}, status=400)
    deps = Department.objects.filter(department_name=department_name)
    if not deps.exists():
        return JsonResponse({'message': 'Department not found.'}, status=404)
    delete_department(department_name)
    return JsonResponse({'message': 'Department deleted successfully.'})

@api_view(['DELETE'])
@permission_classes([AllowAny])
@hr_required
def delete_designation_view(request):
    data = json.loads(request.body)
    designation_name = data.get('designation_name')
    if not designation_name:    
        return JsonResponse({'message': 'No designation name provided.'}, status=400)
    desigs = Designation.objects.filter(designation_name=designation_name)
    if not desigs.exists():
        return JsonResponse({'message': 'Designation not found.'}, status=404)
    delete_designation(designation_name)
    return JsonResponse({'message': 'Designation deleted successfully.'})

@api_view(['PUT'])
@permission_classes([AllowAny])
@hr_required
def update_department_view(request):
    data = json.loads(request.body)
    department_name = data.get('department_name')
    if not department_name:
        return JsonResponse({'message': 'No data provided for update.'}, status=400)
    dep = Department.objects.filter(department_name=department_name)
    if not dep.exists():
        return JsonResponse({'message': 'Department not found.'}, status=404)
    update_department(department_name, department_name)
    return JsonResponse({'message': 'Department updated successfully.'})

@api_view(['PUT'])
@permission_classes([AllowAny])
@hr_required
def update_designation_view(request, designation_name):
    data = json.loads(request.body)
    designation_name = data.get('designation_name')
    if not designation_name:
        return JsonResponse({'message': 'No data provided for update.'}, status=400)
    desig = Designation.objects.filter(designation_name=designation_name)
    if not desig.exists():
        return JsonResponse({'message': 'Designation not found.'}, status=404)
    update_designation(designation_name, designation_name)
    return JsonResponse({'message': 'Designation updated successfully.'})





@csrf_exempt
@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
def generate_report_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)

    data = json.loads(request.body)

    report_type = data.get("report_type")   # "employee" or "company"
    month = int(data.get("month"))
    year = int(data.get("year"))

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

        # 1 — check if report already exists
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

        # 2 — get attendance
        attendance = Attendance.objects.filter(
            employee=emp,
            date__month=month,
            date__year=year
        )
        present_days = attendance.filter(status="present").count()
        absent_days = attendance.filter(status="absent").count()

        # 3 — approved leaves in month
        leaves = LeaveApplication.objects.filter(
            employee=emp,
            status="approved",
            start_date__month=month,
            start_date__year=year
        ).count()

        # 4 — insurance expiring this month
        insurance_exp = EmployeeInsurance.objects.filter(
            employee=emp,
            end_date__month=month,
            end_date__year=year
        ).count()

        # 5 — complaints
        total_comp = Complaint.objects.filter(employee=emp).count()
        resolved_comp = Complaint.objects.filter(employee=emp, status="resolved").count()
        unresolved_comp = total_comp - resolved_comp

        # 6 — write file content
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

        # 7 — write file physically
        file_name = f"employee_{emp.id}_{month}_{year}.txt"
        file_path = os.path.join(base_folder, file_name)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        db_path = f"employee_reports/{file_name}"

        # 8 — save to MySQL
        MonthlyEmployeeReport.objects.create(
            employee=emp,
            month=month,
            year=year,
            file_path=db_path
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

    # 2 — aggregated company-wide data
    total_employees = Employee.objects.count()

    presents = Attendance.objects.filter(
        date__month=month,
        date__year=year,
        status="present"
    ).count()

    absents = Attendance.objects.filter(
        date__month=month,
        date__year=year,
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

    # 3 — prepare content
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

    # 4 — write file
    folder = os.path.join(settings.MEDIA_ROOT, "company_reports")
    os.makedirs(folder, exist_ok=True)

    file_name = f"company_report_{month}_{year}.txt"
    file_path = os.path.join(folder, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    db_path = f"company_reports/{file_name}"

    # 5 — save MySQL
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
            'description': leave.description,
            'max_days_allowed': leave.max_days_allowed,
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
@api_view(['PUT'])
@permission_classes([AllowAny])
def update_leave_status(request, leave_type_name):
    data = json.loads(request.body)
    to_update = data.get('to_update')
    new_val = data.get('new_val')
    if not to_update or not new_val:
        return JsonResponse({'message': 'All Parameters are not provided'}, status=400)
    if to_update == 'leave_type_name':
        if LeaveType.objects.filter(leave_type_name=new_val).exists():
            return JsonResponse({'message': 'Leave type already exists.'}, status=400)
        LeaveType.objects.filter(leave_type_name=leave_type_name).update(leave_type_name=new_val)
        return JsonResponse ({'message': 'Leave type name updated successfully.'})
    elif to_update == 'description':
        LeaveType.objects.filter(leave_type_name=leave_type_name).update(description=new_val)
        return JsonResponse ({'message': 'Leave type description updated successfully.'})
    elif to_update == 'max_days_allowed':
        LeaveType.objects.filter(leave_type_name=leave_type_name).update(max_days_allowed=new_val)
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
    # Performance optimized: one JOIN, no N+1
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
            'coverage': insurance.coverage,  # include any other fields you want
            'premium': str(insurance.premium)  # convert Decimal to string for JSON
        }
        for insurance in insurances
    ]
    return JsonResponse({'insurances': data})


@hr_required
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def add_insurance_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            plan_name = data.get("plan_name")
            coverage = data.get("coverage")
            premium = data.get("premium")
            policy_term = data.get("policy_term")  # new field

            if not plan_name or not coverage or premium is None or policy_term is None:
                return JsonResponse({"error": "Missing required fields"}, status=400)

            insurance = InsurancePlan.objects.create(
                plan_name=plan_name,
                coverage=coverage,
                premium=premium,
                policy_term=policy_term
            )

            return JsonResponse({
                "message": "Insurance added successfully",
                "insurance": {
                    "id": insurance.id,
                    "plan_name": insurance.plan_name,
                    "coverage": insurance.coverage,
                    "premium": str(insurance.premium),
                    "policy_term": insurance.policy_term
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
            'employee': {
                'id': la.employee.id,
                'full_name': la.employee.full_name,
                'email': la.employee.email,
                'department': la.employee.department.department_name if la.employee.department else None,
                'designation': la.employee.designation.designation_name if la.employee.designation else None,
            },
            'leave_type': {
                'id': la.leave_type.id,
                'leave_type_name': la.leave_type.leave_type_name,
                'description': la.leave_type.description,
                'max_days_allowed': la.leave_type.max_days_allowed,
            },
            'start_date': la.start_date,
            'end_date': la.end_date,
            'total_days': la.total_days,
            'status': la.status,
            'applied_date': la.applied_date,
        }
        for la in leave_applications
    ]

    return JsonResponse({'leave_applications': result}, safe=False)


    