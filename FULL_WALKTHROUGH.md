# JFD Hospital HMS — Full Walkthrough Guide
## All Patient Pathways — Step by Step

**Server:** http://127.0.0.1:8000
**Date:** September 2026
**Database:** Fresh pilot reset (empty clinical data, users preserved)
**Version:** 7.0 — SOP sidebar order, role-based visibility, webcam capture, document upload, patient profile

---

## Login Credentials

| Role | URL | Username | Password |
|------|-----|----------|----------|
| Admin | `/login/` | `admin` | `admin123` |
| Registration Clerk | `/login/` | `admin` | `admin123` |
| Triage Nurse | `/login/` | `triage` | `triage123` |
| ER Doctor | `/login/` | `doctor` | `doctor123` |
| OPD Doctor | `/login/` | `doctor` | `doctor123` |
| IPD Doctor | `/login/` | `doctor` | `doctor123` |
| Pharmacist | `/login/` | `pharmacist` | `pharm123` |
| Cashier | `/login/` | `cashier` | `cash123` |
| Surgeon | `/login/` | `surgeon` | `surg123` |

---

## Sidebar Navigation Order (SOP Workflow)

The sidebar follows the SOP workflow order. Each role only sees links relevant to them:

| # | Link | Visible To |
|---|------|-----------|
| 1 | Dashboard | All |
| 2 | **Triage** | Triage Nurse, Doctor, Nurse |
| 3 | **Triage Queue** | Triage Nurse, Nurse |
| 4 | **Register Patient** | MRO, Admin |
| 5 | Search Patients | All clinical staff |
| 6 | **OPD Consultation** | Doctor, Nurse |
| 7 | **Nurse Notes** | Doctor, Nurse |
| 8 | **IPD / Beds** | Doctor, Nurse |
| 9 | **Emergency Room** | Doctor, Nurse, Triage Nurse |
| 10 | **ER Nurse Evaluation** | Doctor, Nurse |
| 11 | **Pediatric Assessment** | Doctor, Nurse |
| 12 | **OBGYN** | Doctor, Nurse |
| 13 | **Surgery** | Doctor, Nurse |
| 14 | **Diagnostics** | Lab Tech, Doctor |
| 15 | **Pharmacy** | Pharmacist |
| 16 | **Billing / Cashier** | Cashier |
| 17 | **Inventory** | Inventory Manager |
| 18 | **Reports / HMIS** | Admin, Medical Director |
| 19 | **Appointments** | Doctor, Nurse, MRO |
| 20 | **Follow-Up Queue** | Doctor, Nurse |
| -- | **Administration** | Admin only |

**Role-based visibility:** A triage nurse only sees Triage + Triage Queue. A pharmacist only sees Pharmacy. A cashier only sees Billing. This keeps the sidebar clean and focused.

---

# PATHWAY A: STANDARD FLOW
## Patient #1: "James Standard"
### Registration → Triage → OPD → Treatment → Discharge

---

### STEP 1: Register Patient (Registration Clerk)
**Login as:** `admin` / `admin123`
**Go to:** `http://127.0.0.1:8000/patients/register/`

| Field | Value |
|-------|-------|
| First Name | James |
| Last Name | Standard |
| Date of Birth | 1985-06-15 |
| Gender | Male |
| Phone | +231-77-123-4567 |
| Payer Category | Self Pay |

**Visit Type Options:** OPD, Emergency, Pediatric, OBGYN, Surgery

### Documents & Photos (Optional)
Scroll down to the **"Documents & Photos"** section:

| Feature | How to Use |
|---------|-----------|
| **Webcam Capture** | Click "Open Camera" → live video feed appears → click "Capture" → photo saved |
| **Document Upload** | Drag & drop files into the upload zone, or click to browse. Supports PDF, DOCX, XLSX, JPG, PNG (max 10MB each) |
| **Multiple Files** | Upload as many documents as needed — they appear in a file list with remove buttons |

**Click:** "Register Patient & Send to Queue"

**✅ EXPECTED RESULT:**
- Success message: "Patient registered successfully"
- **MRN generated:** JFD-2026-XXXXX (write this down!)
- Patient record created in database

**🔍 WHAT HAPPENED:**
- System created Patient record with lifelong MRN
- MRN format: JFD-YYYY-XXXXX (auto-incrementing)

---

### STEP 2: Create Visit (System / Clerk)
**Still on:** Patient registration page OR go to patient record

**If walk-in registration was used**, a Visit is already created with status `checked_in`.

**Otherwise:** From patient record, click "Create Visit" → Select Visit Type: **OPD**

**✅ EXPECTED RESULT:**
- Visit created with status: `checked_in`
- Visit number generated
- Patient now in Triage Queue

**🔍 WHAT HAPPENED:**
- Visit record linked to Patient
- Status: `checked_in` = patient physically present, waiting for triage

---

### STEP 3: Select Patient in Triage (Triage Nurse)
**Login as:** `triage` / `triage123`
**Go to:** `http://127.0.0.1:8000/clinical/triage/`

**✅ EXPECTED RESULT:**
- **Left panel (Triage Queue):** Shows "James Standard" with visit number and wait time
- **Queue count badge:** Shows "1 Waiting"

**Click on** "James Standard" in the queue

**✅ EXPECTED RESULT:**
- Right panel populates with patient info
- Patient name, MRN, and visit number displayed
- Chief Complaint field ready for input
- Vital signs fields ready for input
- Acuity level selector visible (Levels 1-5)

---

### STEP 4: Enter Triage Assessment (Triage Nurse)
**Fill in the form:**

| Field | Value |
|-------|-------|
| Chief Complaint | Headache for 3 days, mild fever |
| Temperature | 37.8 |
| Heart Rate | 82 |
| Respiratory Rate | 18 |
| BP Systolic | 128 |
| BP Diastolic | 82 |
| SpO2 | 98 |

**Look at the system suggestion:**
- With these vitals, system should suggest **Acuity Level 3 (Urgent)** → **OPD**
- Why? Temperature slightly elevated (37.8°C), BP normal, SpO2 normal

**Acuity Level:** Keep the suggested Level 3 (or override if you disagree)

### Photo & Documents (Optional)
Scroll down to the **"Photo & Documents"** section in the triage form:

| Feature | How to Use |
|---------|-----------|
| **Webcam Capture** | Click "Open Camera" → live video → "Capture" → photo attached to triage record |
| **Document Upload** | Drag & drop or click to browse. Upload lab results, referral letters, imaging reports, etc. |
| **Supported Types** | PDF, DOCX, XLSX, JPG, PNG — max 10MB each |

**Click:** "Complete Triage & Route Patient"

**✅ EXPECTED RESULT:**
- Success message: "Triage completed! Patient awaiting registration."
- Patient **disappears from Triage Queue**
- Visit status changed to: `in_progress`

**🔍 WHAT HAPPENED:**
- TriageRecord created with all vitals
- Triage Engine evaluated vitals against 12 rules
- Patient department assigned, awaiting clinical assessment
- Visit status: `checked_in` → `in_progress`
- WorkflowTransition logged

