# JFD Hospital HMS — Admin Setup & Seed Data Guide
## How to Add, Edit, and Manage System Data Before Patient Flow

**For:** System Administrators
**Date:** September 2026

---

## Quick Status Check

Before patients can flow through the system, these data types must exist:

| # | Data Type | Where to Manage | Has UI Form? | Has API? |
|---|-----------|----------------|--------------|----------|
| 1 | Hospital Settings | `/admin/settings/` | ✅ Yes | ✅ |
| 2 | Departments | `/admin/departments/` | ✅ Yes | ✅ |
| 3 | Users & Roles | `/admin/users/` + `/admin/roles/` | ✅ Yes | ✅ |
| 4 | Triage Criteria | `/admin/triage-criteria/` | ✅ Yes | ✅ |
| 5 | Wards & Beds | `/clinical/ipd/` | ✅ Yes | ✅ |
| 6 | Medications | API only | ❌ No UI form | ✅ |
| 7 | Inventory Stores | `/inventory/manage/` | ✅ Yes (tab) | ✅ |
| 8 | Inventory Categories | `/inventory/manage/` | ✅ Yes (tab) | ✅ |
| 9 | Inventory Items | `/inventory/manage/` | ✅ Yes (tab) | ✅ |
| 10 | Stock (Receive) | `/inventory/` | ✅ Yes (button) | ✅ |
| 11 | Lab Test Catalogue | API only | ❌ No UI form | ✅ |
| 12 | Radiology Test Catalogue | API only | ❌ No UI form | ✅ |
| 13 | Service Items & Prices | API only | ❌ No UI form | ✅ |
| 14 | Price Lists | API only | ❌ No UI form | ✅ |

---

## 1. Hospital Settings (Logo, Name, Contact)

**URL:** `http://your-server/admin/settings/`
**Who:** Admin only

| Step | Action |
|------|--------|
| 1 | Go to `/admin/settings/` |
| 2 | Upload **Hospital Logo** (PNG/JPG, max 5MB) |
| 3 | Enter **Hospital Name** (e.g., "Jackson F. Doe Memorial Regional Referral Hospital") |
| 4 | Enter **Contact Phone** |
| 5 | Enter **Contact Email** |
| 6 | Enter **Address** |
| 7 | Click **"Save Settings"** |

**What it affects:** Logo and name appear on all pages, invoices, and reports.

---

## 2. Departments

**URL:** `http://your-server/admin/departments/`
**Who:** Admin only

**Pre-seeded departments (20):**

| Code | Name |
|------|------|
| ER | Emergency Room |
| OPD | Outpatient Department |
| IPD | Inpatient Department |
| OBGYN | Obstetrics & Gynecology |
| PEDS | Pediatrics |
| SURG | Surgery |
| IM | Internal Medicine |
| LAB | Laboratory |
| RAD | Radiology |
| PHARM | Pharmacy |
| NURSE | Nursing Services |
| MRO | Medical Records |
| FIN | Finance |
| HR | Human Resources |
| ICT | ICT |
| PROC | Procurement |
| ADMIN | Administration |
| ICU | Intensive Care Unit |
| THEATRE | Theatre |
| MAT | Maternity Ward |

**To add a new department:**

| Step | Action |
|------|--------|
| 1 | Go to `/admin/departments/` |
| 2 | Click **"Add Department"** |
| 3 | Enter **Code** (e.g., "ONCO") — short unique code |
| 4 | Enter **Name** (e.g., "Oncology Department") |
| 5 | Enter **Description** (optional) |
| 6 | Click **"Save"** |

**To edit:** Click department name → edit fields → Save.

---

## 3. Users & Roles

### Users
**URL:** `http://your-server/admin/users/`
**Who:** Admin only

**Pre-seeded users (10):**

