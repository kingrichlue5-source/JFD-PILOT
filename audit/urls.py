from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('logs/', views.audit_log_list, name='audit-log-list'),
    path('login-logs/', views.login_log_list, name='login-log-list'),
    path('data-access-logs/', views.data_access_log_list, name='data-access-log-list'),
]
