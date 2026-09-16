# JFD Hospital HMS — Training Manual & Standard Operating Procedures
## Step-by-Step Guide for Hospital Staff

**Version:** 8.0 — SOP sidebar order, role-based visibility, webcam capture, document upload, patient profile
**System:** JFD Hospital Management Information System
**Hospital:** Jackson F. Doe Memorial Regional Referral Hospital

---

# PART 1: REGISTRATION CLERK
## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password**
3. Click **"Log In"**
4. You land on the **Dashboard**

---

## SOP-1: Register a New Patient

**When:** Patient arrives at registration desk for the first time.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Register Patient"** | Sidebar → Register Patient (MRO/Admin only) |
| 2 | Fill in: **First Name**, **Last Name** | Registration form |
| 3 | Fill in: **Date of Birth** (use calendar picker) | Registration form |
| 4 | Select: **Gender** (Male / Female) | Dropdown |
| 5 | Fill in: **Phone Number** (if available) | Registration form |
| 6 | *(Optional)* **Take patient photo** — click camera icon for front-camera selfie | Photo section (top-left) |
| 7 | *(Optional)* **Open Camera** for webcam capture — click "Open Camera" → live video → "Capture" | Documents & Photos section |
| 8 | *(Optional)* **Upload documents** — drag & drop or click to browse (PDF, DOCX, images) | Documents & Photos section |
| 9 | Select: **Payer Category** (Self Pay / NHSLA / Other) | Dropdown |
| 10 | Select **Visit Type**: OPD / Emergency / Pediatric / OBGYN / Surgery | Dropdown |
| 11 | Enter **Chief Complaint** (if known) | Text area |
| 12 | Click **"Register Patient & Send to Queue"** | Bottom of form |
| 13 | **System shows MRN** (e.g., JFD-2026-00015) | Success message |
| 14 | **Registration fee ($5) auto-charged** — appears on patient invoice | Automatic |
| 15 | **Tell the patient their MRN** — they need it forever | Verbal |

**What just happened?**
- Patient created with lifelong MRN number
- Visit created with status "Checked In"
- Registration fee invoice created automatically
- Patient can now be seen by any department

---

## SOP-2: Walk-In Registration (Patient + Visit Together)

**When:** Patient walks in AND needs to be seen immediately (same visit).

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **"Register Patient"** | Sidebar → Register Patient |
| 2 | Fill in ALL demographics (name, DOB, gender, phone) | Registration form |
| 3 | *(Optional)* **Take patient photo** | Photo section |
| 4 | Select **Visit Type**: OPD / Emergency / Pediatric / OBGYN / Surgery | Dropdown |
| 5 | Enter **Chief Complaint** (what's wrong) | Text area |
| 6 | Select **Payer Category** | Dropdown |
| 7 | Click **"Register Patient & Send to Queue"** | Bottom of form |
| 8 | **System creates Patient AND Visit** simultaneously | Automatic |
| 9 | **Registration fee auto-charged** | Automatic |
| 10 | Patient appears in **Triage Queue** with status "Checked In" | Automatic |

**Visit Type Guide:**
| Visit Type | When to Use | Goes To |
|---|---|---|
| OPD | General outpatient consultation | OPD Queue → Triage |
| Emergency | Trauma, chest pain, severe symptoms | ER Queue → Triage |
| Pediatric | Children under 18 | Pediatric Queue |
| OBGYN | Pregnant women, gynecology | OBGYN Queue |
| Surgery | Pre-surgical assessment, surgical cases | Surgery Dashboard |

**What just happened?**
- Patient registered AND visit created in one step
- Registration fee charged automatically
- Patient is now waiting for triage

---

## SOP-3: Complete Clinical-First Registration (Retroactive)

**When:** Triage nurse used "Clinical-First Triage" (anonymous). You see a **yellow alert banner** at the top of the Patient Search page.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **"Patients"** page | Sidebar → Patients |
| 2 | **See yellow alert**: "X patient(s) awaiting registration" | Top of page |
| 3 | Click **"Complete Registration"** button next to the patient | Yellow alert section |
| 4 | Enter: **First Name**, **Last Name** | Modal form |
| 5 | Enter: **Date of Birth** | Modal form |
| 6 | Select: **Gender** | Modal form |
| 7 | Enter: **Phone** (if available) | Modal form |
| 8 | Select: **Payer Category** | Modal form |
| 9 | Click **"Register Patient"** | Modal button |
| 10 | **System generates MRN** and links all clinical records | Automatic |

**What just happened?**
- Anonymous triage patient now has a real identity
- MRN generated
- All vitals, triage data, and clinical records linked to this patient

---

## SOP-4: Complete Emergency Bypass Registration (Retroactive)

**When:** ER doctor used "Instant ER Bypass" for a critical patient. Patient has a **red TEMP badge** in the ER dashboard.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **"Emergency Department"** page | Sidebar → ER |
| 2 | **See red TEMP badge** next to patient name | Active ER Cases table |
| 3 | Click **"Complete Registration"** button | Next to TEMP badge |
| 4 | Enter: **First Name**, **Last Name** | Modal form |
| 5 | Enter: **Date of Birth** | Modal form |
| 6 | Select: **Gender** | Modal form |
| 7 | Enter: **Phone** (if available) | Modal form |
| 8 | Select: **Payer Category** | Modal form |
| 9 | Click **"Reconcile & Register"** | Modal button |
| 10 | **System generates MRN** and links all clinical records | Automatic |

**What just happened?**
- Temporary emergency patient now has a real identity
- MRN generated
- All treatment records, labs, medications linked to this patient

---

# PART 2: TRIAGE NURSE

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your triage nurse account)
3. Click **"Log In"**