---

### STEP 5: Open OPD Consultation (OPD Doctor)
**Login as:** `doctor` / `doctor123`
**Go to:** `http://127.0.0.1:8000/opd/`

**Click:** "Find Active Visits"

**✅ EXPECTED RESULT:**
- Modal shows "James Standard" with visit number, status: in_progress
- Visit type: OPD

**Click on** "James Standard"

**✅ EXPECTED RESULT:**
- **Left panel (Recorded Vitals):** Shows BP, Heart Rate, Temp, SpO2 — all populated from triage!
- **Left panel (Allergies):** "No known allergies"
- **Left panel (Visit History):** Visit details
- **Main area:** SOAP Notes form ready
- **Diagnosis section:** ICD-10 search ready
- **Orders section:** Order form ready
- **Prescriptions section:** Prescription form ready
- **Top-right buttons:** "Escalate to ER" (amber), "Admit to IPD" (blue), "Discharge" (red), "Finalize" (green)

**🔍 IMPORTANT:** The vitals you entered during triage now appear on the OPD cards because the system checks both VitalSigns AND TriageRecord tables.

---

### STEP 6: Complete Consultation (OPD Doctor)
**Write SOAP Notes:**

| Field | Value |
|-------|-------|
| Subjective | Patient reports frontal headache x3 days, mild fever, no vomiting |
| Objective | Temp 37.8°C, BP 128/82, HR 82, mild tenderness on frontal sinus |
| Assessment | Tension-type headache with low-grade fever |
| Plan | 1. Paracetamol 500mg TDS x5 days 2. Rest 3. Follow up if no improvement |

**Add Diagnosis:**
- Search ICD-10: "R51" (Headache)
- Click on the diagnosis to add it

**Place Order:**
- Click "+ Add Order Item"
- Select: **CBC** (Complete Blood Count)
- Click "Add"

**Write Prescription:**
- Click "+ Add Prescription"
- Search medication: "Paracetamol"
- Select: Paracetamol 500mg
- Quantity: 15 (5 days x 3 times/day)
- Duration: 5 days

**Click:** "Finalize Encounter"

**✅ EXPECTED RESULT:**
- Success message: "Encounter saved successfully"
- Orders auto-posted to billing (invoice created)
- Encounter status: completed

**🔍 WHAT HAPPENED:**
- Encounter record saved with SOAP notes
- Diagnosis recorded (ICD-10: R51)
- Lab order created → Invoice line item auto-created
- Prescription created with items
- Invoice total updated
---

### STEP 7: Dispense Medication (Pharmacist)
**Login as:** `pharmacist` / `pharm123`
**Go to:** `http://127.0.0.1:8000/pharmacy/dispensing/`

**✅ EXPECTED RESULT:**
- "James Standard" appears in pending prescriptions list
- Prescription shows: Paracetamol 500mg x 15

**Click on** the prescription

**Click:** "Dispense"

**✅ EXPECTED RESULT:**
- Success message
- Stock deducted from inventory
- Billing auto-posted (if not already)

**🔍 WHAT HAPPENED:**
- MedicationDispensing record created
- Stock quantity decremented
- Invoice updated with pharmacy charges

---

### STEP 8: Process Payment (Cashier)
**Login as:** `cashier` / `cash123`
**Go to:** `http://127.0.0.1:8000/cashier/`

**✅ EXPECTED RESULT:**
- "James Standard" appears in patient list
- Invoice with line items visible

**Click on** patient/invoice

**✅ EXPECTED RESULT:**
- Invoice details: Lab (CBC) + Pharmacy (Paracetamol)
- Total amount displayed
- Payment form ready

**Fill in payment:**

| Field | Value |
|-------|-------|
| Amount | Full amount |
| Payment Method | Cash |

**Click:** "Process Payment"

**✅ EXPECTED RESULT:**
- Success message: "Payment processed"
- Receipt generated
- Invoice status: `paid`

**🔍 WHAT HAPPENED:**
- Payment record created
- Invoice status: `pending` → `paid`
- Receipt number generated
- Audit log entry created

---

### STEP 9: Discharge Patient (Doctor)
**Login as:** `doctor` / `doctor123`
**Go to:** `http://127.0.0.1:8000/opd/`
**Find:** "James Standard"

**Click:** "Discharge Patient" (red button)

**Fill in:**

| Field | Value |
|-------|-------|
| Discharge Type | Routine |
| Discharge Notes | Headache resolved. Medications dispensed. Follow up if no improvement in 5 days. |

**Click:** "Confirm Discharge"

**✅ EXPECTED RESULT:**
- Success message: "Patient discharged"
- Visit status: `completed`
- Patient no longer in active visits list

**🔍 WHAT HAPPENED:**
- Visit status: `in_progress` → `completed`
- Patient can now be registered for a new visit anytime
- All records preserved in history

---

### STEP 10: Verify Patient Record
**Go to:** `http://127.0.0.1:8000/patients/`
**Search:** "James Standard"

**✅ EXPECTED RESULT:**
- Patient found with MRN: JFD-2026-XXXXX
- Click to see full record:
  - 1 visit (completed)
  - Triage record with vitals
  - Encounter with SOAP notes
  - Diagnosis: R51 (Headache)
  - Orders: CBC
  - Prescription: Paracetamol
  - Invoice: paid
  - Discharge completed

---

# PATHWAY B: CLINICAL-FIRST FLOW
## Patient #2: "Mary Clinical"
### Triage (Anonymous) → Treatment → Registration (Retroactive)

---

### STEP 11: Clinical-First Triage (Triage Nurse)
**Login as:** `triage` / `triage123`
**Go to:** `http://127.0.0.1:8000/clinical/triage/`

**Triage Queue is EMPTY** (no registered patients waiting)

**Click:** "+ Clinical-First Triage" button (top-right of queue header)

**✅ EXPECTED RESULT:**
- Modal opens with amber warning:
  "Clinical-First Triage: Perform triage assessment before patient registration..."
- Chief Complaint field ready
- Vital signs fields ready
- Acuity level selector ready

**Fill in the form:**

| Field | Value |
|-------|-------|
| Chief Complaint | Severe abdominal pain, started this morning |
| Temperature | 38.5 |
| Heart Rate | 105 |
| Respiratory Rate | 22 |
| BP Systolic | 110 |
| BP Diastolic | 70 |
| SpO2 | 97 |
| Acuity Level | Level 2 (Emergent) |

**Click:** "Submit Triage"

**✅ EXPECTED RESULT:**
- Success toast: "Clinical-First Triage submitted! Visit: XXX (pending registration)"
- **Write down the Visit Number!**
- Triage Queue remains empty (no registered patient added)

**🔍 WHAT HAPPENED:**
- Anonymous Visit created (no Patient linked yet)
- Visit status: `pending_registration`
- TriageRecord created with vitals
- System suggested: Acuity 2 → ER (due to elevated HR, low BP)
- You can override to OPD if clinician judgment says so

---

### STEP 12: Complete Registration (Registration Clerk)
**Login as:** `admin` / `admin123`
**Go to:** `http://127.0.0.1:8000/patients/`

