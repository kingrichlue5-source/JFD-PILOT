# JFD Hospital HMS — Automated Walkthrough (v4.0)

**System:** JFD Hospital Management System
**Server:** http://127.0.0.1:8000
**Date:** September 2026

---

## How to Run

```bash
# Start pilot server
start_pilot.bat

# Run automated tests
venv\Scripts\activate
python manage.py test tests.test_walkthrough_automated -v 2
```

---

## Scenario A: Standard OPD (Registration → Triage → OPD → Discharge)

**Role:** Admin (all permissions)

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| A1 | Login | `POST /api/auth/login/` | 200 |
| A2 | Register patient | `POST /api/patients/` | 201 + MRN |
| A3 | Create visit | `POST /api/clinical/visits/` | 201 |
| A4 | Submit triage | `POST /api/clinical/visits/{id}/triage/submit/` | 200 |
| A5 | Create encounter | `POST /api/clinical/visits/{id}/encounters/` | 201 |
| A6 | Add diagnosis | `POST /api/clinical/encounters/{id}/diagnoses/` | 201 |
| A7 | Place lab order | `POST /api/clinical/visits/{id}/place-order/` | 201 |
| A8 | Write prescription | `POST /api/pharmacy/prescriptions/` | 201 |
| A9 | Add prescription item | `POST /api/pharmacy/prescriptions/{id}/items/` | 201 |

**UI Buttons (for manual testing):**
- `/patients/register/` → "New Registration" button
- `/clinical/triage/` → Patient queue → "Complete Triage & Route Patient"
- `/opd/` → "Find Active Visits" → Select patient → SOAP → "Finalize Encounter"

---

## Scenario B: Emergency Bypass (Critical — Instant ER Entry)

**Role:** Admin (simulating ER Doctor)

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| B1 | Login | `POST /api/auth/login/` | 200 |
| B2 | Activate instant ER bypass | `POST /api/clinical/instant-er-bypass/` | 201 + temp_token |
| B3 | Verify emergency visit | `GET /api/clinical/visits/{id}/` | status=checked_in |
| B4 | Verify temp patient | Check: `is_temporary=True`, `mrn=null` | Correct |

**UI Buttons (for manual testing):**
- `/clinical/emergency/` → Red "INSTANT ER BYPASS" button → Fill modal → "ACTIVATE BYPASS"
- Patient row shows red TEMP badge → "Complete Registration" button for reconciliation

---

## Scenario C: Inpatient Admission (IPD)

**Role:** Admin (simulating IPD Doctor)

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| C1 | Login | `POST /api/auth/login/` | 200 |
| C2 | Register patient | `POST /api/patients/` | 201 + MRN |
| C3 | Create visit (IPD) | `POST /api/clinical/visits/` | 201 |
| C4 | Create encounter | `POST /api/clinical/visits/{id}/encounters/` | 201 |
| C5 | Find available bed | `GET /api/clinical/beds/?is_occupied=false` | 200 |
| C6 | Admit patient | `POST /api/clinical/admissions/` | 201 |
| C7 | Discharge patient | `POST /api/clinical/admissions/{id}/discharge/` | 200 |

**UI Buttons (for manual testing):**
- `/clinical/ipd/` → Click green bed → "Admit" → Fill form → "Confirm"
- Occupied bed → "Discharge" → Select type → "Confirm Discharge"

---

## Scenario D: Multi-Visit Follow-up

**Role:** Admin

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| D1 | Login | `POST /api/auth/login/` | 200 |
| D2 | Register patient | `POST /api/patients/` | 201 + MRN |
| D3 | Create initial visit | `POST /api/clinical/visits/` | 201 |
| D4 | Schedule follow-up | `POST /api/clinical/appointments/` | 201 |
| D5 | Reschedule | `PATCH /api/clinical/appointments/{id}/` | 200 |

