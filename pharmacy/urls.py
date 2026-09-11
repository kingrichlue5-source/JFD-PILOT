from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    # Medications
    path('medications/', views.MedicationListView.as_view(), name='medication-list'),
    path('medications/<uuid:pk>/', views.MedicationDetailView.as_view(), name='medication-detail'),

    # Prescriptions
    path('prescriptions/', views.PrescriptionListView.as_view(), name='prescription-list'),
    path('prescriptions/<uuid:pk>/', views.PrescriptionDetailView.as_view(), name='prescription-detail'),
    path('prescriptions/<uuid:prescription_id>/items/', views.PrescriptionItemListView.as_view(), name='prescription-item-list'),
    path('prescription-items/<uuid:pk>/', views.PrescriptionItemDetailView.as_view(), name='prescription-item-detail'),

    # Dispensing
    path('dispensing/', views.DispensingListView.as_view(), name='dispensing-list'),
    path('dispensing/<uuid:pk>/', views.DispensingDetailView.as_view(), name='dispensing-detail'),
    path('dispense/', views.dispense_medication, name='dispense'),

    # Reports
    path('reports/dispensing-summary/', views.dispensing_summary, name='dispensing-summary'),
    path('reports/prescription-summary/', views.prescription_summary, name='prescription-summary'),
]