**✅ EXPECTED RESULT:**
- **Yellow alert banner at top:** "1 patient(s) awaiting registration"
- Subtitle: "These patients were triaged via Clinical-First and need formal registration."
- Shows: "Severe abdominal pain, started this morning" | Visit: XXX | Acuity: Level 2 | ER
- "Complete Registration" button visible

**Click:** "Complete Registration" (blue button in yellow alert)

**✅ EXPECTED RESULT:**
- Modal opens: "Complete Clinical-First Registration"
- Blue info banner explains this links anonymous triage to real patient

**Fill in demographics:**
| Field | Value |
|-------|-------|
| First Name | Mary |
| Last Name | Clinical |
| Date of Birth | 1992-03-20 |
| Gender | Female |
| Phone | +231-77-987-6543 |
| Payer Category | NHSLA |

**Click:** "Register Patient"

**✅ EXPECTED RESULT:**
- Success message: "Patient registered! MRN generated and clinical records linked."
- Yellow alert disappears (0 pending registrations)
- Patient "Mary Clinical" now in patient list with MRN

**🔍 WHAT HAPPENED:**
- Patient record created with MRN
- Visit linked to this Patient
- Visit status: `pending_registration` → `in_progress`
- All triage records linked to this Patient
- Patient can now be seen by doctor

---

### STEP 13: Continue Clinical Care (Doctor)
**Login as:** `doctor` / `doctor123`
**Go to:** `http://127.0.0.1:8000/opd/` or ER depending on routing

**Find:** "Mary Clinical" in active visits

**Click to open consultation**

**✅ EXPECTED RESULT:**
- **Left panel shows triage vitals** (from anonymous triage):
  - BP: 110/70 mmHg
  - Heart Rate: 105 BPM
  - Temp: 38.5°C
  - SpO2: 97%
- Chief Complaint: "Severe abdominal pain, started this morning"
- All clinical records linked and visible

**Complete consultation, discharge, bill** (same as Steps 6-9 above)

---

## NURSE NOTES: WHO SOAP Format (Any Time)

**When:** A nurse needs to document patient care at any point during the visit. This is a flexible activity — not a fixed step in the workflow.

### Access Points (3 ways):
1. **Sidebar:** Click "Nurse Notes" → Search patient → Select visit
2. **OPD Consultation:** Click "Nurse Notes" button in header bar
3. **ER/IPD:** Click "Nurse Notes" link on active visit

### Writing a SOAP Note:

**Go to:** `http://127.0.0.1:8000/clinical/nurse-notes/`

**Search for patient** by name or MRN, select the active visit.

**Fill in SOAP fields (2x2 grid):**

| Field | What to Write | Example |
|-------|--------------|---------|
| **S — Subjective** | Patient's complaints, symptoms | "Patient reports headache for 3 days, mild fever" |
| **O — Objective** | Vitals, exam findings, labs | "Temp 37.8°C, HR 82, BP 128/82, SpO2 98%" |
| **A — Assessment** | Your clinical judgment | "Viral headache, no red flags" |
| **P — Plan** | Interventions, education, follow-up | "Paracetamol 500mg TID, rest, follow-up 3 days" |

**Click:** "Save SOAP Note"

**✅ EXPECTED RESULT:**
- Note saved with timestamp and author
- Appears in Notes History below
- Linked to patient's visit and encounter

---

# PATHWAY C: EMERGENCY BYPASS FLOW
## Patient #3: "Robert Emergency"
### Instant ER Entry → Treatment → Retroactive Registration

---

### STEP 14: Activate Emergency Bypass (ER Doctor)
**Login as:** `doctor` / `doctor123`
**Go to:** `http://127.0.0.1:8000/clinical/emergency/`

**✅ EXPECTED RESULT:**
- ER Dashboard loads with stats cards:
  - Active ER Cases: 0
  - Awaiting Disposition: 0
  - Discharged Today: 0
  - Admitted from ER: 0
- Active ER Cases table: "No active ER cases"
- **Red "INSTANT ER BYPASS" button** visible (flashing animation) in header

**Click:** "INSTANT ER BYPASS" (red flashing button)

**✅ EXPECTED RESULT:**
- Modal opens with **red warning banner:**
  "CRITICAL EMERGENCY: This creates a temporary patient record (no registration needed). Begin treatment immediately..."
- Fields: Patient Name, Chief Complaint, Emergency Reason

**Fill in:**

| Field | Value |
|-------|-------|
| Patient Name | Robert Emergency (or UNKNOWN PATIENT if not identified) |
| Chief Complaint | Chest pain, difficulty breathing, collapsed at home |
| Emergency Reason | Suspected myocardial infarction |

**Click:** "ACTIVATE BYPASS" (red button)

**✅ EXPECTED RESULT:**
- Success toast (8 seconds): "BYPASS ACTIVATED — Temp Token: TEMP-ER-YYYY-XXXXX — Begin treatment NOW!"
- **WRITE DOWN THE TEMP TOKEN!**
- Dashboard refreshes
- Patient appears in "Active ER Cases" table with:
  - **Red TEMP badge** showing temp token (not MRN)
  - Status: checked_in
  - Chief Complaint displayed

**🔍 WHAT HAPPENED:**
- Temporary Patient created (is_temporary=True, no MRN)
- Visit created with status: `checked_in`
- Patient flagged as emergency bypass
- Zero administrative barriers

---

### STEP 15: Begin Emergency Treatment (ER Doctor)
**Still on ER Dashboard**

**✅ EXPECTED RESULT:**
- Patient "Robert Emergency" in Active ER Cases
- Red TEMP badge with token visible
- Action buttons: "Fill Evaluation", "Log Intervention" (disabled), "Process Disposition" (disabled)

**Click:** "Fill Evaluation" (green button)

**✅ EXPECTED RESULT:**
- ER Nurse Evaluation form opens
- Fields: HPI, PMH, ROS, Physical Exam, Interventions

**Fill in evaluation:**

| Section | Value |
|---------|-------|
| HPI | 58yo male, sudden onset crushing chest pain radiating to left arm, diaphoresis, dyspnea. Collapsed at home. |
| PMH | Hypertension, Type 2 Diabetes |
| ROS | Chest pain 9/10, SOB, nausea, dizziness |
| Physical Exam | Diaphoretic, BP 90/60, HR 110, SpO2 91% on room air |
| Interventions | IV access established, O2 4L via nasal cannula, Aspirin 325mg PO, Nitroglycerin SL |

**Click:** "Save Evaluation"

**✅ EXPECTED RESULT:**
- Success message
- "Fill Evaluation" button changes to "Eval Done" (green badge)
- "Log Intervention" button now **enabled**

---

### STEP 16: Log Additional Interventions (ER Doctor)
**Click:** "Log Intervention" (red button)

**Fill in:**

| Field | Value |
|-------|-------|
| Intervention Description | 12-lead ECG obtained — ST elevation in leads II, III, aVF. Started heparin drip. |
| Vitals (optional) | BP: 88/58, HR: 108, Temp: 36.8, SpO2: 93% |

