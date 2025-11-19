from functools import wraps
from django.http import JsonResponse
from .models import Employee


def hr_required(view_func):
    """
    Decorator to check if the logged-in employee belongs to the HR department.
    
    Checks:
    1. Employee ID exists in session
    2. Employee belongs to HR department
    
    Returns:
    - 404 if employee not found in session
    - 403 if employee is not from HR department
    - Proceeds with view execution if all checks pass
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        employee_id = request.session.get('employee_id')
        
        if not employee_id:
            return JsonResponse({
                'message': 'Employee not found in session'
            }, status=404)
        
        if not request.session['department'] == 'HR':
            return JsonResponse({
                'message': 'Access denied. Only HR Employees can view employee list.'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper

