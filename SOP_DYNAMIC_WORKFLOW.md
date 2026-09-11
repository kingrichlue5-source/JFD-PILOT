# JFD Hospital HMS — Standard Operating Procedures (SOPs)
## Dynamic State Machine Workflow — v2.0

**Effective Date:** September 2026
**System:** JFD Hospital Management Information System
**Hospital:** Jackson F. Doe Memorial Regional Referral Hospital

---

## TABLE OF CONTENTS

1. [Overview of Patient Pathways](#1-overview-of-patient-pathways)
2. [SOP for Registration Clerks](#2-sop-for-registration-clerks)
3. [SOP for Triage Nurses](#3-sop-for-triage-nurses)
4. [SOP for ER Doctors & Nurses](#4-sop-for-er-doctors--nurses)
5. [SOP for OPD Doctors](#5-sop-for-opd-doctors)
6. [SOP for IPD/Ward Doctors](#6-sop-for-ipdward-doctors)
7. [SOP for Pharmacists](#7-sop-for-pharmacists)
8. [SOP for Cashiers](#8-sop-for-cashiers)
9. [SOP for System Administrators](#9-sop-for-system-administrators)
10. [State Reference Matrix](#10-state-reference-matrix)
11. [API Quick Reference](#11-api-quick-reference)

---

## 1. Overview of Patient Pathways

The system supports **three distinct patient pathways**. The pathway used depends on how the patient enters the hospital.

### Pathway A: Standard Flow (Most Common)
```
Registration → Triage → OPD / ER / IPD → Treatment → Discharge
```
**When to use:** Patient arrives at registration desk, has ID, can provide demographics.

### Pathway B: Clinical-First Flow
```
Triage (Anonymous) → Clinical Assessment → Registration (Retroactive)
```
**When to use:** Patient needs immediate clinical attention but registration desk is busy/closed. Triage nurse sees patient first, creates anonymous triage record, then clerk completes registration later.

### Pathway C: Emergency Bypass (Critical)
```
Instant ER Entry → Treatment → Retroactive Registration & Triage
```
**When to use:** Life-threatening emergency. Patient rushed directly to ER. Zero time for registration or triage. Doctor begins treatment immediately.

---

## 2. SOP for Registration Clerks

**Role:** Patient Registration & Demographics
**Login:** `admin` / `admin123` (or your assigned credentials)
**Dashboard:** `/patients/register/`

### 2.1 Standard Patient Registration

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Click **"Register New Patient"** | `/patients/register/` |
| 2 | Enter: First Name, Last Name, Date of Birth, Gender, Phone | Registration form |
| 3 | Enter: Blood Type, Marital Status, Address (if available) | Registration form |
| 4 | Select: Payer Category (Self Pay, NHSLA, etc.) | Registration form |
| 5 | Click **"Save"** — System generates lifelong MRN (JFD-YYYY-XXXXX) | Registration form |
| 6 | Inform patient of their MRN number | Verbal |

**Key Rules:**
- MRN is generated automatically — never manually enter one
- Duplicate check runs on (Name + DOB) and (Phone) — if alert appears, search for existing patient first
- Every patient MUST have an MRN before any clinical encounter (except Emergency Bypass)

### 2.2 Registering a Walk-In Patient (Creates Visit Immediately)

| Step | Action |
|------|--------|
| 1 | Go to `/patients/register/` |
| 2 | Fill in demographics + select Visit Type (OPD/IPD/ER) |
| 3 | System creates Patient AND Visit simultaneously |
| 4 | Patient goes directly to Triage Queue with status `checked_in` |

### 2.3 Completing Emergency Bypass Registration (Retroactive)

**When to do this:** ER doctor used Emergency Bypass. Patient has temporary token (TEMP-ER-YYYY-XXXXX). Patient is now stabilized.

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Search for patient by temporary token or name "UNKNOWN PATIENT" | `/patients/search/` |
| 2 | Open the patient record — note **"TEMPORARY"** badge | Patient detail |
| 3 | Click **"Complete Registration"** | Patient edit form |
| 4 | Enter full demographics: real name, DOB, phone, address, insurance | Edit form |
| 5 | Click **"Save"** — System generates MRN and links all clinical records | Edit form |
| 6 | Verify MRN is now displayed (no longer shows TEMP token) | Patient detail |

### 2.4 Completing Clinical-First Registration (Retroactive)

**When to do this:** Triage nurse used Clinical-First flow. Patient has visit with status `pending_registration`.

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Search for visits with status "Pending Registration" | Visit search |
| 2 | Open the visit — note **"Pending Registration"** badge | Visit detail |
| 3 | Click **"Complete Registration"** | Registration form |
| 4 | Enter full patient demographics | Registration form |
| 5 | System generates MRN, links to existing visit and triage record | System |
| 6 | Visit status changes to `in_progress` | System |

---

## 3. SOP for Triage Nurses

**Role:** Triage Assessment & Patient Routing
**Login:** `triage` / `triage123`
**Dashboard:** `/clinical/triage/`

### 3.1 Standard Triage (Pathway A)

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Open Triage Dashboard — see queue of `checked_in` patients | `/clinical/triage/` |
| 2 | Click on a patient in the queue | Triage form |
| 3 | Enter **Chief Complaint** (free text) | Triage form |
| 4 | Enter **Vital Signs**: Temperature, HR, RR, BP, SpO2, Pain Scale | Triage form |
| 5 | System **auto-suggests** Acuity Level (1-5) and Department based on vitals | System suggestion |
| 6 | **Review suggestion** — accept or override | Triage form |
| 7 | If overriding acuity: select new level + provide clinical justification | Override form |
| 8 | If overriding department: select new department + provide justification | Override form |
| 9 | Click **"Submit Triage"** | Triage form |
| 10 | Patient appears in department queue (OPD, ER, or IPD) | Department dashboard |

**Acuity Levels:**
| Level | Name | Color | Typical Action |
|-------|------|-------|----------------|
| 1 | Resuscitation | Red | Immediate ER — STAT |
| 2 | Emergent | Orange | ER within minutes |
| 3 | Urgent | Yellow | OPD/ER within 30 min |
| 4 | Less Urgent | Blue | OPD within 1-2 hours |
| 5 | Non-Urgent | Green | OPD routine |

**Auto-Suggestion Rules (Admin-configurable at `/admin/triage-criteria/`):**
- SpO2 < 90% → **Level 1 (Resuscitation)** → ER
- Systolic BP < 90 → **Level 2 (Emergent)** → ER
- Heart Rate > 120 → **Level 3 (Urgent)** → ER
- Temperature > 40°C → **Level 3 (Urgent)** → OPD
- Pain Scale ≥ 8 → **Level 3 (Urgent)** → OPD

**IMPORTANT:** The system suggestion is advisory ONLY. The clinician's judgment is always final. However, downgrading from a higher to lower severity requires a written justification.

### 3.2 Clinical-First Triage (Pathway B)

**When to use:** Patient needs immediate assessment but registration is not yet complete.

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Click **"Clinical-First Triage"** button | Triage dashboard |
| 2 | Enter Chief Complaint and Vital Signs (no patient selection needed) | Anonymous triage form |
| 3 | System evaluates vitals and suggests acuity + department | System suggestion |
| 4 | Accept or override (same as standard triage) | Override form |
| 5 | Click **"Submit Clinical-First Triage"** | Triage form |
| 6 | System creates anonymous visit with status `pending_registration` | System |
| 7 | **Note the Visit Number** — give to clerk for registration | Verbal |
| 8 | Patient can proceed to clinical assessment immediately | Clinical area |

**After stabilization:** Clerk completes registration using the visit number (see SOP 2.4).

### 3.3 Emergency Bypass Triage (Pathway C)

**When to use:** NOT used for Pathway C. Emergency Bypass is triggered from the **ER Dashboard** by the ER doctor or nurse (see SOP 4.1).

---

## 4. SOP for ER Doctors & Nurses

**Role:** Emergency Care & Critical Interventions
**Login:** `doctor` / `doctor123` (Doctor) or `nurse` / `nurse123` (Nurse)
**Dashboard:** `/clinical/emergency/`

### 4.1 Instant ER Bypass (Pathway C — Critical Emergency)

**When to use:** Patient arrives in critical condition. No time for registration or triage.

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Click **"INSTANT ER BYPASS"** button (red, top of ER dashboard) | `/clinical/emergency/` |
| 2 | Enter: Patient name (if known), Chief Complaint, Reason | Bypass modal |
| 3 | Click **"Activate Bypass"** | Bypass modal |
| 4 | System creates: Temporary Patient (TEMP-ER-YYYY-XXXXX) + Visit | System |
| 5 | **NOTE the Temporary Token** — displayed in flashing red banner | ER dashboard |
| 6 | Begin treatment immediately — no administrative blocks | Clinical work |
| 7 | Use temporary token for ALL clinical orders (labs, meds, imaging) | Order forms |

**What you can do with a temporary token:**
- Write clinical notes / encounters
- Order laboratory tests
- Order medications
- Request radiology/imaging
- Request blood products
- Document procedures

**What you CANNOT do until reconciliation:**
- Generate a formal invoice (use "Emergency Care" billing)
- Discharge the patient formally

### 4.2 ER Evaluation Workflow

| Step | Action | Screen |
|------|--------|--------|
| 1 | Patient appears in Active ER Cases table | ER Dashboard |
| 2 | Click **"Fill Evaluation"** | ER Nurse Evaluation form |
| 3 | Complete: HPI, PMH, ROS, Physical Exam, Interventions | Evaluation form |
| 4 | Click **"Save Evaluation"** | Evaluation form |
| 5 | Click **"Log Intervention"** (progress note) | Progress Note form |
| 6 | Click **"Process Disposition"** | Disposition modal |

### 4.3 ER Disposition Options

| Disposition | Action | Effect |
|-------------|--------|--------|
| **Admit to IPD** | Click "Admit to IPD" | Creates Admission record, assigns bed, changes visit to IPD |
| **Discharge** | Click "Discharge" | Marks visit completed, patient leaves |
| **Transfer to OPD** | Click "Transfer" | Changes department to OPD |
| **Escalate to Surgery** | Click "Transfer" → Surgery | Changes department to Surgery |

### 4.4 Reconciling Emergency Bypass Patient

**When to do:** Patient is stabilized. Registration clerk or ER nurse completes formal registration.

| Step | Action | Screen/API |
|------|--------|------------|
| 1 | Click **"Complete Registration"** next to the bypass patient | ER dashboard |
| 2 | Enter full demographics: Name, DOB, Gender, Phone, Insurance | Reconciliation form |
| 3 | Optionally backfill triage vitals if not yet recorded | Reconciliation form |
| 4 | Click **"Reconcile & Register"** | Reconciliation form |
| 5 | System generates MRN, links all clinical records, clears temporary flag | System |
| 6 | Visit status changes to `in_triage` or `in_progress` | System |

---

## 5. SOP for OPD Doctors

**Role:** Outpatient Consultation & Treatment
**Login:** `doctor` / `doctor123`
**Dashboard:** `/opd/`

### 5.1 Standard OPD Consultation

| Step | Action | Screen |
|------|--------|--------|
| 1 | Select patient from visit list (status: `in_progress`) | OPD dashboard |
| 2 | Review: Chief Complaint, Triage Assessment, Vitals, Allergies | OPD consultation |
| 3 | Document SOAP notes: Subjective, Objective, Assessment, Plan | SOAP form |
| 4 | Add Diagnosis (ICD-10 code search) | Diagnosis section |
| 5 | Place Orders (Lab, Radiology) | Order section |
| 6 | Write Prescriptions | Prescription section |
| 7 | Click **"Finalize Encounter"** | OPD consultation |
| 8 | System auto-posts orders to billing | System |

### 5.2 OPD to ER Escalation

**When to use:** Patient crashes during OPD consultation. Needs immediate ER care.

| Step | Action | API |
|------|--------|-----|
| 1 | Click **"Escalate to ER"** button | OPD consultation |
| 2 | Enter reason: "Patient condition deteriorating — [details]" | Escalation modal |
| 3 | Click **"Confirm Escalation"** | Escalation modal |
| 4 | System changes visit_type to `er`, department to ER | System |
| 5 | ER team is notified via dashboard | ER dashboard |
| 6 | Patient appears in ER Active Cases | ER dashboard |

**API:** `POST /api/clinical/visits/{visit_id}/escalate-to-er/`
```json
{
    "reason": "Patient developed chest pain during consultation"
}
```

### 5.3 OPD to IPD Admission

**When to use:** OPD doctor determines patient needs hospitalization.

| Step | Action | API |
|------|--------|-----|
| 1 | Click **"Admit to IPD"** button | OPD consultation |
| 2 | Enter: Admitting Diagnosis, Ward preference (optional) | Admission modal |
| 3 | Click **"Confirm Admission"** | Admission modal |
| 4 | System creates Admission record, assigns to IPD | System |
| 5 | IPD team sees patient in Admission Queue | IPD dashboard |

**API:** `POST /api/clinical/visits/{visit_id}/admit-to-ipd/`
```json
{
    "admitting_diagnosis": "Severe pneumonia requiring IV antibiotics",
    "ward_id": "optional-uuid",
    "bed_id": "optional-uuid"
}
```

---

## 6. SOP for IPD/Ward Doctors

**Role:** Inpatient Care & Discharge
**Login:** `doctor` / `doctor123`
**Dashboard:** `/clinical/ipd/`

### 6.1 IPD Bed Assignment

| Step | Action | Screen |
|------|--------|--------|
| 1 | View bed matrix — green = available, red = occupied | IPD dashboard |
| 2 | Click **"Admit"** on available bed (or auto-assigned from ER/OPD) | Bed matrix |
| 3 | Enter: Admission diagnosis, expected discharge date | Admission form |
| 4 | Click **"Confirm"** | Admission form |
| 5 | Bed status changes to occupied | System |

### 6.2 IPD Transfer (Bed-to-Bed)

| Step | Action | Screen |
|------|--------|--------|
| 1 | On occupied bed, click **"Transfer"** | Bed matrix |
| 2 | Select target bed (from available beds list) | Transfer modal |
| 3 | Enter reason: "Patient moved to [ward] for [reason]" | Transfer modal |
| 4 | Click **"Confirm Transfer"** | Transfer modal |
| 5 | Old bed freed, new bed occupied | System |

### 6.3 IPD Discharge

| Step | Action | Screen |
|------|--------|--------|
| 1 | On occupied bed, click **"Discharge"** | Bed matrix |
| 2 | Select discharge type: Routine / AMA / Referred / Transferred / Deceased | Discharge modal |
| 3 | Enter discharge summary | Discharge modal |
| 4 | Optionally schedule follow-up appointment | Discharge modal |
| 5 | Click **"Confirm Discharge"** | Discharge modal |
| 6 | Bed freed, visit marked completed, patient discharged | System |

---

## 7. SOP for Pharmacists

**Role:** Medication Dispensing
**Login:** `pharmacist` / `pharm123`
**Dashboard:** `/pharmacy/dispensing/`

### 7.1 Standard Dispensing

| Step | Action | Screen |
|------|--------|--------|
| 1 | View pending prescriptions | Dispensing dashboard |
| 2 | Select prescription | Prescription list |
| 3 | Verify medication, dosage, quantity | Dispensing form |
| 4 | Click **"Dispense"** | Dispensing form |
| 5 | System deducts stock and posts to billing | System |

**Note:** Emergency Bypass patients with temporary tokens can also receive medications. Their prescriptions are linked to the visit via temporary_token.

---

## 8. SOP for Cashiers

**Role:** Payment Processing
**Login:** `cashier` / `cash123`
**Dashboard:** `/cashier/`

### 8.1 Standard Payment

| Step | Action | Screen |
|------|--------|--------|
| 1 | Select patient / invoice | Cashier dashboard |
| 2 | Review line items and total | Invoice detail |
| 3 | Enter payment amount | Payment form |
| 4 | Select payment method: Cash / Mobile Money / Bank Transfer / Insurance | Payment form |
| 5 | Click **"Process Payment"** | Payment form |
| 6 | Print receipt | Receipt |

### 8.2 Emergency Care Billing

Emergency Bypass patients are billed under **"Emergency Care"** payer category. Invoices are created automatically when orders are placed. Once the patient is reconciled (formal registration), invoices are linked to the permanent MRN.

---

## 9. SOP for System Administrators

**Role:** System Configuration & User Management
**Login:** `admin` / `admin123`
**Dashboard:** `/admin/`

### 9.1 Managing Triage Criteria

| Step | Action | Screen |
|------|--------|--------|
| 1 | Navigate to **Admin → Triage Criteria** | `/admin/triage-criteria/` |
| 2 | View all active criteria rules | Criteria table |
| 3 | **Add new rule:** Fill in name, vital sign, operator, threshold, acuity, department | Create form |
| 4 | **Toggle rule:** Click Activate/Deactivate | Criteria table |
| 5 | **Delete rule:** Click Delete (requires confirmation) | Criteria table |

**Default Rules (12 seeded):**
| Rule | Vital Sign | Condition | → Acuity | → Dept |
|------|-----------|-----------|----------|--------|
| Severe Hypotension | Systolic BP | < 90 | 2 Emergent | ER |
| Hypertensive Crisis | Systolic BP | > 180 | 2 Emergent | ER |
| Severe Hypoxia | SpO2 | < 90 | 1 Resuscitation | ER |
| Mild Hypoxia | SpO2 | < 94 | 3 Urgent | ER |
| Severe Tachycardia | Heart Rate | > 120 | 3 Urgent | ER |
| Severe Bradycardia | Heart Rate | < 50 | 2 Emergent | ER |
| High Fever | Temperature | > 40 | 3 Urgent | OPD |
| Hypothermia | Temperature | < 35 | 2 Emergent | ER |
| Severe Tachypnea | Respiratory Rate | > 30 | 2 Emergent | ER |
| Hypoglycemia | Blood Glucose | < 60 | 2 Emergent | ER |
| Severe Hyperglycemia | Blood Glucose | > 400 | 2 Emergent | ER |
| Severe Pain | Pain Scale | ≥ 8 | 3 Urgent | OPD |

### 9.2 Viewing Workflow Transitions

All patient state changes are logged in the `WorkflowTransition` table. Access via API:
```
GET /api/clinical/movements/
```

### 9.3 Running Pilot Reset

```bash
python manage.py pilot_reset
```
This clears all clinical data, re-seeds departments/roles/medications/triage criteria, and creates test user accounts.

---

## 10. State Reference Matrix

### Visit Statuses

| Status | Meaning | Who Sets It |
|--------|---------|-------------|
| `scheduled` | Appointment booked, not yet arrived | System / Clerk |
| `checked_in` | Patient arrived at registration | Clerk |
| `in_triage` | Patient in triage queue | System (auto after reconciliation) |
| `in_progress` | Active clinical care | Triage Nurse / Doctor |
| `pending_registration` | Clinical-First: triage done, registration pending | Triage Nurse (Clinical-First) |
| `awaiting_reconciliation` | Emergency Bypass: treatment started, registration pending | ER Doctor/Nurse |
| `completed` | Visit finished | Doctor / System |
| `cancelled` | Visit cancelled | Any authorized user |
| `no_show` | Patient did not attend | System / Clerk |

### Valid Status Transitions

```
scheduled ──────────→ checked_in ──────────→ in_triage ──────────→ in_progress ──────────→ completed
    │                     │                      │                      │
    │                     │                      │                      ↓
    │                     │                      │                  cancelled
    │                     │                      │
    │                     │                      └──→ pending_registration ──→ in_progress
    │                     │
    │                     └──→ in_progress ──→ completed
    │
    └──→ cancelled

Emergency Bypass:
    checked_in (is_emergency_bypass=True) ──→ awaiting_reconciliation ──→ in_triage/in_progress
```

### Patient Flags

| Flag | Meaning |
|------|---------|
| `is_temporary=True` | Emergency Bypass patient — has TEMP-ER token, no MRN yet |
| `is_temporary=False` + `mrn` set | Fully registered patient |
| `is_emergency_bypass=True` on Visit | Visit created via Emergency Bypass |

---

## 11. API Quick Reference

### Patient Registration
```
POST /api/patients/                    — Register new patient (returns MRN)
POST /api/patients/walk-in/            — Register + create visit simultaneously
GET  /api/patients/?search=query       — Search patients
```

### Triage
```
POST /api/clinical/visits/{id}/triage/submit/  — Submit triage (Standard)
POST /api/clinical/triage-first/               — Clinical-First triage (Anonymous)
POST /api/clinical/triage-first/complete-registration/  — Complete registration for Clinical-First
GET  /api/clinical/triage-queue/               — View triage queue
```

### Emergency Bypass
```
POST /api/clinical/emergency-bypass/           — Original bypass (creates temp patient)
POST /api/clinical/instant-er-bypass/          — Instant ER bypass (with temporary token)
POST /api/clinical/emergency-reconcile/        — Reconcile bypass patient
```

### Clinical
```
POST /api/clinical/visits/{id}/encounters/     — Create encounter
POST /api/clinical/visits/{id}/place-order/    — Place lab/radiology order
POST /api/clinical/visits/{id}/status/         — Transition visit status
```

### Inter-Departmental Transfers
```
POST /api/clinical/visits/{id}/transfer/       — Transfer to any department
POST /api/clinical/visits/{id}/escalate-to-er/ — One-click escalate to ER
POST /api/clinical/visits/{id}/admit-to-ipd/   — Direct admission to IPD
```

### Admissions
```
POST /api/clinical/admissions/                         — Create admission
POST /api/clinical/admissions/{id}/discharge/          — Discharge patient
POST /api/clinical/admissions/{id}/transfers/          — Bed-to-bed transfer
```

### Billing
```
POST /api/billing/pay/                                — Process payment
GET  /api/billing/invoices/{id}/                      — View invoice
```

### Inventory
```
POST /api/inventory/stock/receive/                    — Receive stock
POST /api/inventory/stock/issue/                      — Issue stock
POST /api/inventory/stock/transfer/                   — Transfer stock
```

### Reports
```
GET /api/reports/hmis/                                — HMIS summary
GET /api/reports/daily-revenue/                       — Daily revenue
GET /api/pharmacy/reports/dispensing-summary/         — Dispensing summary
```

---

## Document Control

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Aug 2026 | Initial SOPs |
| 2.0 | Sep 2026 | Added: Dynamic State Machine, Three Pathways, Triage Engine, Inter-Dept Transfers, Clinical-First Flow, Emergency Bypass Enhancement |

**Prepared by:** JFD HMS Development Team
**Approved by:** Medical Director, Jackson F. Doe Memorial Regional Referral Hospital
