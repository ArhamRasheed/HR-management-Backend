from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
from django.http import JsonResponse
from .models import Employee, EmployeeInsurance, Payroll, Department, Designation, Attendance, LeaveApplication, LeaveType, InsurancePlan, InterviewedCandidate, Complaint, MonthlyCompanyReport, MonthlyEmployeeReport
from django.contrib.auth.hashers import check_password
import secrets
from .decorators import hr_required


def add_employee(full_name, email, phone, applied_position, department): #add
    Employee.objects.create(full_name=full_name, email=email, phone=phone, applied_position=applied_position, department=department, employment_status="active")

def delete_employee(employee_id): #delete
    Employee.objects.filter(id=employee_id).delete()

def update_employee(employee_id, **kwargs): #update
    Employee.objects.filter(id=employee_id).update(**kwargs)

def add_department(department_name): #add
    Department.objects.create(department_name=department_name)

def delete_department(department_name): #delete
    Department.objects.filter(department_name=department_name).delete()

def update_department(department_name, **kwargs): #update
    Department.objects.filter(department_name=department_name).update(**kwargs)

def add_designation(designation_name): #add
    Designation.objects.create(designation_name=designation_name)

def delete_designation(designation_name): #delete
    Designation.objects.filter(designation_name=designation_name).delete()

def update_designation(designation_name, **kwargs): #update
    Designation.objects.filter(designation_name=designation_name).update(**kwargs)

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
    if not candidate_id:
        return JsonResponse({'message': 'No candidate ID provided.'}, status=400)
    candidate = InterviewedCandidate.objects.filter(id=candidate_id, status='shortlisted').first()
    if not candidate:
        return JsonResponse({'message': 'Candidate not found or not shortlisted.'}, status=404)
    add_employee(candidate.full_name, candidate.email, candidate.phone, candidate.applied_position, candidate.department)
    return JsonResponse({'message': 'Employee hired successfully.'})

@api_view(['GET'])
@permission_classes([AllowAny])
def reports_view(request):
    data = json.loads(request.body)
    doc_type = data.get('doc_type')
    if 'company_report' in doc_type and 'employee_report' in doc_type:
        c_reports = MonthlyCompanyReport.objects.all()
        e_reports = MonthlyEmployeeReport.objects.all()
        return JsonResponse({
            'company_reports': list(c_reports.values()),
            'employee_reports': list(e_reports.values())
        })
    elif 'company_report' in doc_type:
        c_reports = MonthlyCompanyReport.objects.all()
        return JsonResponse({
            'company_reports': list(c_reports.values())
        })
    elif 'employee_report' in doc_type:
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
    # Implementation of generate payroll view
    pass
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