**Click:** "Save Intervention"

**✅ EXPECTED RESULT:**
- Success message
- Intervention logged

**Repeat:** Log more interventions as needed (medications, procedures, etc.)

---

### STEP 17: Process Disposition — Admit to IPD (ER Doctor)
**Click:** "Process Disposition" (blue button — now enabled)

**✅ EXPECTED RESULT:**
- Modal opens with disposition options

**Fill in:**

| Field | Value |
|-------|-------|
| Disposition | Admit to IPD |
| Diagnosis / Notes | Acute ST-elevation MI. Needs cardiac monitoring and intervention. |

**Click:** "Process Disposition"

**✅ EXPECTED RESULT:**
- Success message: "Patient admitted to IPD. Assign a bed from the IPD dashboard."
- Visit status: `completed` (ER visit done)
- Admission record created
- Patient disappears from ER Active Cases
- Admitted from ER count: 1

**🔍 WHAT HAPPENED:**
- Admission record created (status: active)
- Visit completed
- Patient now needs a bed assigned in IPD

---

### STEP 18: Assign Bed in IPD (IPD Doctor)
**Login as:** `doctor` / `doctor123`
**Go to:** `http://127.0.0.1:8000/clinical/ipd/`

**✅ EXPECTED RESULT:**
- Bed Matrix shows available beds (green) and occupied beds (red)
- Admission Queue shows "Robert Emergency" waiting for bed assignment

**Click on an available bed** (green) — e.g., "Bed 1A" in Medical Ward

**Fill in:**

| Field | Value |
|-------|-------|
| Admitting Diagnosis | Acute STEMI, post-ER stabilization |
| Expected Discharge | (leave blank or estimate) |

**Click:** "Confirm"

**✅ EXPECTED RESULT:**
- Bed status changes to OCCUPIED (red)
- Patient name shown on bed
- Admission linked to bed

---

### STEP 19: Reconcile Emergency Patient (Registration Clerk)
**Login as:** `admin` / `admin123`
**Go to:** `http://127.0.0.1:8000/clinical/emergency/`

**✅ EXPECTED RESULT:**
- ER Dashboard shows the patient with **Red TEMP badge**
- "Complete Registration" button visible next to TEMP badge

**Click:** "Complete Registration" (amber button)

**✅ EXPECTED RESULT:**
- Modal opens: "Complete Emergency Patient Registration"
- Amber warning: "Reconcile Patient: Complete formal registration for emergency bypass patient..."
- Fields: First Name, Last Name, DOB, Gender, Phone, Payer Category

**Fill in:**

| Field | Value |
|-------|-------|
| First Name | Robert |
| Last Name | Emergency |
| Date of Birth | 1968-11-05 |
| Gender | Male |
| Phone | +231-77-456-7890 |
| Payer Category | NHSLA |

**Click:** "Reconcile & Register"

**✅ EXPECTED RESULT:**
- Success message: "Patient reconciled! MRN generated and clinical records linked."
- TEMP badge disappears from ER dashboard
- Patient now has permanent MRN
- All ER records (evaluation, interventions, vitals, orders) linked to this patient

**🔍 WHAT HAPPENED:**
- Patient record created with MRN
- is_temporary: False
- All clinical records (encounters, orders, vitals) linked
- Admission linked to permanent patient
- Visit status updated

---

### STEP 20: Verify Complete Record
**Go to:** `http://127.0.0.1:8000/patients/`
**Search:** "Robert Emergency"

**Click on** patient to see full record

**✅ EXPECTED RESULT:**
- MRN: JFD-2026-XXXXX
- 1 visit (completed — ER)
- 1 admission (active — IPD, Bed 1A)
- ER Evaluation with full notes
- Interventions logged
- Vitals recorded
- Admission diagnosis

---
### STEP 21: IPD Treatment & Discharge (IPD Doctor)
**Go to:** `http://127.0.0.1:8000/clinical/ipd/`
**Find:** Bed 1A (Robert Emergency)

**Complete IPD care** (encounters, orders, etc.)

**Click:** "Discharge" on the bed

**Fill in:**

| Field | Value |
|-------|-------|
| Discharge Type | Routine |
| Discharge Summary | Patient stabilized. Troponin trending down. Medications adjusted. Follow up cardiology in 2 weeks. |

**Click:** "Confirm Discharge"

**✅ EXPECTED RESULT:**
- Bed freed (green)
- Admission status: `completed`
- Visit completed
- Patient discharged from hospital

---

# VERIFICATION CHECKLIST

After completing all 21 steps, verify:

| # | Check | Expected |
|---|-------|----------|
| 1 | James Standard has MRN | JFD-2026-XXXXX |
| 2 | James Standard has 1 completed visit | status: completed |
| 3 | James Standard has triage record with vitals | All vitals populated |
| 4 | James Standard has encounter with SOAP notes | Full consultation |
| 5 | James Standard has diagnosis | R51 (Headache) |
| 6 | James Standard has prescription | Paracetamol dispensed |
| 7 | James Standard has paid invoice | status: paid |
| 8 | Mary Clinical has MRN | JFD-2026-XXXXX |
| 9 | Mary Clinical has 1 completed visit | status: completed |
| 10 | Mary Clinical triage records linked | Vitals visible on OPD |
| 11 | Robert Emergency has MRN | JFD-2026-XXXXX |
| 12 | Robert Emergency has ER evaluation | Full clinical notes |
| 13 | Robert Emergency was admitted to IPD | Admission record exists |
| 14 | Robert Emergency was discharged | Bed freed, visit completed |
| 15 | All 3 patients in patient list | Search finds all |
| 16 | No TEMP patients remain | is_temporary=False for all |

---

# QUICK REFERENCE: SIDEBAR NAVIGATION

Sidebar order follows the SOP workflow. Each role only sees their relevant links:

| Order | Link | Role Gate |
|-------|------|-----------|
| 1 | Dashboard | All |
| 2 | Triage | Triage Nurse, Doctor, Nurse |
| 3 | Triage Queue | Triage Nurse, Nurse |
| 4 | Register Patient | MRO, Admin |
| 5 | Search Patients | All clinical |
| 6 | OPD Consultation | Doctor, Nurse |
| 7 | Nurse Notes | Doctor, Nurse |
| 8 | IPD / Beds | Doctor, Nurse |
| 9 | Emergency Room | Doctor, Nurse, Triage Nurse |
| 10 | ER Nurse Evaluation | Doctor, Nurse |
| 11 | Pediatric Assessment | Doctor, Nurse |
| 12 | OBGYN | Doctor, Nurse |
| 13 | Surgery | Doctor, Nurse |
| 14 | Diagnostics | Lab Tech, Doctor |
| 15 | Pharmacy | Pharmacist |
| 16 | Billing / Cashier | Cashier |
| 17 | Inventory | Inventory Manager |
| 18 | Reports / HMIS | Admin, Medical Director |
| 19 | Appointments | Doctor, Nurse, MRO |
| 20 | Follow-Up Queue | Doctor, Nurse |
| -- | Administration | Admin only |

