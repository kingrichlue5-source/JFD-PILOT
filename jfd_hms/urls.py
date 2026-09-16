"""
URL configuration for jfd_hms project.
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Admin pages (must be before Django admin to avoid catch-all)
    path('admin/users/', views.admin_users, name='admin-users'),
    path('admin/profile/', views.admin_user_profile, name='admin-profile'),
    path('admin/roles/', views.admin_roles, name='admin-roles'),
    path('admin/departments/', views.admin_departments, name='admin-departments'),
    path('admin/audit/', views.admin_audit_trail, name='admin-audit'),
    path('admin/login-history/', views.admin_login_history, name='admin-login-history'),
    path('admin/settings/', views.admin_settings, name='admin-settings'),
    path('admin/triage-criteria/', views.admin_triage_criteria, name='admin-triage-criteria'),

    path('admin/', admin.site.urls),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Debug endpoints (temporary)
    path('debug-env/', views.debug_env, name='debug-env'),
    path('debug-render/', views.debug_render, name='debug-render'),
    path('setup-prod/', views.setup_prod, name='setup-prod'),

    # Template views (pages)
    path('', views.index, name='index'),
    path('patients/search/', views.patient_search, name='patient-search-page'),
    path('patients/register/', views.patient_register, name='patient-register-page'),
    path('patients/<uuid:patient_id>/profile/', views.patient_profile, name='patient-profile-page'),
    path('clinical/triage-pending/', views.triage_awaiting_registration, name='triage-pending-page'),
    path('clinical/follow-up-queue/', views.follow_up_queue, name='follow-up-queue-page'),
    path('clinical/triage/', views.triage_dashboard, name='triage-dashboard-page'),
    path('clinical/triage-ticket/', views.triage_ticket, name='triage-ticket-page'),
    path('opd/', views.opd_consultation, name='opd-consultation-page'),
    path('clinical/ipd/', views.ipd_dashboard, name='ipd-dashboard-page'),
    path('clinical/emergency/', views.emergency_dashboard, name='emergency-dashboard-page'),
    path('clinical/obgyn/', views.obgyn_dashboard, name='obgyn-dashboard-page'),
    path('clinical/surgery/', views.surgery_dashboard, name='surgery-dashboard-page'),
    path('clinical/diagnostics/', views.diagnostics_dashboard, name='diagnostics-dashboard-page'),
    path('pharmacy/dispensing/', views.pharmacy_dispensing, name='pharmacy-dispensing-page'),
    path('cashier/', views.cashier, name='cashier-page'),
    path('cashier/payment-history/', views.payment_history, name='payment-history-page'),
    path('receipt/<uuid:payment_id>/', views.receipt_detail, name='receipt-page'),
    path('invoice/<uuid:invoice_id>/', views.invoice_detail, name='invoice-detail-page'),
    path('inventory/', views.inventory_dashboard, name='inventory-dashboard-page'),
    path('inventory/manage/', views.inventory_management, name='inventory-management-page'),
    path('clinical/appointments/', views.appointments_dashboard, name='appointments-dashboard-page'),
    path('vital-events/', views.vital_events_dashboard, name='vital-events-dashboard-page'),
    path('reports/hmis/', views.hmis_dashboard, name='hmis-dashboard-page'),
    path('clinical/er-evaluation/', views.er_nurse_evaluation, name='er-evaluation-page'),
    path('clinical/pediatric/', views.pediatric_assessment, name='pediatric-page'),
    path('clinical/nurse-notes/', views.nurse_notes, name='nurse-notes-page'),
    path('lab/', lambda request: redirect('/clinical/diagnostics/')),

    # API endpoints
    path('api/auth/', include('users_auth.urls')),
    path('api/patients/', include('patients.urls')),
    path('api/clinical/', include('clinical.urls')),
    path('api/pharmacy/', include('pharmacy.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/export/', include('exports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
