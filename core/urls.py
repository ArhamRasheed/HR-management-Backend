from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-session/', views.check_session_view, name='check_session'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('employees/', views.employee_list_view, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail_view, name='employee_detail'),
    path('departments/', views.department_list_view, name='department_list'),
    path('designations/', views.designation_list_view, name='designation_list'),
    path('shortlisted-candidates/', views.shortlisted_candidate_list_view, name='shortlisted_candidate_list'),
    path('interviewed-candidates/', views.candidate_list_view, name='interviewed_candidate_list'),
    path('employees/hire/', views.hire_employee_view, name='hire_employee'),
    path('report/company', views.reports_view, name='reports'),
    path('departments/', views.department_view, name='department'),
    path('old-employee-records/', views.old_employee_records_view, name='old_employee_records'),
    path('payroll-generate/employee/', views.generate_payroll_view, name='generate_payroll'),
    path('payroll-history/', views.payroll_history_view, name='payroll_history'),
    path('add_department/', views.add_department_view, name='add_department'),
]

