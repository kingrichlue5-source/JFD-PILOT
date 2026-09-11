from django.urls import path
from . import views

app_name = 'clinical'

urlpatterns = [
    # Visits
    path('visits/', views.VisitListView.as_view(), name='visit-list'),
    path('visits/<uuid:pk>/', views.VisitDetailView.as_view(), name='visit-detail'),
    path('visits/<uuid:visit_id>/status/', views.visit_status_transition, name='visit-status'),

    # Triage
    path('triage-queue/', views.triage_queue, name='triage-queue'),
    path('triage-evaluate/', views.triage_evaluate, name='triage-evaluate'),
    path('visits/<uuid:visit_id>/triage/', views.TriageRecordListView.as_view(), name='triage-list'),
    path('visits/<uuid:visit_id>/triage/submit/', views.triage_submit, name='triage-submit'),
    path('triage/<uuid:pk>/', views.TriageRecordDetailView.as_view(), name='triage-detail'),

    # Encounters
    path('visits/<uuid:visit_id>/encounters/', views.EncounterListView.as_view(), name='encounter-list'),
    path('encounters/<uuid:pk>/', views.EncounterDetailView.as_view(), name='encounter-detail'),
    path('encounters/<uuid:encounter_id>/finalize/', views.finalize_encounter, name='encounter-finalize'),

    # Vital Signs
    path('visits/<uuid:visit_id>/vitals/', views.VitalSignsListView.as_view(), name='vitals-list'),
    path('vitals/<uuid:pk>/', views.VitalSignsDetailView.as_view(), name='vitals-detail'),

    # Diagnoses
    path('encounters/<uuid:encounter_id>/diagnoses/', views.DiagnosisListView.as_view(), name='diagnosis-list'),
    path('diagnoses/<uuid:pk>/', views.DiagnosisDetailView.as_view(), name='diagnosis-detail'),

    # Orders
    path('visits/<uuid:visit_id>/orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/', views.AllOrdersListView.as_view(), name='all-orders-list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='order-detail'),

    # Progress Notes
    path('encounters/<uuid:encounter_id>/notes/', views.ProgressNoteListView.as_view(), name='progress-note-list'),
    path('notes/<uuid:pk>/', views.ProgressNoteDetailView.as_view(), name='progress-note-detail'),

    # Nursing Notes
    path('encounters/<uuid:encounter_id>/nursing-notes/', views.NursingNoteListView.as_view(), name='nursing-note-list'),
    path('nursing-notes/<uuid:pk>/', views.NursingNoteDetailView.as_view(), name='nursing-note-detail'),

    # Admissions
    path('admissions/', views.AdmissionListView.as_view(), name='admission-list'),
    path('admissions/<uuid:pk>/', views.AdmissionDetailView.as_view(), name='admission-detail'),
    path('admissions/<uuid:admission_id>/transfers/', views.AdmissionTransferListView.as_view(), name='admission-transfer-list'),
    path('admissions/<uuid:admission_id>/discharge/', views.discharge_patient, name='admission-discharge'),

    # Ward/Bed Management
    path('wards/', views.WardListView.as_view(), name='ward-list'),
    path('wards/<uuid:pk>/', views.WardDetailView.as_view(), name='ward-detail'),
    path('beds/', views.BedListView.as_view(), name='bed-list'),
    path('beds/<uuid:pk>/', views.BedDetailView.as_view(), name='bed-detail'),
    path('bed-occupancy/', views.bed_occupancy, name='bed-occupancy'),

    # Patient Movements
    path('movements/', views.PatientMovementListView.as_view(), name='movement-list'),

    # OPD Module - Catalogues
    path('lab-tests/', views.lab_test_catalogue, name='lab-test-catalogue'),
    path('radiology-tests/', views.radiology_test_catalogue, name='radiology-test-catalogue'),
    path('icd-lookup/', views.icd_diagnosis_lookup, name='icd-diagnosis-lookup'),

    # OPD Module - Orders
    path('visits/<uuid:visit_id>/place-order/', views.place_order, name='place-order'),
    path('visits/<uuid:visit_id>/orders-summary/', views.visit_orders_summary, name='visit-orders-summary'),

    # OBGYN
    path('antenatal/', views.AntenatalVisitListView.as_view(), name='antenatal-list'),
    path('antenatal/<uuid:pk>/', views.AntenatalVisitDetailView.as_view(), name='antenatal-detail'),
    path('labor/', views.LaborRecordListView.as_view(), name='labor-list'),
    path('labor/<uuid:pk>/', views.LaborRecordDetailView.as_view(), name='labor-detail'),
    path('delivery/', views.DeliveryRecordListView.as_view(), name='delivery-list'),
    path('delivery/<uuid:pk>/', views.DeliveryRecordDetailView.as_view(), name='delivery-detail'),
    path('birth/', views.BirthRecordListView.as_view(), name='birth-list'),
    path('birth/<uuid:pk>/', views.BirthRecordDetailView.as_view(), name='birth-detail'),
    path('postnatal/', views.PostnatalVisitListView.as_view(), name='postnatal-list'),
    path('postnatal/<uuid:pk>/', views.PostnatalVisitDetailView.as_view(), name='postnatal-detail'),

    # Surgery
    path('surgical/', views.SurgicalCaseListView.as_view(), name='surgical-list'),
    path('surgical/<uuid:pk>/', views.SurgicalCaseDetailView.as_view(), name='surgical-detail'),

    # Referrals
    path('referrals/', views.ReferralListView.as_view(), name='referral-list'),
    path('referrals/<uuid:pk>/', views.ReferralDetailView.as_view(), name='referral-detail'),

    # Appointments
    path('appointments/', views.AppointmentListView.as_view(), name='appointment-list'),
    path('appointments/<uuid:pk>/', views.AppointmentDetailView.as_view(), name='appointment-detail'),

    # Diagnostic Results
    path('diagnostic-results/', views.DiagnosticResultCreateView.as_view(), name='diagnostic-result-create'),
    path('diagnostic-results/<uuid:result_id>/verify/', views.verify_diagnostic_result, name='diagnostic-result-verify'),
    path('visits/<uuid:visit_id>/diagnostic-results/', views.DiagnosticResultListView.as_view(), name='diagnostic-result-list'),
    path('diagnostic-results/<uuid:pk>/', views.DiagnosticResultDetailView.as_view(), name='diagnostic-result-detail'),

    # Rooms
    path('rooms/', views.RoomListView.as_view(), name='room-list'),
    path('rooms/<uuid:pk>/', views.RoomDetailView.as_view(), name='room-detail'),

    # Specimens
    path('specimens/', views.SpecimenListView.as_view(), name='specimen-list'),
    path('specimens/<uuid:pk>/', views.SpecimenDetailView.as_view(), name='specimen-detail'),
    path('specimens/<uuid:specimen_id>/receive/', views.specimen_receive, name='specimen-receive'),
    path('specimens/<uuid:specimen_id>/complete/', views.specimen_complete, name='specimen-complete'),

    # Emergency Bypass
    path('emergency-bypass/', views.emergency_bypass, name='emergency-bypass'),

    # Enhanced Emergency Bypass (Instant ER with Token)
    path('instant-er-bypass/', views.instant_er_bypass, name='instant-er-bypass'),
    path('emergency-reconcile/', views.reconcile_emergency_patient, name='emergency-reconcile'),

    # Clinical-First Flow (Triage → Registration)
    path('triage-first/', views.triage_first, name='triage-first'),
    path('triage-first/complete-registration/', views.complete_clinical_first_registration, name='triage-first-complete-registration'),

    # Inter-Departmental Transfers
    path('visits/<uuid:visit_id>/transfer/', views.transfer_patient, name='transfer-patient'),
    path('visits/<uuid:visit_id>/escalate-to-er/', views.escalate_to_er, name='escalate-to-er'),
    path('visits/<uuid:visit_id>/admit-to-ipd/', views.admit_to_ipd, name='admit-to-ipd'),
]