| Username | Password | Role | Department |
|----------|----------|------|------------|
| admin | admin123 | Administrator | Administration |
| doctor | doctor123 | Doctor | Internal Medicine |
| nurse | nurse123 | Nurse | Nursing Services |
| triage | triage123 | Triage Nurse | ER |
| pharmacist | pharm123 | Pharmacist | Pharmacy |
| cashier | cash123 | Cashier | Finance |
| labtech | lab123 | Lab Technician | Laboratory |
| obgyn | obgyn123 | OBGYN Specialist | OBGYN |
| surgeon | surg123 | General Surgeon | Surgery |
| inventory | inv123 | Inventory Manager | Procurement |

**To add a new user:**

| Step | Action |
|------|--------|
| 1 | Go to `/admin/users/` |
| 2 | Click **"Add User"** |
| 3 | Enter: Username, Password, First Name, Last Name, Email |
| 4 | Select: Department |
| 5 | Select: Job Title |
| 6 | Assign: Role(s) |
| 7 | Click **"Save"** |

### Roles
**URL:** `http://your-server/admin/roles/`
**Who:** Admin only

**Pre-seeded roles (15):**
ADMIN, MED_DIRECTOR, DOCTOR, NURSE, TRIAGE_NURSE, PHARMACIST, LAB_TECH, RADIOLOGIST, CASHIER, MRO, INV_MGR, NURSE_MGR, FIN_OFF, INT_AUDIT, SYS_ADMIN

**To add a new role:**

| Step | Action |
|------|--------|
| 1 | Go to `/admin/roles/` |
| 2 | Click **"Add Role"** |
| 3 | Enter **Code** (e.g., "WARD_NURSE") |
| 4 | Enter **Name** (e.g., "Ward Nurse") |
| 5 | Select **Permissions** (check boxes) |
| 6 | Click **"Save"** |

---

## 4. Triage Criteria (Auto-Suggestion Rules)

**URL:** `http://your-server/admin/triage-criteria/`
**Who:** Admin only

**Pre-seeded rules (12):**

| Rule | Vital Sign | Condition | → Acuity | → Dept |
|------|-----------|-----------|----------|--------|
| Severe Hypotension | Systolic BP | < 90 | 2 | ER |
| Hypertensive Crisis | Systolic BP | > 180 | 2 | ER |
| Severe Hypoxia | SpO2 | < 90 | 1 | ER |
| Mild Hypoxia | SpO2 | < 94 | 3 | ER |
| Severe Tachycardia | Heart Rate | > 120 | 3 | ER |
| Severe Bradycardia | Heart Rate | < 50 | 2 | ER |
| High Fever | Temperature | > 40 | 3 | OPD |
| Hypothermia | Temperature | < 35 | 2 | ER |
| Severe Tachypnea | Resp Rate | > 30 | 2 | ER |
| Hypoglycemia | Blood Glucose | < 60 | 2 | ER |
| Severe Hyperglycemia | Blood Glucose | > 400 | 2 | ER |
| Severe Pain | Pain Scale | ≥ 8 | 3 | OPD |

**To add a new rule:**

| Step | Action |
|------|--------|
| 1 | Go to `/admin/triage-criteria/` |
| 2 | Fill in **Rule Name** (e.g., "Severe Dehydration") |
| 3 | Select **Vital Sign** (e.g., "Blood Glucose") |
| 4 | Select **Operator** (e.g., "< less than") |
| 5 | Enter **Threshold** (e.g., "50") |
| 6 | Select **Suggested Acuity** (1-5) |
| 7 | Select **Suggested Department** (ER/OPD/IPD) |
| 8 | Enter **Priority** (lower = checked first) |
| 9 | Click **"Create Rule"** |

**To toggle rule:** Click "Activate/Deactivate" in the table.
**To delete:** Click "Delete" (requires confirmation).

---

## 5. Wards & Beds

**URL:** `http://your-server/clinical/ipd/`
**Who:** Doctor, Nurse, Admin

**Pre-seeded wards (6):**

| Ward | Beds |
|------|------|
| Medical Ward 1 | 9 beds |
| Medical Ward 2 | 6 beds |
| Surgical Ward 1 | 6 beds |
| ER Resuscitation | 6 beds |
| Maternity Ward | 7 beds |
| Intensive Care Unit | 6 beds |

**To add a new ward:**