**UI Buttons (for manual testing):**
- `/clinical/appointments/` → "New Appointment" → Select patient → Set date → "Save"
- Appointment card → "Reschedule" → New date → "Confirm"

---

## Scenario E: Financial Cycle

**Role:** Admin (simulating Cashier)

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| E1 | Login | `POST /api/auth/login/` | 200 |
| E2 | Register patient | `POST /api/patients/` | 201 + MRN |
| E3 | Create visit | `POST /api/clinical/visits/` | 201 |
| E4 | Place order (auto-billing) | `POST /api/clinical/visits/{id}/place-order/` | 201 + invoice |
| E5 | Get invoice | `GET /api/billing/invoices/?visit={id}` | 200 |
| E6 | Process payment | `POST /api/billing/pay/` | 200 |
| E7 | Verify invoice status | `GET /api/billing/invoices/{id}/` | status=paid |

**UI Buttons (for manual testing):**
- `/cashier/` → Select patient → Review invoice → Enter amount → Select method → "Process Payment"

---

## Scenario F: Inventory Cycle

**Role:** Admin (simulating Inventory Manager)

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| F1 | Login | `POST /api/auth/login/` | 200 |
| F2 | Get stores | `GET /api/inventory/stores/` | 200 |
| F3 | Get items | `GET /api/inventory/items/` | 200 |
| F4 | Receive stock | `POST /api/inventory/receive/` | 201 |
| F5 | Check stock | `GET /api/inventory/stock/` | 200 |

**UI Buttons (for manual testing):**
- `/inventory/stock/` → "Receive Stock" → Select item → Enter qty → "Save"
- `/inventory/stock/` → "Store Transfer" → Select from/to → Enter qty → "Transfer Stock"

---

## Scenario G: Admin Security & Roles

**Role:** Multiple users

| Step | Action | Expected |
|------|--------|----------|
| G1 | Login as admin | 200 |
| G2 | Login as doctor | 200 |
| G3 | Login as nurse | 200 |
| G4 | Login as pharmacist | 200 |
| G5 | Login as cashier | 200 |
| G6 | Wrong password | 401 |
| G7 | Unauthorized endpoint | 403 |

---

## Scenario H: Reporting

**Role:** Admin

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| H1 | Login | `POST /api/auth/login/` | 200 |
| H2 | HMIS summary | `GET /api/reports/hmis/` | 200 |
| H3 | Daily revenue | `GET /api/billing/daily-revenue/` | 200 |
| H4 | Dispensing summary | `GET /api/pharmacy/reports/dispensing-summary/` | 200 |

---

## Scenario I: Clinical-First Flow (Triage Before Registration)

**Role:** Admin (simulating Triage Nurse)

| Step | Action | API Call | Expected |
|------|--------|----------|----------|
| I1 | Login | `POST /api/auth/login/` | 200 |
| I2 | Clinical-First triage (anonymous) | `POST /api/clinical/triage-first/` | 201 |
| I3 | Verify visit status | Check: status=pending_registration | Correct |
| I4 | Verify suggested acuity | Check: suggested_acuity set | Set by engine |
| I5 | Complete registration | `POST /api/clinical/triage-first/complete-registration/` | 200 |
| I6 | Verify MRN assigned | `GET /api/patients/{id}/` | mrn set |

**UI Buttons (for manual testing):**
- `/clinical/triage/` → "Clinical-First Triage" button → Fill modal → "Submit Triage"
- `/patients/` → Yellow alert banner → "Complete Registration" → Fill form → "Register Patient"

---

## Role Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | doctor | doctor123 |
| Nurse | nurse | nurse123 |
| Triage | triage | triage123 |
| Pharmacist | pharmacist | pharm123 |
| Cashier | cashier | cash123 |
| Lab Tech | labtech | lab123 |
| Radiology | radiology | radiology123 |
| Inventory | inventory | inventory123 |

---

## Run

```bash
python tests/test_walkthrough_automated.py
```

**Expected:** All 62 steps across 9 scenarios pass at 100%.