---

# QUICK REFERENCE: WHAT EACH BUTTON DOES

## ER Dashboard
| Button | When | What Happens |
|--------|------|-------------|
| **INSTANT ER BYPASS** | Critical emergency | Creates temp patient, skips registration |
| **Fill Evaluation** | After bypass | Opens ER assessment form |
| **Log Intervention** | After evaluation | Records treatment/procedure |
| **Process Disposition** | After evaluation + intervention | Admit, discharge, or transfer |
| **Complete Registration** | On TEMP badge patient | Reconciles to permanent patient |

## OPD Consultation
| Button | When | What Happens |
|--------|------|-------------|
| **Escalate to ER** | Patient crashing | Transfers visit to ER |
| **Admit to IPD** | Needs hospitalization | Creates admission record |
| **Discharge Patient** | Ready to go home | Completes visit |
| **Finalize Encounter** | After SOAP + orders | Saves all clinical data |

## Triage Page
| Button | When | What Happens |
|--------|------|-------------|
| **Clinical-First Triage** | No registered patient | Anonymous triage before registration |
| **Complete Triage & Route** | After entering vitals | Routes patient to department |

## Patient Search
| Button | When | What Happens |
|--------|------|-------------|
| **Complete Registration** (yellow alert) | Clinical-First pending | Links anonymous triage to real patient |

---

# WHAT TO EXPECT AT EACH STAGE

| Stage | Who | What You See | What You Do |
|-------|-----|-------------|-------------|
| Registration | Clerk | Empty form | Enter demographics → Get MRN |
| Triage Queue | Triage Nurse | Patient cards with wait time | Select patient → Enter vitals |
| Triage Form | Triage Nurse | Vitals form + acuity selector | Enter vitals → System suggests → Submit |
| OPD Queue | Doctor | Active visits list | Select patient → See vitals + SOAP |
| Consultation | Doctor | SOAP form + orders + rx | Write notes → Orders → Prescribe |
| Pharmacy | Pharmacist | Pending prescriptions | Verify → Dispense |
| Cashier | Cashier | Invoice with line items | Process payment → Receipt |
| Discharge | Doctor | Discharge form | Select type → Notes → Confirm |
| ER Dashboard | ER Doctor | Active cases table | Bypass → Evaluate → Disposition |
| IPD Dashboard | IPD Doctor | Bed matrix | Assign bed → Transfer → Discharge |

---

# TROUBLESHOOTING

| Problem | Cause | Solution |
|---------|-------|----------|
| Vitals show "-" on OPD | No vitals recorded yet | Record via "+ Record" button or ensure triage was done |
| Can't find patient in queue | Wrong status | Check visit status is `checked_in` or `in_progress` |
| "INSTANT ER BYPASS" not visible | Wrong page | Go to `/clinical/emergency/` not `/er/` |
| Yellow alert not showing | No pending registrations | Clinical-First triage must be done first |
| Can't dispense | Invoice not paid | Process payment first at cashier |
| Bed won't assign | Bed occupied | Select green (available) bed |

---

# PATHWAY D: SPECIALTY MODULES (Demo Data Pre-Seeded)
## Surgery, OBGYN, Pediatric, Lab, Maternity, Admin

**Setup:** Run the following before the demo:
```bash
start_pilot.bat
```
Then login as `admin` / `admin123`.

**Pre-seeded data:** The `seed_demo_modules` command creates:
- 3 SurgicalCases (Surgery)
- 2 AntenatalVisits, 1 LaborRecord, 1 DeliveryRecord, 1 BirthRecord, 1 PostnatalVisit (OBGYN)
- 2 Pediatric patients (ages 3, 7) with visits and assessments
- 3 Specimens, 2 DiagnosticResults (Lab)

---

# MODULE 1: SURGERY
## Viewing Pre-Seeded Surgical Cases

### STEP 22: Open Surgery Dashboard
**Login as:** `admin` / `admin123`
**Go to:** `http://127.0.0.1:8000/surgery/`

**✅ EXPECTED RESULT:**
- Surgery Dashboard loads with stats cards:
  - Scheduled: 1
  - In Progress: 1
  - Completed: 1
- Table shows 3 surgical cases

### STEP 23: Review a Scheduled Case
**Click** on "Laparoscopic Cholecystectomy" (scheduled case)

**✅ EXPECTED RESULT:**
- Patient name displayed
- Procedure: Laparoscopic Cholecystectomy
- Surgeon: Dr. James Sherman
- Scheduled date: tomorrow
- Status: Scheduled
- Pre-op diagnosis: Symptomatic gallstones

### STEP 24: Start a Case (Change Status)
**Click** on "Appendectomy" (in_progress case)

**✅ EXPECTED RESULT:**
- Status: In Progress
- Procedure: Appendectomy
- Surgeon: Dr. James Sherman

### STEP 25: View Completed Case
**Click** on "Cesarean Section" (completed case)

**✅ EXPECTED RESULT:**
- Status: Completed
- Procedure: Cesarean Section
- Notes visible

---

# MODULE 2: OBGYN
## Antenatal, Labor, Delivery, Postnatal Records

### STEP 26: Open OBGYN Dashboard
**Go to:** `http://127.0.0.1:8000/obgyn/`

**✅ EXPECTED RESULT:**
- OBGYN Dashboard loads with stats cards:
  - ANC Visits: 2
  - Active Labor: 1
  - Deliveries: 1
  - Postnatal: 1
- Tabs: ANC Visits | Labor & Delivery | Postnatal | New ANC Visit

### STEP 27: View ANC Visits
**Click** the "ANC Visits" tab

**✅ EXPECTED RESULT:**
- Table shows 2 antenatal visits
- Fields: Patient, Gestational Age, BP, Weight, Hemoglobin,下次_visit

### STEP 28: Create New ANC Visit
**Click** the "+ New ANC Visit" tab

**Fill in:**
| Field | Value |
|-------|-------|
| Patient | Select from dropdown |
| Gestational Weeks | 28 |
| BP Systolic | 118 |
| BP Diastolic | 76 |
| Weight (kg) | 68 |
| Hemoglobin | 11.2 |
| Fundal Height | 26 cm |
| Fetal Heart Rate | 140 |
| Urine Protein | Negative |
| Notes | Normal ANC visit |

**Click:** "Save ANC Visit"

**✅ EXPECTED RESULT:**
- Success message
- New visit appears in ANC list
- ANC count updated

### STEP 29: View Labor & Delivery
**Click** the "Labor & Delivery" tab

**✅ EXPECTED RESULT:**
- Table shows 1 labor record
- Fields: Patient, Gestational Age, Status, Cervical Dilation, Fetal Heart Rate

### STEP 30: Create Delivery Record
**Click** on a labor record → "Record Delivery"

**Fill in:**
| Field | Value |
|-------|-------|
| Delivery Method | Normal Vaginal Delivery |
| Blood Loss (mL) | 350 |
| Complications | None |
| Placenta Expelled | Yes |
| Notes | Uncomplicated delivery |

