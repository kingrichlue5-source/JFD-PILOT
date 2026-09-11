from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.PatientListView.as_view(), name='patient-list'),
    path('search/', views.patient_search, name='patient-search'),
    path('register/', views.walk_in_registration_api, name='patient-register'),
    path('<uuid:pk>/', views.PatientDetailView.as_view(), name='patient-detail'),
    path('<uuid:patient_id>/allergies/', views.PatientAllergyListView.as_view(), name='patient-allergy-list'),
    path('<uuid:patient_id>/allergies/<uuid:pk>/', views.PatientAllergyDetailView.as_view(), name='patient-allergy-detail'),
    path('<uuid:patient_id>/alerts/', views.PatientAlertListView.as_view(), name='patient-alert-list'),
    path('<uuid:patient_id>/alerts/<uuid:pk>/', views.PatientAlertDetailView.as_view(), name='patient-alert-detail'),
    path('<uuid:patient_id>/documents/', views.PatientDocumentListView.as_view(), name='patient-document-list'),
    path('<uuid:patient_id>/documents/<uuid:pk>/', views.PatientDocumentDetailView.as_view(), name='patient-document-detail'),
    path('merge/', views.merge_patients, name='patient-merge'),
]