| Step | Action |
|------|--------|
| 1 | Go to `/clinical/ipd/` |
| 2 | Click **"+ Add Ward"** button |
| 3 | Enter **Ward Name** (e.g., "Pediatric Ward") |
| 4 | Select **Department** (e.g., "PEDS") |
| 5 | Enter **Floor** (optional, e.g., "2nd Floor") |
| 6 | Enter **Capacity** (optional) |
| 7 | Click **"Save"** |

**To add a bed to a ward:**

| Step | Action |
|------|--------|
| 1 | Go to `/clinical/ipd/` |
| 2 | Click **"+ Add Bed"** button |
| 3 | Select **Ward** from dropdown |
| 4 | Enter **Room Number** (e.g., "201") |
| 5 | Enter **Bed Number** (e.g., "A") |
| 6 | Select **Bed Type** (Standard / ICU / Isolation / Maternity) |
| 7 | Click **"Save"** |

**To edit a ward:** Click ward name → edit → Save.
**To delete a ward:** Click ward → "Delete" (all beds removed too).
**To edit a bed:** Click bed → edit → Save.

---

## 6. Medications

**No UI form — API only.**

**Pre-seeded medications (20):**
Amoxicillin 500mg, Paracetamol 500mg, Metformin 500mg, Lisinopril 10mg, Amlodipine 5mg, Omeprazole 20mg, Salbutamol Inhaler, Ciprofloxacin 500mg, Azithromycin 500mg, Ibuprofen 400mg, Cetirizine 10mg, Prednisolone 5mg, Ferrous Sulphate 200mg, ORS Sachets, Insulin (Regular), Diazepam 5mg, Morphine 10mg, IV Normal Saline 1L, Ringer's Lactate 1L, Chlorhexidine 5%

**To add a medication via API:**

```bash
curl -X POST http://127.0.0.1:8000/api/pharmacy/medications/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Doxycycline",
    "strength": "100mg",
    "form": "Capsule",
    "category": "Antibiotic",
    "unit_price": "500"
  }'
```

**Or use Django admin:**
1. Go to `http://your-server/admin/pharmacy/medication/add/`
2. Fill: Name, Strength, Form, Category, Unit Price
3. Click **"Save"**

---

## 7. Inventory Management

### Stores
**URL:** `http://your-server/inventory/manage/` → **Stores** tab
**Who:** Admin, Inventory Manager

**Pre-seeded stores (5):**
Main Pharmacy, Ward Pharmacy, Laboratory Store, Central Warehouse, Surgical Supplies Store

**To add a store:**

| Step | Action |
|------|--------|
| 1 | Go to `/inventory/manage/` |
| 2 | Click **"Stores"** tab |
| 3 | Click **"+ Add Store"** |
| 4 | Enter **Name** (e.g., "Emergency Pharmacy") |
| 5 | Enter **Location** (optional) |
| 6 | Click **"Save"** |

### Categories
**URL:** `http://your-server/inventory/manage/` → **Categories** tab

**Pre-seeded categories (5):**
Medications, Consumables, Medical Equipment, Surgical Supplies, Laboratory Supplies

**To add a category:**

| Step | Action |
|------|--------|
| 1 | Go to `/inventory/manage/` |
| 2 | Click **"Categories"** tab |
| 3 | Click **"+ Add Category"** |
| 4 | Enter **Name** (e.g., "Wound Care") |
| 5 | Enter **Description** (optional) |
| 6 | Click **"Save"** |

### Items
**URL:** `http://your-server/inventory/manage/` → **Items** tab

**Pre-seeded items (64):** 20 medications + 20 consumables + 8 equipment + 8 surgical + 8 lab

**To add an item:**

| Step | Action |
|------|--------|
| 1 | Go to `/inventory/manage/` |
| 2 | Click **"Items"** tab |
| 3 | Click **"+ Add Item"** |
| 4 | Enter **Name** (e.g., "Gauze Bandage") |
| 5 | Select **Category** (e.g., "Consumables") |
| 6 | Select **Store** (e.g., "Main Pharmacy") |
| 7 | Enter **Unit** (e.g., "pack") |
| 8 | Enter **Unit Cost** (e.g., "200") |
| 9 | Enter **Reorder Level** (e.g., "50") |
| 10 | Click **"Save"** |