---

## SOP-5: Standard Triage (Pathway A — Most Common)

**When:** Patient has been registered and is in the Triage Queue.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Triage"** | Sidebar → Triage (Triage Nurse/Doctor/Nurse only) |
| 2 | **See the Triage Queue** on the left — patients waiting | Left panel |
| 3 | **Click on a patient** in the queue | Patient card |
| 4 | Patient's name and MRN appear on the right | Right panel |
| 5 | Enter **Chief Complaint** (what's wrong?) | Text area |
| 6 | Enter **Vital Signs**: | Form fields |
| | → Temperature (°C) | e.g., 37.5 |
| | → Heart Rate (BPM) | e.g., 72 |
| | → Respiratory Rate (/min) | e.g., 18 |
| | → BP Systolic | e.g., 120 |
| | → BP Diastolic | e.g., 80 |
| | → SpO2 (%) | e.g., 98 |
| 7 | **System auto-suggests** Acuity Level and Department | Yellow/blue banner |
| 8 | **Review the suggestion** | |
| | → **Agree?** Keep the suggested level | |
| | → **Disagree?** Select a different level + write justification | Override section |
| 9 | *(Optional)* **Capture photo** — click "Open Camera" → live video → "Capture" | Photo & Documents section |
| 10 | *(Optional)* **Upload documents** — drag & drop lab results, referral letters, etc. | Photo & Documents section |
| 11 | Click **"Complete Triage & Route Patient"** | Green button |

**What just happened?**
- Patient's vitals recorded
- Acuity level assigned (1-5)
- Patient department assigned, awaiting clinical assessment
- Patient disappears from your queue

---

## SOP-6: Clinical-First Triage (Pathway B)

**When:** Patient needs immediate assessment but registration desk is busy/closed.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Triage"** | Sidebar → Triage |
| 2 | Click **"+ Clinical-First Triage"** button | Top-right of Triage Queue header |
| 3 | **Read the amber warning**: This creates anonymous triage | Modal |
| 4 | Enter **Chief Complaint** | Modal form |
| 5 | Enter **Vital Signs** (same as Standard Triage) | Modal form |
| 6 | Select **Acuity Level** (1-5) | Radio buttons |
| 7 | Click **"Submit Triage"** | Modal button |
| 8 | **System creates anonymous visit** with status "pending_registration" | Automatic |
| 9 | **Note the Visit Number** — tell the clerk | Success toast |

**What just happened?**
- Patient triaged WITHOUT registration
- Visit created with "pending registration" status
- Clerk will complete registration later (see SOP-3)

---

# PART 3: ER DOCTOR / NURSE

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your ER account)
3. Click **"Log In"**

---

## SOP-7: Instant ER Bypass (Pathway C — Critical Emergency)

**When:** Patient arrives in CRITICAL condition. No time for registration or triage.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Emergency"** | Sidebar → Emergency icon |
| 2 | Click the **red "INSTANT ER BYPASS"** button | Top of ER Dashboard (flashing) |
| 3 | **Read the red warning**: This skips registration | Modal |
| 4 | Enter **Patient Name** (if known, otherwise leave as "UNKNOWN") | Modal form |
| 5 | Enter **Chief Complaint** (e.g., "Chest pain, unconscious") | Modal form |
| 6 | Enter **Emergency Reason** (e.g., "Motor vehicle accident") | Modal form |
| 7 | Click **"ACTIVATE BYPASS"** | Red button |
| 8 | **System creates TEMP patient** with token (TEMP-ER-YYYY-XXXXX) | Automatic |
| 9 | **WRITE DOWN the Temp Token** — shown in success toast | Critical! |
| 10 | **BEGIN TREATMENT IMMEDIATELY** | No barriers |

**What you can do now:**
- Write clinical notes
- Order lab tests
- Order medications
- Request imaging
- Document procedures

**What you CANNOT do yet:**
- Generate formal invoice
- Discharge formally

---

## SOP-8: ER Evaluation Workflow

**When:** ER patient needs assessment and intervention tracking.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **"Emergency Department"** | Sidebar → Emergency |
| 2 | Find patient in **"Active ER Cases"** table | Main table |
| 3 | Click **"Fill Evaluation"** button | Green button in Actions column |
| 4 | Complete: **HPI** (History of Present Illness) | Evaluation form |
| 5 | Complete: **PMH** (Past Medical History) | Evaluation form |
| 6 | Complete: **ROS** (Review of Systems) | Evaluation form |
| 7 | Complete: **Physical Exam** | Evaluation form |
| 8 | Complete: **Interventions** | Evaluation form |
| 9 | Click **"Save Evaluation"** | Form button |
| 10 | Click **"Log Intervention"** for each treatment given | Red button |
| 11 | Enter intervention notes + vitals | Modal form |
| 12 | Click **"Save Intervention"** | Modal button |

---

## SOP-9: ER Disposition