**Click:** "Save Delivery"

**✅ EXPECTED RESULT:**
- Success message
- Delivery record created

### STEP 31: Record Birth
**Click** on a delivery record → "Record Birth"

**Fill in:**
| Field | Value |
|-------|-------|
| Baby Name | Baby Girl Toe |
| Sex | Female |
| Birth Weight (g) | 3100 |
| Birth Length (cm) | 49 |
| Apgar 1min | 9 |
| Apgar 5min | 10 |
| Cry at Birth | Yes |
| Feeding Method | Breastfeeding |
| Vitamin K Given | Yes |
| Eye Prophylaxis | Yes |
| Hepatitis B Vaccine | Yes |
| Status | Alive |

**Click:** "Save Birth Record"

**✅ EXPECTED RESULT:**
- Success message
- Birth record created with auto-generated birth number

### STEP 32: View Postnatal Visits
**Click** the "Postnatal" tab

**✅ EXPECTED RESULT:**
- Table shows 1 postnatal visit
- Fields: Patient, Day Postpartum, BP, Temperature, Fundal Height, Baby Weight, Feeding Method

---

# MODULE 3: PEDIATRIC
## Child Health Assessments

### STEP 33: Open Pediatric Dashboard
**Go to:** `http://127.0.0.1:8000/pediatric/`

**✅ EXPECTED RESULT:**
- Pediatric Dashboard loads
- Table shows 2 pediatric patients

### STEP 34: View Pediatric Assessment
**Click** on "David Patient" (age 3)

**✅ EXPECTED RESULT:**
- Patient info: Age 3, Male
- Assessment form with:
  - Child Problem
  - Danger Signs (dyspnea, severe dehydration, vomiting, convulsions, etc.)
  - Vitals (temperature, heart rate, respiratory rate, SpO2, weight)
  - Clinical Assessment
  - Diagnosis
  - Treatment Plan

---

# MODULE 4: LABORATORY
## Specimens and Diagnostic Results

### STEP 35: Open Lab Dashboard
**Go to:** `http://127.0.0.1:8000/lab/`

**✅ EXPECTED RESULT:**
- Lab Dashboard loads with stats:
  - Total Orders: 3
  - Pending Results: 1
  - Completed Today: 2

### STEP 36: View Specimens
**Click** on a specimen

**✅ EXPECTED RESULT:**
- Specimen details:
  - Specimen ID
  - Type: Blood / Urine / Stool
  - Collection date/time
  - Collected by
  - Status: pending / received / completed

### STEP 37: View Diagnostic Results
**Click** on a completed result

**✅ EXPECTED RESULT:**
- Result text visible (e.g., CBC or Malaria test)
- Status: verified
- Abnormal flag if applicable

---

# MODULE 5: MATERNITY
## Uses OBGYN Records

**Note:** Maternity is the same as OBGYN — use the same dashboard at `/obgyn/`.

The **Maternity Ward** (code: MAT1) is linked to the OBGYN department. When creating an ANC record, you can optionally assign a bed in the Maternity Ward. The ward occupancy panel at the top of the OBGYN dashboard shows all Maternity Ward beds (free/occupied).

---

# PATHWAY E: SURGERY REGISTRATION FLOW (WHO-Compliant)
## Register → Surgery Dashboard → Schedule Case → Ward Bed (Optional)

**WHO Standard:** Patients enter through ONE registration entry. Visit type is selected at registration. Ward assignment is a clinical decision made by the surgeon, not at registration.

### STEP 43: Register Surgical Patient
**Login as:** `admin` / `admin123`
**Go to:** `http://127.0.0.1:8000/patients/register/`

| Field | Value |
|-------|-------|
| First Name | Sarah |
| Last Name | Surgical |
| Date of Birth | 1990-03-20 |
| Gender | Female |
| Phone | +231-77-987-6543 |
| Visit Type | **Surgery** |
| Chief Complaint | Abdominal pain, suspected appendicitis |
| Payer Category | Insurance |

**Click:** "Register Patient & Send to Queue"

**✅ EXPECTED RESULT:**
- Patient registered with MRN
- Visit created with `visit_type='surgery'`
- Patient in checked-in status

### STEP 44: Open Surgery Dashboard
**Go to:** `http://127.0.0.1:8000/surgery/`

**✅ EXPECTED RESULT:**
- Stats cards: Scheduled, In Progress, Completed, Cancelled
- **Surgical Ward Beds panel** at top showing bed occupancy:
  - Green beds = free
  - Red beds = occupied
  - Summary: "X free / Y occupied / Z total"
- Theatre Schedule list below

### STEP 45: Schedule Surgical Case
**Click:** "+ Schedule Case"

| Field | Value |
|-------|-------|
| Patient | Sarah Surgical (search by name/MRN) |
| Procedure | Appendectomy |
| Surgical Site | Right Lower Quadrant |
| Laterality | Right |
| Priority | Urgent |
| Surgeon | Select from dropdown |
| Anesthesia | General |
| Pre-op Diagnosis | Acute appendicitis |

**Optional — Ward Bed Assignment:**
- If the patient needs pre-op admission, select a **green (free) bed** from the Surgical Ward Beds panel
- The system auto-creates an Admission record linked to Surgical Ward 1

**Click:** "Save Case"

**✅ EXPECTED RESULT:**
- Case created with number SG-YYYYMMDD-XXXX
- Status: Scheduled
- If bed selected: Admission created, bed turns red (occupied)

### STEP 46: View Case Detail
**Click** on the case card in the Theatre Schedule

**✅ EXPECTED RESULT:**
- Full case detail modal showing:
  - Case number, MRN, procedure, surgeon, site, laterality
  - Priority, anesthesia, pre/post-op diagnosis
  - Duration, blood loss, complications
  - Action buttons: Start Surgery, Complete, Cancel

---

# PATHWAY F: OBGYN REGISTRATION FLOW (WHO-Compliant)
## Register → OBGYN Dashboard → ANC Visit → Labor → Delivery → Postnatal

**WHO Standard:** ANC visits are outpatient (no bed needed). Ward assignment happens only when the patient is admitted for labor/delivery in the Maternity Ward.

### STEP 47: Register OBGYN Patient
**Login as:** `admin` / `admin123`
**Go to:** `http://127.0.0.1:8000/patients/register/`

| Field | Value |
|-------|-------|
| First Name | Margaret |
| Last Name | Maternity |
| Date of Birth | 1995-07-10 |
| Gender | Female |
| Phone | +231-77-456-7890 |
| Visit Type | **OBGYN** |
| Chief Complaint | 28 weeks pregnant, routine ANC visit |
| Payer Category | Maternal Free Care |

**Click:** "Register Patient & Send to Queue"

**✅ EXPECTED RESULT:**
- Patient registered with MRN
- Visit created with `visit_type='obgyn'`

### STEP 48: Open OBGYN Dashboard
**Go to:** `http://127.0.0.1:8000/obgyn/`

**✅ EXPECTED RESULT:**
- Stats cards: ANC Patients, Active Labor, Deliveries, Postnatal
- **Maternity Ward Beds panel** at top showing bed occupancy
- ANC Register below with "+ New ANC Visit" button