### Receive Stock
**URL:** `http://your-server/inventory/` → **"Receive Stock"** button

**To receive stock:**

| Step | Action |
|------|--------|
| 1 | Go to `/inventory/` |
| 2 | Click **"Receive Stock"** button |
| 3 | Select **Item** from dropdown |
| 4 | Enter **Quantity** received |
| 5 | Enter **Batch Number** (optional) |
| 6 | Enter **Expiry Date** (optional) |
| 7 | Click **"Receive"** |

---

## 8. Lab & Radiology Test Catalogues

**No UI form — API or Django Admin only.**

**Pre-seeded:** 20 lab tests + 20 radiology tests

**To add via Django Admin:**

| Step | Action |
|------|--------|
| 1 | Go to `http://your-server/admin/clinical/labtestcatalogue/add/` |
| 2 | Enter: Test Name, Code, Department, Cost |
| 3 | Click **"Save"** |

**To add via API:**

```bash
curl -X POST http://127.0.0.1:8000/api/clinical/lab-tests/ \
  -H "Content-Type: application/json" \
  -d '{"name": "HbA1c", "code": "LAB-HBA1C", "cost": "5000"}'
```

---

## 9. Service Items & Prices (Billing)

**No UI form — API or Django Admin only.**

**Pre-seeded:** 40 service items with prices for 3 payer categories (Self Pay, NHSLA, Other)

**Examples:**

| Service | Self Pay | NHSLA | Other |
|---------|----------|-------|-------|
| Consultation (OPD) | $500 | $300 | $400 |
| Lab Test (CBC) | $2,000 | $1,200 | $1,500 |
| X-Ray (Chest) | $3,000 | $1,800 | $2,200 |
| Surgery (Minor) | $15,000 | $9,000 | $11,000 |

**To add a service item via Django Admin:**

| Step | Action |
|------|--------|
| 1 | Go to `http://your-server/admin/billing/serviceitem/add/` |
| 2 | Enter: Name, Code, Category, Description |
| 3 | Click **"Save"** |
| 4 | Go to `http://your-server/admin/billing/serviceprice/add/` |
| 5 | Select: Service Item, Payer Category |
| 6 | Enter: Price |
| 7 | Click **"Save"** |
| 8 | Repeat for each payer category |

---

## 10. Price Lists

**No UI form — API or Django Admin only.**

**Pre-seeded:** 1 default price list

**To add via Django Admin:**

| Step | Action |
|------|--------|
| 1 | Go to `http://your-server/admin/billing/pricelist/add/` |
| 2 | Enter: Name (e.g., "Standard Pricing 2026") |
| 3 | Check **"Is Default"** if this is the main list |
| 4 | Click **"Save"** |

---

## Data Setup Order

For a new hospital deployment, add data in this order:

```
1. Hospital Settings (name, logo)
2. Departments
3. Users & Roles
4. Triage Criteria
5. Wards & Beds
6. Medications
7. Inventory Stores → Categories → Items → Stock
8. Lab/Radiology Test Catalogues
9. Price Lists → Service Items → Service Prices
10. Ready for patient flow!
```

---

## Quick Re-Seed (Development/Testing)

To reset ALL infrastructure data (keeps users, clears patients):

```bash
python manage.py pilot_reset
```

This takes ~5 seconds and gives you a clean slate with all seed data.

---

## Django Admin Access

For data types without UI forms, use Django's built-in admin:

**URL:** `http://your-server/admin/`
**Login:** `admin` / `admin123`

Available models:
- Pharmacy: Medications, Prescriptions, Prescription Items, Dispensing
- Billing: Invoices, Payments, Price Lists, Service Items, Service Prices
- Inventory: Stores, Categories, Items, Stock, Stock Movements
- Clinical: Lab Tests, Radiology Tests, Wards, Beds
- Audit: Audit Logs, Login Logs

---

**Document prepared for:** System Administrators
**Jackson F. Doe Memorial Regional Referral Hospital**