**When:** ER patient is ready to be admitted, discharged, or transferred.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **First**: Complete Evaluation + log at least 1 Intervention | See SOP-8 |
| 2 | Click **"Process Disposition"** button | Blue button (now enabled) |
| 3 | Select **Disposition Type**: | Dropdown |
| | → **Admit to IPD** — patient needs hospital bed | |
| | → **Discharge** — patient can go home | |
| | → **Transfer** — patient needs different department | |
| 4 | Enter **Diagnosis / Notes** | Text area |
| 5 | Click **"Process Disposition"** | Modal button |

**If Admitted to IPD:**
- Admission record created automatically
- Go to **IPD Dashboard** to assign a bed

**If Discharged:**
- Visit marked as completed
- Patient can leave

---

# PART 4: OPD DOCTOR

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your doctor account)
3. Click **"Log In"**

---

## SOP-10: Standard OPD Consultation

**When:** Patient is in your queue (status: "in_progress").

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"OPD Consultation"** | Sidebar → OPD Consultation (Doctor/Nurse only) |
| 2 | Click **"Find Active Visits"** | Button on OPD page |
| 3 | **See list of patients** waiting for you | Modal list |
| 4 | **Click on a patient** to select | Visit card |
| 5 | **Review on the left panel:** | Left sidebar |
| | → Recorded Vitals (BP, HR, Temp, SpO2) | |
| | → Allergies & Risk Alerts | |
| | → Visit History | |
| 6 | **Write SOAP Notes** in the main area: | Text areas |
| | → **Subjective** (what patient says) | |
| | → **Objective** (what you find) | |
| | → **Assessment** (your diagnosis) | |
| | → **Plan** (treatment) | |
| 7 | **Add Diagnosis**: Type ICD-10 code or search | Search field |
| 8 | **Place Orders**: Click "+ Add Order Item" | Button |
| 9 | **Write Prescriptions**: Click "+ Add Prescription" | Button |
| 10 | Click **"Finalize Encounter"** | Green button |
| 11 | **System auto-posts orders to billing** | Automatic |

---

## SOP-11: Escalate to ER (OPD → ER)

**When:** Patient in OPD crashes or needs emergency care.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **While in OPD Consultation** for the patient | OPD page |
| 2 | Click **"Escalate to ER"** button | Amber button (top-right) |
| 3 | **Read the amber warning**: Visit will transfer to ER | Modal |
| 4 | Enter **Reason for Escalation** | Text area |
| 5 | Click **"Confirm Escalation"** | Modal button |
| 6 | **System changes visit type to ER** | Automatic |
| 7 | **ER team is notified** via their dashboard | Automatic |
| 8 | Patient appears in **ER Active Cases** | Automatic |

---

## SOP-12: Admit to IPD (OPD → IPD)

**When:** OPD doctor determines patient needs hospitalization.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **While in OPD Consultation** for the patient | OPD page |
| 2 | Click **"Admit to IPD"** button | Blue button (top-right) |
| 3 | **Read the blue warning**: Admission will be created | Modal |
| 4 | Enter **Admitting Diagnosis** | Text area |
| 5 | Select **Admission Type** (Emergency / Elective / Observation) | Dropdown |
| 6 | Click **"Confirm Admission"** | Modal button |
| 7 | **Admission record created** | Automatic |
| 8 | Go to **IPD Dashboard** to assign a bed | Manual |

---

# PART 5: IPD / WARD DOCTOR

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your IPD account)
3. Click **"Log In"**

---

## SOP-13: IPD Bed Assignment

**When:** Patient needs a hospital bed.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"IPD"** | Sidebar → IPD icon |
| 2 | **See the Bed Matrix** | Main area |
| | → **Green** = Available bed | |
| | → **Red** = Occupied bed | |
| 3 | **Click on a green bed** (or auto-assigned from ER/OPD) | Bed cell |
| 4 | Enter: **Admitting Diagnosis** | Modal form |
| 5 | Enter: **Expected Discharge Date** (if known) | Modal form |
| 6 | Click **"Confirm"** | Modal button |
| 7 | **Bed status changes to OCCUPIED** (red) | Automatic |

---

## SOP-14: IPD Bed-to-Bed Transfer

**When:** Patient needs to move to a different bed/ward.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **IPD Dashboard** | Sidebar → IPD |
| 2 | Find the **occupied bed** with the patient | Bed matrix (red) |
| 3 | Click **"Transfer"** button on the bed | Blue button |
| 4 | **Select target bed** from dropdown (only shows available beds) | Modal dropdown |
| 5 | Enter **Reason** (e.g., "Step-down care", "Isolation needed") | Modal form |
| 6 | Click **"Confirm Transfer"** | Modal button |
| 7 | **Old bed freed** (green), **new bed occupied** (red) | Automatic |

---

## SOP-15: IPD Discharge

**When:** Patient is ready to leave the hospital.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **IPD Dashboard** | Sidebar → IPD |
| 2 | Find the **occupied bed** with the patient | Bed matrix (red) |
| 3 | Click **"Discharge"** button on the bed | Red button |
| 4 | Select **Discharge Type**: | Dropdown |
| | → Routine (normal discharge) | |
| | → AMA (Against Medical Advice) | |
| | → Referred (to another hospital) | |
| | → Transferred (to another ward) | |
| | → Deceased | |
| 5 | Enter **Discharge Summary** | Text area |
| 6 | Optionally: **Schedule Follow-up Appointment** | Date picker |
| 7 | Click **"Confirm Discharge"** | Modal button |
| 8 | **Bed freed** (green), **visit completed** | Automatic |