### STEP 49: Create ANC Record
**Click:** "+ New ANC Visit"

| Field | Value |
|-------|-------|
| Patient | Margaret Maternity |
| LMP Date | 2026-01-15 (required — auto-calculates EDD +280 days) |
| EDD Date | Auto-filled: 2026-10-22 |
| Gestational Weeks | Auto-filled from LMP |
| Gravida | 2 |
| Parity | 1 |
| Blood Group | O+ |
| BP Systolic | 110 |
| BP Diastolic | 70 |
| Weight | 68.5 |
| Fetal Heart Rate | 140 |

**No bed assignment** — ANC is outpatient.

**Click:** "Save ANC Visit"

**✅ EXPECTED RESULT:**
- ANC record created with number ANC-YYYYMMDD-XXXX
- Status: active
- Next visit date can be set

### STEP 50: When Labor Begins — Admit to Maternity Ward
**On OBGYN Dashboard:** Click "+ Record Labor"

| Field | Value |
|-------|-------|
| Patient | Margaret Maternity |
| Status | in_progress |
| Cervical Dilation | 4 cm |
| Fetal Heart Rate | 130 |
| Presentation | Cephalic |

**Bed Assignment (optional but recommended):**
- Select a **green (free) bed** from the Maternity Ward Beds panel
- System auto-creates Admission in Maternity Ward

**Click:** "Save Labor Record"

**✅ EXPECTED RESULT:**
- Labor record created
- Maternity Ward bed turns red (occupied)

### STEP 51: Record Delivery
**Click:** "Save Delivery Outcome" (bottom section)

| Field | Value |
|-------|-------|
| Mode of Delivery | SVD |
| Newborn Sex | Female |
| Birth Weight | 3.20 kg |
| APGAR 1min / 5min | 8 / 9 |

**Click:** "Save Delivery Outcome"

### STEP 52: Record Birth
**Click:** "+ Record Birth"

| Field | Value |
|-------|-------|
| Baby Name | Baby Margaret |
| Sex | Female |
| Weight | 3.20 kg |
| APGAR 1min | 8 |
| APGAR 5min | 9 |
| Feeding | Breastfed |

**Click:** "Save Birth Record"

### STEP 53: Postnatal Visit
**Click:** "+ New Postnatal Visit"

| Field | Value |
|-------|-------|
| Day Postpartum | 1 |
| Temperature | 36.8 |
| Blood Pressure | 120/80 |
| Lochia | Normal |
| Feeding | Breastfeeding |

**Click:** "Save Postnatal Visit"

---

# MODULE 6: ADMIN
## User & Role Management

### STEP 38: Open Admin Dashboard
**Go to:** `http://127.0.0.1:8000/admin/`

**✅ EXPECTED RESULT:**
- Admin Dashboard with navigation:
  - User Management
  - Role Management
  - Department Management
  - Audit Trail
  - Login History
  - Triage Criteria
  - Hospital Settings

### STEP 39: User Management
**Click:** "User Management"

**✅ EXPECTED RESULT:**
- Table shows all users (admin, doctor, nurse, triage, pharmacist, cashier, labtech, obgyn, surgeon)
- Each user shows: name, username, email, role, status
- "Edit" and "Deactivate" buttons

### STEP 40: Role Management
**Click:** "Role Management"

**✅ EXPECTED RESULT:**
- Table shows all 15 roles with their assigned permissions
- "Edit Permissions" button opens permission editor
- Permissions grouped by category

### STEP 41: Triage Criteria
**Click:** "Triage Criteria"

**✅ EXPECTED RESULT:**
- Table shows 12 auto-suggestion rules
- Each rule shows: name, vital sign, operator, threshold, suggested acuity, department
- "Toggle" button to activate/deactivate
- "Delete" button to remove

### STEP 42: Hospital Settings
**Click:** "Hospital Settings"

**✅ EXPECTED RESULT:**
- Form with:
  - Hospital Name: Jackson F. Doe Memorial Regional Referral Hospital
  - Logo upload
  - Contact info (phone, email, address)
- "Save Settings" button

---

# VERIFICATION CHECKLIST (Updated)

After completing all steps, verify:

| # | Check | Expected |
|---|-------|----------|
| 1 | James Standard has MRN | JFD-2026-XXXXX |
| 2 | James Standard has 1 completed visit | status: completed |
| 3 | James Standard has triage record with vitals | All vitals populated |
| 4 | James Standard has encounter with SOAP notes | Full consultation |
| 5 | James Standard has diagnosis | R51 (Headache) |
| 6 | James Standard has prescription | Paracetamol dispensed |
| 7 | James Standard has paid invoice | status: paid |
| 8 | Registration fee auto-charged | Invoice has REG line item ($5) |
| 9 | Mary Clinical has MRN | JFD-2026-XXXXX |
| 10 | Mary Clinical has 1 completed visit | status: completed |
| 11 | Mary Clinical triage records linked | Vitals visible on OPD |
| 12 | Robert Emergency has MRN | JFD-2026-XXXXX |
| 13 | Robert Emergency has ER evaluation | Full clinical notes |
| 14 | Robert Emergency was admitted to IPD | Admission record exists |
| 15 | Robert Emergency was discharged | Bed freed, visit completed |
| 16 | All 3 patients in patient list | Search finds all |
| 17 | No TEMP patients remain | is_temporary=False for all |
| 18 | Surgery: 3 cases visible | Scheduled, In Progress, Completed |
| 19 | OBGYN: 2 ANC visits visible | With vitals and GA |
| 20 | OBGYN: 1 labor record visible | Active labor |
| 21 | OBGYN: 1 delivery record visible | With complications |
| 22 | OBGYN: 1 birth record visible | Baby name, Apgar scores |
| 23 | OBGYN: 1 postnatal visit visible | Day postpartum, vitals |
| 24 | Pediatric: 2 child patients visible | Ages 3 and 7 |
| 25 | Pediatric: 2 assessments visible | With danger signs |
| 26 | Lab: 3 specimens visible | Blood, Urine, Stool |
| 27 | Lab: 2 results visible | CBC, Malaria test |
| 28 | Admin: 9 users visible | All test accounts |
| 29 | Admin: 15 roles visible | With permissions |
| 30 | Admin: 12 triage criteria visible | All active |
| 31 | Admin: Hospital settings saved | Name, logo, contact |
| 32 | Admin: Registration fee configurable | Settings > Financial Settings |
| 33 | Registration form shows 5 visit types | OPD, Emergency, Pediatric, OBGYN, Surgery |
| 34 | Registration form shows photo capture | Camera icon + file upload |
| 35 | Surgery: Ward beds panel visible | Green/red bed indicators |
| 36 | Surgery: Case linked to admission | If bed was selected |
| 37 | OBGYN: Maternity ward beds panel visible | Green/red bed indicators |
| 38 | OBGYN: ANC record created with EDD | Auto-calculated from LMP |
| 39 | OBGYN: Labor record linked to admission | If bed was selected |
| 40 | OBGYN: Delivery + birth records linked | DeliveryRecord → BirthRecord |
| 41 | Triage Queue shows pending registrations | Patients awaiting registration visible |
| 42 | Triage Queue → Complete Registration works | Pre-fills registration form |
| 43 | Follow-Up Queue shows scheduled follow-ups | Inside window + overdue sections |
| 44 | Discharge with Follow-Up works | Creates follow-up appointment |
| 45 | Patient photo shows in EMR drawer | Photo replaces initials avatar |

