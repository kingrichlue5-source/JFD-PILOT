from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('hmis/', views.hmis_summary, name='hmis-summary'),
    path('hmis/dhis2/', views.dhis2_export, name='dhis2-export'),
    path('hmis/csv/', views.csv_export, name='csv-export'),
    path('hmis/xlsx/', views.xlsx_export, name='xlsx-export'),
    path('diagnoses/top/', views.top_diagnoses, name='top-diagnoses'),
    path('revenue/monthly/', views.monthly_revenue, name='monthly-revenue'),
    path('attendance/trend/', views.attendance_trend, name='attendance-trend'),
    path('patients/demographics/', views.patient_demographics, name='patient-demographics'),
    path('departments/utilization/', views.department_utilization, name='department-utilization'),
    path('beds/occupancy/', views.bed_occupancy_report, name='bed-occupancy-report'),
]