---

# PART 6: PHARMACIST

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your pharmacist account)
3. Click **"Log In"**

---

## SOP-16: Dispense Medication

**When:** Patient has a prescription and has paid.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Pharmacy"** | Sidebar → Pharmacy icon |
| 2 | **See pending prescriptions** | Dispensing dashboard |
| 3 | **Click on a prescription** | Prescription list |
| 4 | **Verify**: Medication name, dosage, quantity | Prescription detail |
| 5 | Click **"Dispense"** | Dispense button |
| 6 | **System deducts stock** from inventory | Automatic |
| 7 | **System posts to billing** | Automatic |

---

# PART 7: CASHIER

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your cashier account)
3. Click **"Log In"**

---

## SOP-17: Process Payment

**When:** Patient comes to pay their bill.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Cashier"** | Sidebar → Cashier icon |
| 2 | **Search for patient** or select from list | Search / List |
| 3 | **Review invoice line items** | Invoice detail |
| 4 | **Enter payment amount** | Payment form |
| 5 | Select **Payment Method**: | Dropdown |
| | → Cash | |
| | → Mobile Money | |
| | → Bank Transfer | |
| | → Insurance | |
| 6 | Click **"Process Payment"** | Button |
| 7 | **Print receipt** | Receipt generated |

---

# PART 8: SYSTEM ADMINISTRATOR

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Admin Username** and **Password**
3. Click **"Log In"**

---

## SOP-18: Configure Triage Criteria

**When:** Doctor/Admin wants to adjust auto-suggestion rules.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Triage Criteria"** | Admin section in sidebar |
| 2 | **See all active rules** in the table | Criteria table |
| 3 | **Add new rule**: | Create form |
| | → Enter **Rule Name** (e.g., "Severe Dehydration") | |
| | → Select **Vital Sign** (e.g., "Blood Glucose") | |
| | → Select **Operator** (e.g., "< less than") | |
| | → Enter **Threshold** (e.g., "50") | |
| | → Select **Suggested Acuity** (e.g., "2 - Emergent") | |
| | → Select **Suggested Department** (e.g., "ER") | |
| | → Click **"Create Rule"** | |
| 4 | **Toggle rule**: Click **"Activate/Deactivate"** | Table button |
| 5 | **Delete rule**: Click **"Delete"** (requires confirmation) | Table button |

**Default Rules (12 seeded):**
| Rule | Condition | Suggests |
|------|-----------|----------|
| Severe Hypotension | BP Systolic < 90 | Acuity 2 → ER |
| Hypertensive Crisis | BP Systolic > 180 | Acuity 2 → ER |
| Severe Hypoxia | SpO2 < 90 | Acuity 1 → ER |
| Mild Hypoxia | SpO2 < 94 | Acuity 3 → ER |
| Severe Tachycardia | HR > 120 | Acuity 3 → ER |
| Severe Bradycardia | HR < 50 | Acuity 2 → ER |
| High Fever | Temp > 40 | Acuity 3 → OPD |
| Hypothermia | Temp < 35 | Acuity 2 → ER |
| Severe Tachypnea | RR > 30 | Acuity 2 → ER |
| Hypoglycemia | Glucose < 60 | Acuity 2 → ER |
| Severe Hyperglycemia | Glucose > 400 | Acuity 2 → ER |
| Severe Pain | Pain ≥ 8 | Acuity 3 → OPD |

---

## SOP-19: Hospital Settings (Branding & Financial)

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Hospital Settings"** | Admin section in sidebar |
| 2 | Upload **Hospital Logo** | File upload |
| 3 | Enter **Hospital Name** | Text field |
| 4 | Enter **Contact Info** (phone, email, address) | Form fields |
| 5 | Scroll to **"Financial Settings"** section | Below branding fields |
| 6 | Set **Registration Fee** ($ amount) | Number field — charged to each patient at registration |
| 7 | Set **Follow-Up Window** (days) | Number field — days before/after follow-up date considered "inside window" |
| 8 | Click **"Save Settings"** | Button |

**Note:** Registration fee changes take effect on the next registration. Existing invoices are not affected.

---

## SOP-20: User Management

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"User Management"** | Admin section |
| 2 | **See all users** in table | User list |
| 3 | **Edit user**: Click "Edit" button | Table row |
| 4 | **Change role**: Select new role from dropdown | Modal form |
| 5 | **Deactivate user**: Click "Deactivate" | Table row |
| 6 | **Save changes** | Modal button |

---

## SOP-21: Role & Permission Management

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Role Management"** | Admin section |
| 2 | **See all roles** with permission counts | Role table |
| 3 | **Edit permissions**: Click "Edit Permissions" | Table row |
| 4 | **Toggle permissions**: Check/uncheck boxes | Permission grid |
| 5 | **Save** | Modal button |

---

# PART 9: LABORATORY TECHNICIAN

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your labtech account)
3. Click **"Log In"**

---

## SOP-22: View Specimens & Results

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Lab"** | Sidebar → Lab icon |
| 2 | **See specimen list** | Lab dashboard |
| 3 | **Click on specimen** to view details | Specimen row |
| 4 | **View result** if available | Result panel |
| 5 | **Verify result** if needed | Verify button |

