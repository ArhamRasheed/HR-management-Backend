from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-session/', views.check_session_view, name='check_session'),
    
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    path('employees/all/', views.employee_list_view, name='employee_list'), #working
    path('employees/', views.employee_detail_view, name='employee_detail'), #working
    path('employees/hire/', views.hire_employee_view, name='hire_employee'), #working
    path('employees/<int:employee_id>/update/', views.update_employee, name='update_employee'), #working
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'), #working
    
    path('departments/', views.department_list_view, name='department_list'),
    path('departments/employees/', views.department_view, name='department'),
    path('add_department/', views.add_department_view, name='add_department'),
    path('departments/<str:department_name>/update/', views.update_department, name='update_department'),
    path('departments/<str:department_name>/delete/', views.delete_department, name='delete_department'),
    
    path('designations/', views.designation_list_view, name='designation_list'),
    path('add_designation/', views.add_designation, name='add_designation'),
    path('designations/<str:designation_name>/update/', views.update_designation, name='update_designation'),
    path('designations/<str:designation_name>/delete/', views.delete_designation, name='delete_designation'),
    
    path('shortlisted-candidates/', views.shortlisted_candidate_list_view, name='shortlisted_candidate_list'), #working
    path('interviewed-candidates/', views.candidate_list_view, name='interviewed_candidate_list'), #working
    path('old-employee-records/', views.old_employee_records_view, name='old_employee_records'), #working
    
    path('payroll-generate/employee/', views.generate_payroll_view, name='generate_payroll'),
    path('payroll-history/', views.payroll_history_view, name='payroll_history'),
    path('report/', views.reports_view, name='reports'),
    
    path('leaves/all', views.leave_list_view, name='leave_list'),
    path('add_leave/', views.add_leave_view, name='add_leave'),
    path('leaves/<int:leave_id>/update/', views.update_leave_status, name='update_leave_status'),
    path('leaves/<int:leave_id>/delete/', views.delete_leave, name='delete_leave'),
    path('leaves/employees', views.employee_leave, name='employee_leaves'),
    
    path('attendance/view/', views.view_attendance_view, name='view_attendance'),
    path('attendance/mark/<int:employee_id>/', views.mark_attendance, name='mark_attendance'),
    
    path('insurance/all/', views.insurance_view, name='insurance'),
    path('add_insurance/', views.add_insurance_view, name='add_insurance'),
    path('insurance/<int:insurance_id>/delete/', views.delete_insurance, name='delete_leave'),
    path('insurance/<int:insurance_id>/update/', views.update_insurance, name='update_leave_status'),
    path('insurance/employees/', views.insured_employees_view, name='insured_employees'),
    
    path('edit-insurances/<int:employee_id>/', views.edit_insurances_view, name='edit_insurances'),
    path('edit-leaves/<int:employee_id>/', views.edit_leaves_view, name='edit_leaves'),
    
    path('apply-insurance/<int:employee_id>/', views.apply_insurences, name='apply_insurances'),
    path('apply-leaves/<int:employee_id>/', views.apply_leaves, name='apply_leaves'),
    
    path('complain/all/', views.all_complaints_view, name='all_complains'), #working
    path('add_complain/', views.add_complaint_view, name='add_complain'), #working
    path('complain/<int:complain_id>/delete/', views.delete_complain, name='delete_complain'), #working
    path('complain/<int:complain_id>/update/', views.update_complain, name='update_complain'), #working
]