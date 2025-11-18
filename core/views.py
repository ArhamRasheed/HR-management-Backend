from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json
from django.http import JsonResponse
from .models import Employee, EmployeeInsurance, Payroll, Department, Designation, Attendance, LeaveApplication, LeaveType, InsurancePlan, InterviewedCandidate, Complaint
from django.contrib.auth.hashers import check_password
import secrets


def add_employee(full_name, email): #add
    Employee.objects.create(full_name=full_name, email=email, employment_status="active")

def delete_employee(employee_id): #delete
    Employee.objects.filter(id=employee_id).delete()

def update_employee(employee_id, **kwargs): #update
    Employee.objects.filter(id=employee_id).update(**kwargs)

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
    if not employee:
        return JsonResponse({
            'message': 'Employee not found.'
        }, status=404)
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

def employee_list_view(request):
    # Implementation of employee list view
    pass    
def employee_detail_view(request, employee_id):
    # Implementation of employee detail view
    pass
def department_list_view(request):
    # Implementation of department list view
    pass
def designation_list_view(request):
    # Implementation of designation list view
    pass
def shortlisted_candidate_list_view(request):
    # Implementation of shortlisted candidate list view
    pass
@api_view(['POST'])
def hire_employee_view(request):
    pass
def reports_view(request):
    # Implementation of reports view
    pass
def department_view(request, department_name):
    # Implementation of department view
    pass
def old_employee_records_view(request):
    # Implementation of old employee records view
    pass
def generate_payroll_view(request, employee_id):
    # Implementation of generate payroll view
    pass
def payroll_history_view(request):
    # Implementation of payroll history view
    pass
def add_department_view(request):
    # Implementation of add department view
    pass