**Pre-seeded data:** 3 specimens (Blood, Urine, Stool), 2 diagnostic results (CBC, Malaria test)

---

# PART 10: OBGYN SPECIALIST

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your obgyn account)
3. Click **"Log In"**

---

## SOP-23: ANC Visit Management

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"OBGYN"** | Sidebar → OBGYN icon |
| 2 | **See Maternity Ward Beds panel** at top | Top of page — green/red bed indicators |
| 3 | **See ANC Register** below | Section with "+ New ANC Visit" button |
| 4 | **Create new**: Click "+ New ANC Visit" | Button |
| 5 | **Fill form**: LMP Date (required — auto-calculates EDD), GA, BP, Weight, Hb | Form |
| 6 | **Save** | Button |

**Note:** ANC visits are **outpatient** — no bed assignment needed unless the patient is being admitted for monitoring.

**Maternity Ward Beds Panel:**
- Shows all beds in Maternity Ward (MAT1)
- **Green** = free (available for labor admission)
- **Red** = occupied
- Summary shows: "X free / Y occupied / Z total"

**Pre-seeded data:** 2 ANC visits with full vitals

---

## SOP-24: Labor & Delivery

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **Click "+ Record Labor"** on OBGYN dashboard | Button |
| 2 | **Fill form**: Patient, Status, Cervical Dilation, FHR, Presentation | Form |
| 3 | **Optional**: Select a **green bed** from Maternity Ward for admission | Bed selector |
| 4 | **Save** — Admission auto-created if bed selected | Button |
| 5 | **Record delivery**: Click "Save Delivery Outcome" | Bottom section |
| 6 | **Fill form**: Mode, Baby Sex, Weight, APGAR scores | Form |
| 7 | **Save** | Button |

**When a bed is selected during labor recording:**
- Admission auto-created in Maternity Ward
- Bed turns red (occupied)
- Patient visible in IPD dashboard for discharge later

---

## SOP-25: Birth Recording

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **Click on delivery record** | Table row |
| 2 | **Click "Record Birth"** | Button |
| 3 | **Fill form**: Name, Sex, Weight, Length, Apgar scores | Form |
| 4 | **Check**: Vitamin K, Eye Prophylaxis, Hep B Vaccine | Checkboxes |
| 5 | **Save** | Button |

---

## SOP-26: Postnatal Visit

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **Click "Postnatal" tab** | Tab bar |
| 2 | **See postnatal list** | Table |
| 3 | **Create new**: Click "+ New Postnatal Visit" | Button |
| 4 | **Fill form**: Day postpartum, BP, Temp, Fundal height, Baby weight | Form |
| 5 | **Save** | Button |

**Pre-seeded data:** 1 postnatal visit (Day 3 postpartum)

---

# PART 11: SURGEON

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your surgeon account)
3. Click **"Log In"**

---

## SOP-27: Surgical Case Management

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Surgery"** | Sidebar → Surgery icon |
| 2 | **See Surgical Ward Beds panel** at top | Top of page — green/red bed indicators |
| 3 | **See surgical cases** in Theatre Schedule | Below bed panel |
| 4 | **Schedule new case**: Click "+ Schedule Case" | Button |
| 5 | **Fill form**: Patient, Procedure, Surgeon, Priority, Anesthesia | Form |
| 6 | **Optional**: Select a free bed for pre-op admission | Bed selector in form |
| 7 | **Save** | Button |
| 8 | **Click on case** to view details | Case card |
| 9 | **Change status**: Scheduled → In Progress → Completed | Status buttons |

**Surgical Ward Beds Panel:**
- Shows all beds in Surgical Ward 1 (SURG1)
- **Green** = free (available for admission)
- **Red** = occupied (patient admitted)
- **Amber** = reserved
- Summary shows: "X free / Y occupied / Z total"

**Pre-seeded data:** 3 surgical cases (ORIF, Appendectomy, Hernia Repair)

---

## SOP-28: Ward Bed Assignment (Surgeon)

**When:** Surgical patient needs pre-op or post-op admission.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | **Open Surgery Dashboard** | Sidebar → Surgery |
| 2 | **Check Surgical Ward Beds** panel | Top of page |
| 3 | **Schedule a case** with patient details | "+ Schedule Case" button |
| 4 | **In the form**, select a **green bed** from the dropdown | Bed selector |
| 5 | **Save** — Admission auto-created | Button |
| 6 | **Bed turns red** in the panel | Automatic |

**What just happened?**
- SurgicalCase created with procedure details
- Admission record auto-created in Surgical Ward 1
- Bed marked as occupied
- Patient visible in IPD dashboard for discharge later

---

# PART 12: PEDIATRICIAN

## Login
1. Open browser → go to `http://your-server-address`
2. Enter **Username** and **Password** (your doctor account)
3. Click **"Log In"**

---

## SOP-35: Pediatric Assessment

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Pediatric"** | Sidebar → Pediatric icon |
| 2 | **See child patients** | Table |
| 3 | **Click on patient** to open assessment | Patient row |
| 4 | **Fill assessment form**: | Form sections |
| | → **Child Problem** (chief complaint) | |
| | → **Danger Signs** (dyspnea, dehydration, vomiting, etc.) | |
| | → **Vitals** (temp, HR, RR, SpO2, weight) | |
| | → **Clinical Assessment** | |
| | → **Diagnosis** | |
| | → **Treatment Plan** | |
| 5 | **Save Assessment** | Button |