---

# QUICK REFERENCE: MODULE URLs

| Module | URL | Login Role |
|--------|-----|------------|
| Registration | `/patients/register/` | admin, registration |
| Triage Queue | `/clinical/triage-pending/` | admin, registration, triage |
| Follow-Up Queue | `/clinical/follow-up-queue/` | admin, doctor, nurse |
| Surgery | `/clinical/surgery/` | admin, surgeon, doctor |
| OBGYN | `/clinical/obgyn/` | admin, obgyn, doctor |
| Pediatric | `/clinical/pediatric/` | admin, doctor, nurse |
| Lab | `/clinical/diagnostics/` | admin, labtech |
| Maternity | `/clinical/obgyn/` (same as OBGYN) | admin, obgyn |
| IPD | `/clinical/ipd/` | admin, doctor, nurse |
| Nurse Notes | `/clinical/nurse-notes/` | admin, doctor, nurse |
| Admin | `/admin/` | admin |
| Hospital Settings | `/admin/settings/` | admin (superuser) |

### Visit Types at Registration
| Visit Type | Value | Dashboard |
|---|---|---|
| OPD | `opd` | `/opd/` |
| Emergency | `er` | `/er/` |
| Pediatric | `pediatric` | `/pediatric/` |
| OBGYN | `obgyn` | `/obgyn/` |
| Surgery | `surgery` | `/surgery/` |

### Ward Bed Occupancy
| Ward | Code | Department | Dashboard |
|---|---|---|---|
| Surgical Ward 1 | SURG1 | SURG | `/surgery/` (top panel) |
| Maternity Ward | MAT1 | OBGYN | `/obgyn/` (top panel) |
| Medical Ward 1 | MED1 | IPD | `/ipd/` (bed matrix) |
| Medical Ward 2 | MED2 | IPD | `/ipd/` (bed matrix) |
| ER Resuscitation | ER1 | ER | `/ipd/` (bed matrix) |
| ICU | ICU1 | IPD | `/ipd/` (bed matrix) |

---

# TROUBLESHOOTING (Updated)

| Problem | Solution |
|---------|----------|
| "I can't find the patient" | Search by MRN, name, or phone in Patient Search |
| "Triage won't submit" | Make sure visit status is "checked_in" or "in_triage" |
| "Orders not showing in billing" | Click "Finalize Encounter" first |
| "Can't dispense medication" | Check if patient has paid (invoice status = paid) |
| "Bed won't assign" | Make sure bed is green (available) |
| "Patient shows TEMP badge" | Click "Complete Registration" to reconcile |
| "Surgery page shows no cases" | Run `python manage.py seed_demo_modules` |
| "OBGYN page shows no records" | Run `python manage.py seed_demo_modules` |
| "Pediatric page shows no patients" | Run `python manage.py seed_demo_modules` |
| "Lab page shows no specimens" | Run `python manage.py seed_demo_modules` |
| "No beds showing in ward panel" | Ensure wards are seeded: `python manage.py seed_demo_modules` |
| "Can't select Surgery visit type" | Clear browser cache, refresh. Form now has 5 options |
| "Registration fee not showing" | Go to Admin > Hospital Settings > Financial Settings, set fee amount |
| "Photo not uploading" | Ensure form has `enctype="multipart/form-data"`, check file size < 5MB |
| "Webcam not working" | Check browser camera permissions. Try Chrome/Edge. Use file upload as fallback |
| "Documents not saving" | Ensure form has `enctype="multipart/form-data"`. Files max 10MB each |
| "Can't see patient profile" | Click "Profile" button in patient search results (next to "View EMR") |
| "Sidebar shows wrong links" | Log out and log back in. Sidebar is role-based — each role sees only their links |
| "Triage Queue is empty" | Patients appear here after clinical-first triage. Use "Clinical-First Triage" button on Triage page |
| "Follow-Up Queue shows no patients" | Create follow-up appointments from OPD discharge or nurse notes page |
| "Discharge button not working" | Must have an active visit selected in Nurse Notes page |
| "Surgery dropdown empty for surgeon" | Doctor/nurse can now list users (ENCOUNTER_VIEW permission) |
| "Seed command fails" | Run `python manage.py pilot_reset` then `python seed_data.py` then `python manage.py seed_demo_modules` |

---

# DATA EXPORT SYSTEM

## Export Any Table in 5 Formats

Every page with a data table now has **export buttons** next to the header.

### How to Export
1. Navigate to any page with data (Patients, Visits, Billing, etc.)
2. Find the **export buttons** next to the page title
3. Click your preferred format:
   - **CSV** — Opens in any spreadsheet software
   - **Excel** — Formatted XLSX with hospital header, colors, auto-width columns
   - **PDF** — Print-ready document with hospital header
   - **Word** — Editable DOCX document
   - **Image** — PNG screenshot of the data table

### Available Data Exports

| Page | Data Type | URL Pattern |
|------|-----------|-------------|
| Patient Search | patients | `/api/export/patients/` |
| Clinical Visits | visits | `/api/export/visits/` |
| Triage Queue | triage | `/api/export/triage/` |
| OPD Consultations | opd | `/api/export/opd/` |
| Emergency Cases | emergency | `/api/export/emergency/` |
| IPD Patients | ipd | `/api/export/ipd/` |
| Appointments | appointments | `/api/export/appointments/` |
| Surgical Cases | surgery | `/api/export/surgery/` |
| ANC Visits | obgyn | `/api/export/obgyn/` |
| Labor Records | labor | `/api/export/labor/` |
| Delivery Records | delivery | `/api/export/delivery/` |
| Birth Records | births | `/api/export/births/` |
| Postnatal Visits | postnatal | `/api/export/postnatal/` |
| Prescriptions | prescriptions | `/api/export/prescriptions/` |
| Dispensing | dispensing | `/api/export/dispensing/` |
| Invoices | invoices | `/api/export/invoices/` |
| Payments | payments | `/api/export/payments/` |
| Stock | stock | `/api/export/stock/` |
| Inventory | inventory | `/api/export/inventory/` |
| Audit Trail | audit | `/api/export/audit/` |
| Users | users | `/api/export/users/` |

### Manual URL Export
You can also export directly via URL:
```
http://127.0.0.1:8000/api/export/patients/?format=csv
http://127.0.0.1:8000/api/export/invoices/?format=xlsx
http://127.0.0.1:8000/api/export/surgery/?format=pdf
```

---

**Document prepared for:** Hospital Staff Training
**Jackson F. Doe Memorial Regional Referral Hospital**