**Pre-seeded data:** 2 child patients (ages 3 and 7) with full assessments

---

# PART 13: TRIAGE-FIRST WORKFLOW & FOLLOW-UP MANAGEMENT

## SOP-30: Triage Queue Registration (Triage-First Flow)

**When:** A patient was triaged using "Clinical-First Triage" (anonymous) and now needs formal registration.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Triage Queue"** | Sidebar → Triage Queue (under Triage section) |
| 2 | **See patients awaiting registration** | Table with Visit #, Patient, Chief Complaint, Acuity |
| 3 | Click **"Complete Registration"** next to the patient | Action button on right |
| 4 | **Registration form opens** pre-filled with visit info | Form shows triage banner at top |
| 5 | Fill in: **First Name**, **Last Name**, **DOB**, **Gender** | Registration form |
| 6 | *(Optional)* **Take patient photo** | Photo section |
| 7 | Select **Payer Category** | Dropdown |
| 8 | Click **"Complete Registration & Start Consultation"** | Bottom of form |
| 9 | **Registration fee auto-charged** | Automatic |
| 10 | **Patient status → in_progress** — appears in OPD queue | Automatic |

**What just happened?**
- Anonymous triage visit linked to a real patient
- MRN generated, registration fee charged
- Patient ready for consultation

---

## SOP-31: Patient Photo Capture & Document Upload

**When:** Registering a new patient or during triage assessment.

### Photo Capture (3 methods)

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | On registration/triage form, find the **"Documents & Photos"** section | Below Visit Details |
| 2a | **Method 1 — Webcam:** Click **"Open Camera"** → live video feed → click **"Capture"** | Documents & Photos section |
| 2b | **Method 2 — Mobile camera:** Click the photo field → device opens front camera | Photo section (top-left) |
| 2c | **Method 3 — File upload:** Click photo field → select image from device | File picker (JPG/PNG) |
| 3 | **Preview** shows in the circular frame | Live preview |
| 4 | Submit — **photo saved with patient/triage record** | Automatic |

### Document Upload

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Scroll to **"Documents & Photos"** section | Below Visit Details |
| 2 | **Drag & drop** files into the upload zone, OR **click to browse** | Dashed border area |
| 3 | Select any files: PDF, DOCX, XLSX, JPG, PNG (max 10MB each) | File picker |
| 4 | **Files appear in a list** with name, size, and remove button | File list below upload zone |
| 5 | Upload more files by dragging or clicking again | Repeat as needed |
| 6 | Submit — **files saved to patient record** | Automatic |

**Note:** Photo is optional. If skipped, the patient record shows initials in the EMR drawer. Documents are viewable on the Patient Profile page.

---

## SOP-32: Configure Registration Fee

**When:** Admin needs to change the registration fee amount.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Hospital Settings"** | Admin section |
| 2 | Scroll to **"Financial Settings"** section | Below branding fields |
| 3 | Update **Registration Fee** ($ amount) | Number field |
| 4 | Update **Follow-Up Window** (days) if needed | Number field |
| 5 | Click **"Save Settings"** | Button |

**Note:** Fee changes take effect on the next registration. Existing invoices are not affected.

---

## SOP-33: Follow-Up Queue Management

**When:** Checking which patients have scheduled follow-up visits.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | From sidebar, click **"Follow-Up Queue"** | Sidebar → Follow-Up Queue (after Appointments) |
| 2 | **See overdue follow-ups** (red alert banner) | Top of page |
| 3 | **See inside-window follow-ups** (green table) | Main table |
| 4 | **See upcoming follow-ups** (future dates) | Bottom section |
| 5 | Click **"View Patient"** to open patient record | Action button |

**Status indicators:**
| Color | Status | Meaning |
|-------|--------|---------|
| Green | On Track | Follow-up within ±3 days of today |
| Amber | Approaching | 4-7 days away |
| Red | Overdue | Past due date |

---

## SOP-34: Discharge with Follow-Up

**When:** A nurse is discharging a patient and wants to schedule a follow-up visit.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Open **Nurse Notes** page | Sidebar → Nurse Notes |
| 2 | **Select the visit** to discharge | Visit search |
| 3 | Click **"Discharge Patient"** button | Patient Actions card |
| 4 | **Discharge modal opens** | Modal |
| 5 | Enter **Discharge Notes** | Text area |
| 6 | Check **"Schedule Follow-Up Visit"** | Checkbox (default: checked) |
| 7 | Select **Follow-Up Date** | Date picker (default: 7 days from today) |
| 8 | Enter **Reason** for follow-up | Text field |
| 9 | Click **"Discharge & Schedule Follow-Up"** | Button |
| 10 | **Visit status → completed** | Automatic |
| 11 | **Follow-up appointment created** | Automatic |

**What just happened?**
- Patient discharged from active care
- Follow-up appointment scheduled
- Patient appears in Follow-Up Queue

---

## SOP-35: Nursing Progress Notes (WHO SOAP Format)

**When:** A nurse needs to document patient care at any point during the visit (after triage, during OPD/ER/IPD, before discharge).

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Open **Nurse Notes** page | Sidebar → Nurse Notes |
| 2 | **Search for the patient** by name or MRN | Patient search field |
| 3 | **Select the active visit** from search results | Click visit card |
| 4 | **Fill in SOAP fields:** | Form (2x2 grid) |
| | **S — Subjective:** Patient's complaints, symptoms, concerns | Top-left field |
| | **O — Objective:** Vital signs, physical exam, lab results | Top-right field |
| | **A — Assessment:** Nurse's clinical judgment | Bottom-left field |
| | **P — Plan:** Interventions, patient education, follow-up | Bottom-right field |
| 5 | Click **"Save SOAP Note"** | Green button |
| 6 | Note appears in **Notes History** | Below form |

**Quick Access from Clinical Pages:**
- **OPD:** Click "Nurse Notes" button in header bar
- **ER:** Click "Nurse Notes" link on active visit row
- **IPD:** Click note icon on occupied bed card

**SOAP Format Guide:**
- **Subjective (S):** What the patient says — "Patient reports headache for 3 days, mild fever"
- **Objective (O):** What you observe/measure — "Temp 37.8°C, HR 82, BP 128/82, SpO2 98%"
- **Assessment (A):** Your clinical judgment — "Viral headache, no red flags"
- **Plan (P):** What you will do — "Paracetamol 500mg TID, rest, follow-up in 3 days"

**What just happened?**
- Nursing progress note saved in WHO SOAP format
- Note linked to patient's visit and encounter
- Note visible to all clinical staff in the patient's record

---

## SOP-36: View Patient Profile

**When:** Need to view a patient's complete record including documents, visits, triage history, and invoices.

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Go to **"Search Patients"** (Master Patient Index) | Sidebar → Search Patients |
| 2 | **Search** by MRN, name, or phone | Search bar |
| 3 | Click **"Profile"** button next to the patient | Patient results table |
| 4 | **Patient Profile page opens** showing: | Profile page |
| | → **Demographics:** Name, MRN, DOB, gender, phone, payer | Top card |
| | → **Photo:** Patient photo (if uploaded) | Top-left |
| | → **Documents & Files:** Uploaded documents with download links | Left column |
| | → **Visit History:** Recent visits with status | Left column |
| | → **Triage History:** Triage records with vitals and photos | Right column |
| | → **Recent Invoices:** Invoice list with status | Right column |
| 5 | Click **"View"** on any document to open/download it | Document list |
| 6 | Click **"Back to Search"** to return to patient search | Top-right button |

**What just happened?**
- Complete patient record viewable in one place
- Documents uploaded during registration/triage are accessible
- Triage photos visible in triage history
- Invoice status at a glance

---

# PART 14: THREE PATHWAYS — FLOW SUMMARY

## Pathway A: Standard Flow (90% of patients)

```
┌─────────────────┐
│  REGISTRATION    │  Clerk registers patient → MRN generated
│  CLERK           │
└────────┬────────┘
         ↓
┌─────────────────┐
│  TRIAGE          │  Nurse records vitals, assigns acuity, routes to dept
│  NURSE           │
└────────┬────────┘
         ↓
┌─────────────────┐
│  OPD / ER / IPD  │  Doctor treats patient
│  DOCTOR          │
└────────┬────────┘
         ↓
┌─────────────────┐
│  PHARMACY        │  Pharmacist dispenses medication
│  PHARMACIST      │
└────────┬────────┘
         ↓
┌─────────────────┐
│  BILLING         │  Cashier processes payment
│  CASHIER         │
└────────┬────────┘
         ↓
┌─────────────────┐
│  DISCHARGE       │  Patient goes home
└─────────────────┘
```

---

## Pathway B: Clinical-First Flow

```
┌─────────────────┐
│  TRIAGE (FIRST!) │  Nurse triages BEFORE registration
│  NURSE           │  Click "Clinical-First Triage" button
└────────┬────────┘
         ↓
┌─────────────────┐
│  CLINICAL CARE   │  Doctor treats immediately
│  DOCTOR          │  Visit status = "pending_registration"
└────────┬────────┘
         ↓
┌─────────────────┐
│  REGISTRATION    │  Clerk completes registration later
│  CLERK           │  Click "Complete Registration" in yellow alert
└─────────────────┘
```

---

## Pathway C: Emergency Bypass Flow (Critical)

```
┌─────────────────┐
│  INSTANT BYPASS  │  ER Doctor clicks "INSTANT ER BYPASS"
│  ER DOCTOR       │  Temp patient created (no registration)
└────────┬────────┘
         ↓
┌─────────────────┐
│  TREATMENT       │  Begin treatment IMMEDIATELY
│  ER TEAM         │  Use temp token for all orders
└────────┬────────┘
         ↓
┌─────────────────┐
│  RECONCILE       │  Clerk/ER Nurse completes registration
│  CLERK           │  Click "Complete Registration" on temp patient
└─────────────────┘
```

---

# PART 15: BUTTON REFERENCE MAP

## ER Dashboard Buttons
| Button | Color | What It Does |
|--------|-------|-------------|
| **INSTANT ER BYPASS** | Red (flashing) | Creates temp patient, skip registration |
| **Fill Evaluation** | Green | Opens ER evaluation form |
| **Log Intervention** | Red | Records treatment/procedure |
| **Process Disposition** | Blue | Admit, discharge, or transfer |
| **Complete Registration** | Amber | Reconciles temp patient (only on TEMP patients) |

## OPD Consultation Buttons
| Button | Color | What It Does |
|--------|-------|-------------|
| **Escalate to ER** | Amber | Transfers visit to ER department |
| **Admit to IPD** | Blue | Creates admission record |
| **Discharge Patient** | Red | Discharges from OPD |
| **Finalize Encounter** | Green | Saves SOAP notes + orders |

## Triage Page Buttons
| Button | Color | What It Does |
|--------|-------|-------------|
| **Clinical-First Triage** | White/transparent | Anonymous triage before registration |
| **Complete Triage & Route** | Green | Submits triage + routes patient |

## Patient Search Page
| Button | Color | What It Does |
|--------|-------|-------------|
| **Complete Registration** (in yellow alert) | Blue | Completes Clinical-First registration |

## IPD Dashboard
| Button | Color | What It Does |
|--------|-------|-------------|
| **Transfer** | Blue | Moves patient to different bed |
| **Discharge** | Red | Discharges from hospital |

---

# PART 17: TROUBLESHOOTING

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
| "No beds showing in ward panel" | Ensure wards seeded: run `python manage.py seed_demo_modules` |
| "Can't select Surgery at registration" | Clear browser cache. Form now has 5 visit type options |
| "Seed command fails" | Run `pilot_reset` → `seed_data` → `seed_demo_modules` |
| "Registration fee not showing on invoice" | Go to Hospital Settings > Financial Settings, set fee amount, register new patient |
| "Photo not uploading on registration" | Ensure form has `enctype="multipart/form-data"`, check file < 5MB |
| "Webcam not working" | Check browser permissions for camera access. Try Chrome/Edge. Use file upload as fallback |
| "Documents not saving" | Ensure form has `enctype="multipart/form-data"`. Files max 10MB each |
| "Can't see patient profile" | Click "Profile" button in patient search results (next to "View EMR") |
| "Sidebar shows wrong links" | Log out and log back in. Sidebar is role-based — each role sees only their links |
| "Triage Queue is empty" | Use "Clinical-First Triage" button on Triage page first |
| "Follow-Up Queue shows no patients" | Create follow-up from OPD discharge or Nurse Notes page |
| "Discharge button not working" | Select an active visit on the Nurse Notes page first |
| "SOAP form not saving" | At least one SOAP field (S, O, A, or P) must be filled |

---

# PART 18: DATA EXPORT

## Exporting Data in Any Format

**When:** You need to download a list of patients, invoices, stock items, or any other data for reporting, auditing, or sharing.

### SOP-29: Export Data from Any Page

| Step | Action | Where to Click |
|------|--------|----------------|
| 1 | Navigate to the page with the data you want | Sidebar → Patients, Billing, etc. |
| 2 | Find the **export buttons** next to the page title | Top of page, near the header |
| 3 | Click your preferred format: **CSV**, **Excel**, **PDF**, **Word**, or **Image** | Button group |
| 4 | File downloads automatically | Browser downloads folder |

### Export Format Guide

| Format | When to Use | File Extension |
|--------|-------------|----------------|
| **CSV** | Quick data analysis in any spreadsheet | `.csv` |
| **Excel** | Formatted report with hospital header, colors | `.xlsx` |
| **PDF** | Print-ready document for meetings/reports | `.pdf` |
| **Word** | Editable document for modification | `.docx` |
| **Image** | Screenshot-style image for sharing | `.png` |

### Available Exports

| Page | What You Get |
|------|-------------|
| Patient Search | All patients with MRN, name, DOB, phone |
| Triage Queue | Current triage queue with acuity |
| OPD Consultations | All OPD visits |
| Emergency Cases | All ER cases |
| IPD Patients | All admitted patients |
| Appointments | All scheduled appointments |
| Surgery Dashboard | All surgical cases |
| OBGYN Dashboard | ANC, labor, delivery, birth, postnatal records |
| Cashier | All invoices |
| Payment History | All payments |
| Stock | All stock items with quantities |
| Inventory | All inventory items |
| Admin → Users | All users with roles |
| Admin → Audit Trail | Last 500 audit entries |

---

# DOCUMENT CONTROL

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Aug 2026 | Initial SOPs |
| 2.0 | Sep 2026 | Dynamic State Machine, Three Pathways |
| 3.0 | Sep 2026 | Step-by-step training format, all buttons verified |
| 4.0 | Sep 2026 | Added 6 specialty modules: Surgery, OBGYN, Pediatric, Lab, Maternity, Admin |
| 5.0 | Sep 2026 | WHO-compliant registration: Surgery visit type, ward bed occupancy panels, bed assignment in case/ANC forms |
| 6.0 | Sep 2026 | Data export system: CSV, Excel, PDF, Word, Image for all 21 data types |
| 7.0 | Sep 2026 | Board recommendations: Registration Fee config, Patient Photo Capture, Triage-First workflow, Follow-Up Queue & Discharge |
| 8.0 | Sep 2026 | Nursing Progress Notes (WHO SOAP Format): 4-field SOAP form, quick access from OPD/ER/IPD pages, flexible any-time documentation |

**Prepared for:** Hospital Staff Training — Jackson F. Doe Memorial Regional Referral Hospital
