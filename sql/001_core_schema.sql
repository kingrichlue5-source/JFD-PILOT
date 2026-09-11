-- =============================================================================
-- JFD Memorial Regional Referral Hospital - HMS Core Database Schema
-- PostgreSQL 14+ DDL Script
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. SCHEMA CREATION
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS users_auth;
CREATE SCHEMA IF NOT EXISTS patients;
CREATE SCHEMA IF NOT EXISTS clinical;
CREATE SCHEMA IF NOT EXISTS pharmacy;
CREATE SCHEMA IF NOT EXISTS billing;
CREATE SCHEMA IF NOT EXISTS inventory;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set search path
SET search_path TO users_auth, patients, clinical, pharmacy, billing, inventory, audit, public;

-- =============================================================================
-- 2. ENUM TYPES
-- =============================================================================

CREATE TYPE sync_status_enum AS ENUM ('local', 'synced');
CREATE TYPE gender_enum AS ENUM ('M', 'F', 'O', 'U');
CREATE TYPE blood_type_enum AS ENUM ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'UNKNOWN');
CREATE TYPE marital_status_enum AS ENUM ('single', 'married', 'divorced', 'widowed', 'separated', 'unknown');
CREATE TYPE patient_status_enum AS ENUM ('active', 'inactive', 'deceased', 'merged');
CREATE TYPE visit_status_enum AS ENUM ('scheduled', 'checked_in', 'in_progress', 'completed', 'cancelled', 'no_show');
CREATE TYPE encounter_type_enum AS ENUM ('opd', 'ipd', 'er', 'obgyn', 'anc', 'labor_delivery', 'postpartum', 'surgery', 'telemedicine');
CREATE TYPE order_status_enum AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'failed');
CREATE TYPE priority_enum AS ENUM ('routine', 'urgent', 'stat', 'asap');
CREATE TYPE payment_status_enum AS ENUM ('pending', 'partial', 'paid', 'refunded', 'voided');
CREATE TYPE payment_method_enum AS ENUM ('cash', 'bank_transfer', 'mobile_money', 'insurance', 'credit', 'other');
CREATE TYPE stock_movement_enum AS ENUM ('receipt', 'issue', 'transfer', 'adjustment', 'return', 'dispensed', 'expired', 'damaged');
CREATE TYPE user_status_enum AS ENUM ('active', 'inactive', 'locked', 'pending');
CREATE TYPE appointment_status_enum AS ENUM ('scheduled', 'confirmed', 'checked_in', 'completed', 'cancelled', 'no_show');
CREATE TYPE severity_enum AS ENUM ('critical', 'high', 'medium', 'low');
CREATE TYPE auth_status_enum AS ENUM ('pending', 'approved', 'denied', 'expired');
CREATE TYPE discharge_status_enum AS ENUM ('routine', 'against_medical_advice', 'referred', 'transferred', 'deceased');
CREATE TYPE delivery_type_enum AS ENUM ('vaginal', 'c_section', 'assisted', 'other');
CREATE TYPE transaction_type_enum AS ENUM ('charge', 'payment', 'refund', 'adjustment', 'write_off', 'exemption');

-- =============================================================================
-- 3. USERS_AUTH SCHEMA
-- =============================================================================

CREATE TABLE users_auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    department_id UUID,
    employee_id VARCHAR(50),
    job_title VARCHAR(100),
    status user_status_enum DEFAULT 'active',
    last_login TIMESTAMP WITH TIME ZONE,
    password_changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    profile_photo_url VARCHAR(500),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE users_auth.roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

CREATE TABLE users_auth.permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE users_auth.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users_auth.users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES users_auth.roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_by UUID,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(user_id, role_id)
);

CREATE TABLE users_auth.role_permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES users_auth.roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES users_auth.permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID,
    UNIQUE(role_id, permission_id)
);

CREATE TABLE users_auth.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users_auth.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE users_auth.departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_department_id UUID REFERENCES users_auth.departments(id),
    head_of_department_id UUID,
    is_clinical BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 4. PATIENTS SCHEMA
-- =============================================================================

CREATE TABLE patients.patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    mrn VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender gender_enum DEFAULT 'U',
    blood_type blood_type_enum DEFAULT 'UNKNOWN',
    marital_status marital_status_enum DEFAULT 'unknown',
    nationality VARCHAR(50),
    ethnicity VARCHAR(50),
    religion VARCHAR(50),
    occupation VARCHAR(100),
    education_level VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(255),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Liberia',
    postal_code VARCHAR(20),
    photo_url VARCHAR(500),
    identification_type VARCHAR(50),
    identification_number VARCHAR(100),
    next_of_kin_name VARCHAR(200),
    next_of_kin_phone VARCHAR(20),
    next_of_kin_relationship VARCHAR(50),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),
    insurance_provider VARCHAR(100),
    insurance_policy_number VARCHAR(100),
    insurance_group_number VARCHAR(100),
    insurance_expiry_date DATE,
    payer_category VARCHAR(50),
    credit_limit DECIMAL(12, 2) DEFAULT 0,
    status patient_status_enum DEFAULT 'active',
    merged_into_id UUID REFERENCES patients.patients(id),
    registered_by UUID,
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE patients.patient_allergies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id) ON DELETE CASCADE,
    allergen VARCHAR(200) NOT NULL,
    allergy_type VARCHAR(50),
    severity severity_enum DEFAULT 'medium',
    reaction TEXT,
    onset_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    recorded_by UUID,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE patients.patient_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    alert_text TEXT NOT NULL,
    severity severity_enum DEFAULT 'high',
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE patients.patient_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    description TEXT,
    uploaded_by UUID,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE patients.patient_consent (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id) ON DELETE CASCADE,
    consent_type VARCHAR(100) NOT NULL,
    consent_given BOOLEAN NOT NULL,
    consent_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expiry_date TIMESTAMP WITH TIME ZONE,
    witness_name VARCHAR(200),
    witness_signature_url VARCHAR(500),
    patient_signature_url VARCHAR(500),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- MRN Generation Sequence
CREATE SEQUENCE patients.mrn_sequence START WITH 1 INCREMENT BY 1;

-- =============================================================================
-- 5. CLINICAL SCHEMA
-- =============================================================================

CREATE TABLE clinical.visits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_number VARCHAR(20) UNIQUE NOT NULL,
    visit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    visit_type encounter_type_enum NOT NULL,
    department_id UUID REFERENCES users_auth.departments(id),
    status visit_status_enum DEFAULT 'scheduled',
    chief_complaint TEXT,
    triage_priority priority_enum,
    triage_notes TEXT,
    triage_time TIMESTAMP WITH TIME ZONE,
    check_in_time TIMESTAMP WITH TIME ZONE,
    check_out_time TIMESTAMP WITH TIME ZONE,
    provider_id UUID REFERENCES users_auth.users(id),
    attending_physician_id UUID REFERENCES users_auth.users(id),
    nurse_id UUID REFERENCES users_auth.users(id),
    appointment_id UUID,
    is_follow_up BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE clinical.triage_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    chief_complaint TEXT NOT NULL,
    acuity_level INTEGER CHECK (acuity_level BETWEEN 1 AND 5),
    temperature DECIMAL(5,2),
    heart_rate INTEGER,
    respiratory_rate INTEGER,
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    oxygen_saturation DECIMAL(5,2),
    weight DECIMAL(6,2),
    height DECIMAL(5,2),
    pain_scale INTEGER CHECK (pain_scale BETWEEN 0 AND 10),
    blood_glucose INTEGER,
    screening_notes TEXT,
    triage_nurse_id UUID REFERENCES users_auth.users(id),
    triage_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.encounters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    encounter_type encounter_type_enum NOT NULL,
    encounter_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    provider_id UUID REFERENCES users_auth.users(id),
    department_id UUID REFERENCES users_auth.departments(id),
    location VARCHAR(100),
    status order_status_enum DEFAULT 'in_progress',
    subjective TEXT,
    objective TEXT,
    assessment TEXT,
    plan TEXT,
    diagnosis_primary VARCHAR(100),
    diagnosis_secondary VARCHAR(100),
    diagnosis_notes TEXT,
    is_finalized BOOLEAN DEFAULT FALSE,
    finalized_at TIMESTAMP WITH TIME ZONE,
    signed_by UUID,
    signed_at TIMESTAMP WITH TIME ZONE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

CREATE TABLE clinical.vital_signs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    encounter_id UUID REFERENCES clinical.encounters(id),
    temperature DECIMAL(5,2),
    heart_rate INTEGER,
    respiratory_rate INTEGER,
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    oxygen_saturation DECIMAL(5,2),
    weight DECIMAL(6,2),
    height DECIMAL(5,2),
    bmi DECIMAL(5,2),
    pain_scale INTEGER CHECK (pain_scale BETWEEN 0 AND 10),
    blood_glucose INTEGER,
    recorded_by UUID REFERENCES users_auth.users(id),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.diagnoses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES clinical.encounters(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id),
    diagnosis_code VARCHAR(20),
    diagnosis_code_system VARCHAR(20) DEFAULT 'ICD-10',
    diagnosis_description TEXT NOT NULL,
    diagnosis_type VARCHAR(20) DEFAULT 'primary',
    is_principal BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',
    onset_date DATE,
    resolved_date DATE,
    notes TEXT,
    coded_by UUID,
    coded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    encounter_id UUID REFERENCES clinical.encounters(id),
    order_type VARCHAR(50) NOT NULL,
    order_description TEXT NOT NULL,
    priority priority_enum DEFAULT 'routine',
    status order_status_enum DEFAULT 'pending',
    ordering_provider_id UUID NOT NULL REFERENCES users_auth.users(id),
    ordered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    required_by TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancellation_reason TEXT,
    notes TEXT,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.progress_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES clinical.encounters(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id),
    note_type VARCHAR(50) DEFAULT 'progress',
    subjective TEXT,
    objective TEXT,
    assessment TEXT,
    plan TEXT,
    note_text TEXT NOT NULL,
    author_id UUID NOT NULL REFERENCES users_auth.users(id),
    authored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_signed BOOLEAN DEFAULT FALSE,
    signed_at TIMESTAMP WITH TIME ZONE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.nursing_notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    encounter_id UUID NOT NULL REFERENCES clinical.encounters(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id),
    note_type VARCHAR(50) DEFAULT 'nursing',
    note_text TEXT NOT NULL,
    interventions TEXT,
    patient_response TEXT,
    author_id UUID NOT NULL REFERENCES users_auth.users(id),
    authored_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- 6. CLINICAL - ADMISSIONS & BED MANAGEMENT
-- =============================================================================

CREATE TABLE clinical.wards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    department_id UUID REFERENCES users_auth.departments(id),
    ward_type VARCHAR(50),
    floor VARCHAR(20),
    capacity INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ward_id UUID NOT NULL REFERENCES clinical.wards(id),
    room_number VARCHAR(20) NOT NULL,
    room_type VARCHAR(50),
    capacity INTEGER DEFAULT 1,
    is_private BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ward_id, room_number)
);

CREATE TABLE clinical.beds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID NOT NULL REFERENCES clinical.rooms(id),
    bed_number VARCHAR(20) NOT NULL,
    bed_type VARCHAR(50) DEFAULT 'standard',
    is_occupied BOOLEAN DEFAULT FALSE,
    is_reserved BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(room_id, bed_number)
);

CREATE TABLE clinical.admissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id),
    admission_number VARCHAR(20) UNIQUE NOT NULL,
    admission_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    admission_type VARCHAR(50),
    admitting_diagnosis TEXT,
    admitting_provider_id UUID REFERENCES users_auth.users(id),
    ward_id UUID REFERENCES clinical.wards(id),
    room_id UUID REFERENCES clinical.rooms(id),
    bed_id UUID REFERENCES clinical.beds(id),
    expected_discharge_date DATE,
    actual_discharge_date TIMESTAMP WITH TIME ZONE,
    discharge_type discharge_status_enum,
    discharge_summary TEXT,
    discharge_provider_id UUID REFERENCES users_auth.users(id),
    status VARCHAR(20) DEFAULT 'active',
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID
);

CREATE TABLE clinical.admission_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admission_id UUID NOT NULL REFERENCES clinical.admissions(id),
    from_ward_id UUID REFERENCES clinical.wards(id),
    from_room_id UUID REFERENCES clinical.rooms(id),
    from_bed_id UUID REFERENCES clinical.beds(id),
    to_ward_id UUID NOT NULL REFERENCES clinical.wards(id),
    to_room_id UUID NOT NULL REFERENCES clinical.rooms(id),
    to_bed_id UUID NOT NULL REFERENCES clinical.beds(id),
    transfer_reason TEXT,
    transferred_by UUID REFERENCES users_auth.users(id),
    transferred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE clinical.patient_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_id UUID REFERENCES clinical.visits(id),
    admission_id UUID REFERENCES clinical.admissions(id),
    movement_type VARCHAR(50) NOT NULL,
    from_location VARCHAR(200),
    to_location VARCHAR(200),
    movement_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT,
    recorded_by UUID REFERENCES users_auth.users(id),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Visit sequence
CREATE SEQUENCE clinical.visit_sequence START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE clinical.admission_sequence START WITH 1 INCREMENT BY 1;

-- =============================================================================
-- 7. PHARMACY SCHEMA
-- =============================================================================

CREATE TABLE pharmacy.medications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    brand_name VARCHAR(200),
    medication_code VARCHAR(50),
    category VARCHAR(100),
    dosage_form VARCHAR(50),
    strength VARCHAR(100),
    unit VARCHAR(50),
    route VARCHAR(50),
    manufacturer VARCHAR(200),
    is_controlled BOOLEAN DEFAULT FALSE,
    controlled_schedule INTEGER,
    requires_prescription BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE pharmacy.prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    visit_id UUID NOT NULL REFERENCES clinical.visits(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    encounter_id UUID REFERENCES clinical.encounters(id),
    prescription_number VARCHAR(20) UNIQUE NOT NULL,
    prescribed_by UUID NOT NULL REFERENCES users_auth.users(id),
    prescribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status order_status_enum DEFAULT 'pending',
    notes TEXT,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE pharmacy.prescription_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prescription_id UUID NOT NULL REFERENCES pharmacy.prescriptions(id) ON DELETE CASCADE,
    medication_id UUID NOT NULL REFERENCES pharmacy.medications(id),
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(100),
    quantity_prescribed DECIMAL(10,2) NOT NULL,
    quantity_dispensed DECIMAL(10,2) DEFAULT 0,
    route VARCHAR(50),
    instructions TEXT,
    refills_allowed INTEGER DEFAULT 0,
    refills_used INTEGER DEFAULT 0,
    status order_status_enum DEFAULT 'pending',
    dispensed_by UUID REFERENCES users_auth.users(id),
    dispensed_at TIMESTAMP WITH TIME ZONE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE pharmacy.medication_dispensing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prescription_item_id UUID NOT NULL REFERENCES pharmacy.prescription_items(id),
    medication_id UUID NOT NULL REFERENCES pharmacy.medications(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    quantity_dispensed DECIMAL(10,2) NOT NULL,
    batch_lot_number VARCHAR(100),
    expiry_date DATE,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    dispensed_by UUID NOT NULL REFERENCES users_auth.users(id),
    dispensed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE pharmacy.prescription_sequence START WITH 1 INCREMENT BY 1;

-- =============================================================================
-- 8. BILLING SCHEMA
-- =============================================================================

CREATE TABLE billing.price_lists (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATE,
    expiry_date DATE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing.service_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    description TEXT,
    unit_of_measure VARCHAR(50),
    is_billable BOOLEAN DEFAULT TRUE,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing.service_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_item_id UUID NOT NULL REFERENCES billing.service_items(id),
    price_list_id UUID NOT NULL REFERENCES billing.price_lists(id),
    price DECIMAL(12, 2) NOT NULL,
    payer_category VARCHAR(50),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(service_item_id, price_list_id, payer_category, effective_date)
);

CREATE TABLE billing.invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(20) UNIQUE NOT NULL,
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    visit_id UUID REFERENCES clinical.visits(id),
    admission_id UUID REFERENCES clinical.admissions(id),
    invoice_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE,
    subtotal DECIMAL(12, 2) DEFAULT 0,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    total_amount DECIMAL(12, 2) DEFAULT 0,
    amount_paid DECIMAL(12, 2) DEFAULT 0,
    balance_due DECIMAL(12, 2) DEFAULT 0,
    status payment_status_enum DEFAULT 'pending',
    payer_type VARCHAR(50),
    insurance_authorization_number VARCHAR(100),
    notes TEXT,
    created_by UUID REFERENCES users_auth.users(id),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE billing.invoice_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id UUID NOT NULL REFERENCES billing.invoices(id) ON DELETE CASCADE,
    service_item_id UUID NOT NULL REFERENCES billing.service_items(id),
    description VARCHAR(200),
    quantity DECIMAL(10,2) DEFAULT 1,
    unit_price DECIMAL(12, 2) NOT NULL,
    discount_amount DECIMAL(12, 2) DEFAULT 0,
    tax_amount DECIMAL(12, 2) DEFAULT 0,
    total_amount DECIMAL(12, 2) NOT NULL,
    order_id UUID REFERENCES clinical.orders(id),
    prescription_item_id UUID REFERENCES pharmacy.prescription_items(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing.payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_number VARCHAR(20) UNIQUE NOT NULL,
    invoice_id UUID NOT NULL REFERENCES billing.invoices(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    amount DECIMAL(12, 2) NOT NULL,
    payment_method payment_method_enum NOT NULL,
    payment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reference_number VARCHAR(100),
    bank_name VARCHAR(100),
    check_number VARCHAR(50),
    mobile_money_number VARCHAR(50),
    insurance_claim_number VARCHAR(100),
    notes TEXT,
    received_by UUID REFERENCES users_auth.users(id),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_deleted BOOLEAN DEFAULT FALSE
);

CREATE TABLE billing.refunds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    refund_number VARCHAR(20) UNIQUE NOT NULL,
    payment_id UUID NOT NULL REFERENCES billing.payments(id),
    invoice_id UUID NOT NULL REFERENCES billing.invoices(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    amount DECIMAL(12, 2) NOT NULL,
    reason TEXT NOT NULL,
    refund_method payment_method_enum,
    refund_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_by UUID REFERENCES users_auth.users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    processed_by UUID REFERENCES users_auth.users(id),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing.credit_adjustments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    adjustment_number VARCHAR(20) UNIQUE NOT NULL,
    invoice_id UUID NOT NULL REFERENCES billing.invoices(id),
    patient_id UUID NOT NULL REFERENCES patients.patients(id),
    adjustment_type VARCHAR(50) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    reason TEXT NOT NULL,
    adjusted_by UUID REFERENCES users_auth.users(id),
    approved_by UUID REFERENCES users_auth.users(id),
    adjusted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE billing.cashier_shifts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shift_number VARCHAR(20) UNIQUE NOT NULL,
    cashier_id UUID NOT NULL REFERENCES users_auth.users(id),
    shift_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    shift_end TIMESTAMP WITH TIME ZONE,
    opening_balance DECIMAL(12, 2) DEFAULT 0,
    closing_balance DECIMAL(12, 2),
    total_cash DECIMAL(12, 2) DEFAULT 0,
    total_mobile_money DECIMAL(12, 2) DEFAULT 0,
    total_bank_transfer DECIMAL(12, 2) DEFAULT 0,
    total_insurance DECIMAL(12, 2) DEFAULT 0,
    total_credit DECIMAL(12, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'open',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE SEQUENCE billing.invoice_sequence START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE billing.payment_sequence START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE billing.refund_sequence START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE billing.adjustment_sequence START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE billing.cashier_shift_sequence START WITH 1 INCREMENT BY 1;

-- =============================================================================
-- 9. INVENTORY SCHEMA
-- =============================================================================

CREATE TABLE inventory.categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    parent_category_id UUID REFERENCES inventory.categories(id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory.items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    category_id UUID REFERENCES inventory.categories(id),
    description TEXT,
    unit_of_measure VARCHAR(50) NOT NULL,
    item_type VARCHAR(50),
    is_medication BOOLEAN DEFAULT FALSE,
    medication_id UUID REFERENCES pharmacy.medications(id),
    is_consumable BOOLEAN DEFAULT FALSE,
    is_equipment BOOLEAN DEFAULT FALSE,
    reorder_level INTEGER DEFAULT 0,
    reorder_quantity INTEGER DEFAULT 0,
    minimum_stock INTEGER DEFAULT 0,
    maximum_stock INTEGER DEFAULT 0,
    unit_cost DECIMAL(12, 2),
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory.stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    store_type VARCHAR(50),
    location VARCHAR(200),
    manager_id UUID REFERENCES users_auth.users(id),
    is_active BOOLEAN DEFAULT TRUE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory.stock (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES inventory.items(id),
    store_id UUID NOT NULL REFERENCES inventory.stores(id),
    batch_lot_number VARCHAR(100),
    expiry_date DATE,
    quantity_on_hand DECIMAL(12,2) DEFAULT 0,
    quantity_reserved DECIMAL(12,2) DEFAULT 0,
    quantity_available DECIMAL(12,2) GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    unit_cost DECIMAL(12,2),
    last_received_date DATE,
    last_issued_date DATE,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(item_id, store_id, batch_lot_number)
);

CREATE TABLE inventory.stock_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    movement_number VARCHAR(20) UNIQUE NOT NULL,
    item_id UUID NOT NULL REFERENCES inventory.items(id),
    store_id UUID NOT NULL REFERENCES inventory.stores(id),
    movement_type stock_movement_enum NOT NULL,
    quantity DECIMAL(12,2) NOT NULL,
    unit_cost DECIMAL(12,2),
    total_cost DECIMAL(12,2),
    batch_lot_number VARCHAR(100),
    expiry_date DATE,
    reference_type VARCHAR(50),
    reference_id UUID,
    from_store_id UUID REFERENCES inventory.stores(id),
    to_store_id UUID REFERENCES inventory.stores(id),
    notes TEXT,
    performed_by UUID REFERENCES users_auth.users(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory.stock_counts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    count_number VARCHAR(20) UNIQUE NOT NULL,
    store_id UUID NOT NULL REFERENCES inventory.stores(id),
    count_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) DEFAULT 'in_progress',
    conducted_by UUID REFERENCES users_auth.users(id),
    approved_by UUID REFERENCES users_auth.users(id),
    notes TEXT,
    sync_status sync_status_enum DEFAULT 'synced',
    last_modified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE inventory.stock_count_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stock_count_id UUID NOT NULL REFERENCES inventory.stock_counts(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES inventory.items(id),
    batch_lot_number VARCHAR(100),
    system_quantity DECIMAL(12,2),
    counted_quantity DECIMAL(12,2),
    variance DECIMAL(12,2) GENERATED ALWAYS AS (counted_quantity - system_quantity) STORED,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE SEQUENCE inventory.movement_sequence START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE inventory.stock_count_sequence START WITH 1 INCREMENT BY 1;

-- =============================================================================
-- 10. AUDIT SCHEMA
-- =============================================================================

CREATE TABLE audit.audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_name VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_id UUID,
    user_name VARCHAR(200),
    user_ip INET,
    user_agent TEXT,
    session_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE audit.login_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    username VARCHAR(100) NOT NULL,
    login_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    logout_at TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    failure_reason TEXT,
    session_id UUID
);

CREATE TABLE audit.data_access_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    schema_name VARCHAR(50) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID,
    access_type VARCHAR(20) NOT NULL,
    accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET
);

-- =============================================================================
-- 11. INDEXES
-- =============================================================================

-- Users indexes
CREATE INDEX idx_users_email ON users_auth.users(email);
CREATE INDEX idx_users_username ON users_auth.users(username);
CREATE INDEX idx_users_department ON users_auth.users(department_id);
CREATE INDEX idx_users_status ON users_auth.users(status);
CREATE INDEX idx_users_employee_id ON users_auth.users(employee_id);

-- Patients indexes
CREATE INDEX idx_patients_mrn ON patients.patients(mrn);
CREATE INDEX idx_patients_first_name ON patients.patients(first_name);
CREATE INDEX idx_patients_last_name ON patients.patients(last_name);
CREATE INDEX idx_patients_dob ON patients.patients(date_of_birth);
CREATE INDEX idx_patients_phone ON patients.patients(phone);
CREATE INDEX idx_patients_name_search ON patients.patients(last_name, first_name);
CREATE INDEX idx_patients_status ON patients.patients(status);
CREATE INDEX idx_patients_insurance ON patients.patients(insurance_provider);

-- Clinical indexes
CREATE INDEX idx_visits_patient ON clinical.visits(patient_id);
CREATE INDEX idx_visits_date ON clinical.visits(visit_date);
CREATE INDEX idx_visits_status ON clinical.visits(status);
CREATE INDEX idx_visits_department ON clinical.visits(department_id);
CREATE INDEX idx_visits_provider ON clinical.visits(provider_id);

CREATE INDEX idx_encounters_visit ON clinical.encounters(visit_id);
CREATE INDEX idx_encounters_patient ON clinical.encounters(patient_id);
CREATE INDEX idx_encounters_date ON clinical.encounters(encounter_date);

CREATE INDEX idx_diagnoses_encounter ON clinical.diagnoses(encounter_id);
CREATE INDEX idx_diagnoses_patient ON clinical.diagnoses(patient_id);
CREATE INDEX idx_diagnoses_code ON clinical.diagnoses(diagnosis_code);

CREATE INDEX idx_orders_visit ON clinical.orders(visit_id);
CREATE INDEX idx_orders_patient ON clinical.orders(patient_id);
CREATE INDEX idx_orders_status ON clinical.orders(status);
CREATE INDEX idx_orders_type ON clinical.orders(order_type);

CREATE INDEX idx_admissions_patient ON clinical.admissions(patient_id);
CREATE INDEX idx_admissions_ward ON clinical.admissions(ward_id);
CREATE INDEX idx_admissions_status ON clinical.admissions(status);

CREATE INDEX idx_beds_ward ON clinical.beds(room_id);
CREATE INDEX idx_beds_occupied ON clinical.beds(is_occupied);

-- Pharmacy indexes
CREATE INDEX idx_prescriptions_patient ON pharmacy.prescriptions(patient_id);
CREATE INDEX idx_prescriptions_visit ON pharmacy.prescriptions(visit_id);
CREATE INDEX idx_prescriptions_status ON pharmacy.prescriptions(status);

CREATE INDEX idx_prescription_items_prescription ON pharmacy.prescription_items(prescription_id);
CREATE INDEX idx_prescription_items_medication ON pharmacy.prescription_items(medication_id);

CREATE INDEX idx_dispensing_patient ON pharmacy.medication_dispensing(patient_id);
CREATE INDEX idx_dispensing_medication ON pharmacy.medication_dispensing(medication_id);

-- Billing indexes
CREATE INDEX idx_invoices_patient ON billing.invoices(patient_id);
CREATE INDEX idx_invoices_visit ON billing.invoices(visit_id);
CREATE INDEX idx_invoices_status ON billing.invoices(status);
CREATE INDEX idx_invoices_date ON billing.invoices(invoice_date);

CREATE INDEX idx_payments_invoice ON billing.payments(invoice_id);
CREATE INDEX idx_payments_patient ON billing.payments(patient_id);
CREATE INDEX idx_payments_date ON billing.payments(payment_date);
CREATE INDEX idx_payments_method ON billing.payments(payment_method);

-- Inventory indexes
CREATE INDEX idx_stock_item ON inventory.stock(item_id);
CREATE INDEX idx_stock_store ON inventory.stock(store_id);
CREATE INDEX idx_stock_batch ON inventory.stock(batch_lot_number);
CREATE INDEX idx_stock_expiry ON inventory.stock(expiry_date);

CREATE INDEX idx_movements_item ON inventory.stock_movements(item_id);
CREATE INDEX idx_movements_store ON inventory.stock_movements(store_id);
CREATE INDEX idx_movements_type ON inventory.stock_movements(movement_type);
CREATE INDEX idx_movements_date ON inventory.stock_movements(performed_at);

-- Audit indexes
CREATE INDEX idx_audit_schema ON audit.audit_logs(schema_name);
CREATE INDEX idx_audit_table ON audit.audit_logs(table_name);
CREATE INDEX idx_audit_record ON audit.audit_logs(record_id);
CREATE INDEX idx_audit_user ON audit.audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit.audit_logs(action);
CREATE INDEX idx_audit_created ON audit.audit_logs(created_at);

-- =============================================================================
-- 12. TRIGGER FUNCTIONS
-- =============================================================================

-- Function to update last_modified timestamp
CREATE OR REPLACE FUNCTION update_last_modified()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate MRN
CREATE OR REPLACE FUNCTION generate_mrn()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    year_part VARCHAR(4);
BEGIN
    year_part := TO_CHAR(NOW(), 'YYYY');
    next_val := nextval('patients.mrn_sequence');
    NEW.mrn := 'JFD-' || year_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate visit number
CREATE OR REPLACE FUNCTION generate_visit_number()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    date_part VARCHAR(8);
BEGIN
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    next_val := nextval('clinical.visit_sequence');
    NEW.visit_number := 'VIS-' || date_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate admission number
CREATE OR REPLACE FUNCTION generate_admission_number()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    date_part VARCHAR(8);
BEGIN
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    next_val := nextval('clinical.admission_sequence');
    NEW.admission_number := 'ADM-' || date_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate invoice number
CREATE OR REPLACE FUNCTION generate_invoice_number()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    date_part VARCHAR(8);
BEGIN
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    next_val := nextval('billing.invoice_sequence');
    NEW.invoice_number := 'INV-' || date_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate payment number
CREATE OR REPLACE FUNCTION generate_payment_number()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    date_part VARCHAR(8);
BEGIN
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    next_val := nextval('billing.payment_sequence');
    NEW.payment_number := 'PAY-' || date_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate prescription number
CREATE OR REPLACE FUNCTION generate_prescription_number()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    date_part VARCHAR(8);
BEGIN
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    next_val := nextval('pharmacy.prescription_sequence');
    NEW.prescription_number := 'RX-' || date_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate movement number
CREATE OR REPLACE FUNCTION generate_movement_number()
RETURNS TRIGGER AS $$
DECLARE
    next_val INTEGER;
    date_part VARCHAR(8);
BEGIN
    date_part := TO_CHAR(NOW(), 'YYYYMMDD');
    next_val := nextval('inventory.movement_sequence');
    NEW.movement_number := 'STM-' || date_part || '-' || LPAD(next_val::TEXT, 5, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    record_id UUID;
    user_id UUID;
    user_name VARCHAR(200);
BEGIN
    -- Get current user context (set by application)
    user_id := current_setting('app.current_user_id', TRUE)::UUID;
    user_name := current_setting('app.current_user_name', TRUE);

    IF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        record_id := OLD.id;
        INSERT INTO audit.audit_logs(
            schema_name, table_name, record_id, action,
            old_values, user_id, user_name, created_at
        ) VALUES (
            TG_TABLE_SCHEMA, TG_TABLE_NAME, record_id, 'DELETE',
            old_data, user_id, user_name, NOW()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        record_id := NEW.id;
        INSERT INTO audit.audit_logs(
            schema_name, table_name, record_id, action,
            old_values, new_values, user_id, user_name, created_at
        ) VALUES (
            TG_TABLE_SCHEMA, TG_TABLE_NAME, record_id, 'UPDATE',
            old_data, new_data, user_id, user_name, NOW()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        new_data := to_jsonb(NEW);
        record_id := NEW.id;
        INSERT INTO audit.audit_logs(
            schema_name, table_name, record_id, action,
            new_values, user_id, user_name, created_at
        ) VALUES (
            TG_TABLE_SCHEMA, TG_TABLE_NAME, record_id, 'INSERT',
            new_data, user_id, user_name, NOW()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Block deletion of financial transactions
CREATE OR REPLACE FUNCTION block_financial_deletion()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Deletion of financial transactions is not allowed. Use void/refund instead.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- 13. CREATE TRIGGERS
-- =============================================================================

-- MRN generation trigger
CREATE TRIGGER trigger_generate_mrn
    BEFORE INSERT ON patients.patients
    FOR EACH ROW
    EXECUTE FUNCTION generate_mrn();

-- Visit number generation trigger
CREATE TRIGGER trigger_generate_visit_number
    BEFORE INSERT ON clinical.visits
    FOR EACH ROW
    EXECUTE FUNCTION generate_visit_number();

-- Admission number generation trigger
CREATE TRIGGER trigger_generate_admission_number
    BEFORE INSERT ON clinical.admissions
    FOR EACH ROW
    EXECUTE FUNCTION generate_admission_number();

-- Invoice number generation trigger
CREATE TRIGGER trigger_generate_invoice_number
    BEFORE INSERT ON billing.invoices
    FOR EACH ROW
    EXECUTE FUNCTION generate_invoice_number();

-- Payment number generation trigger
CREATE TRIGGER trigger_generate_payment_number
    BEFORE INSERT ON billing.payments
    FOR EACH ROW
    EXECUTE FUNCTION generate_payment_number();

-- Prescription number generation trigger
CREATE TRIGGER trigger_generate_prescription_number
    BEFORE INSERT ON pharmacy.prescriptions
    FOR EACH ROW
    EXECUTE FUNCTION generate_prescription_number();

-- Movement number generation trigger
CREATE TRIGGER trigger_generate_movement_number
    BEFORE INSERT ON inventory.stock_movements
    FOR EACH ROW
    EXECUTE FUNCTION generate_movement_number();

-- Audit triggers for billing schema
CREATE TRIGGER audit_invoices
    AFTER INSERT OR UPDATE OR DELETE ON billing.invoices
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_payments
    AFTER INSERT OR UPDATE OR DELETE ON billing.payments
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_invoice_line_items
    AFTER INSERT OR UPDATE OR DELETE ON billing.invoice_line_items
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_refunds
    AFTER INSERT OR UPDATE OR DELETE ON billing.refunds
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_credit_adjustments
    AFTER INSERT OR UPDATE OR DELETE ON billing.credit_adjustments
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Audit triggers for clinical schema
CREATE TRIGGER audit_visits
    AFTER INSERT OR UPDATE OR DELETE ON clinical.visits
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_encounters
    AFTER INSERT OR UPDATE OR DELETE ON clinical.encounters
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_diagnoses
    AFTER INSERT OR UPDATE OR DELETE ON clinical.diagnoses
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_orders
    AFTER INSERT OR UPDATE OR DELETE ON clinical.orders
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_admissions
    AFTER INSERT OR UPDATE OR DELETE ON clinical.admissions
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Block deletion on financial tables
CREATE TRIGGER block_delete_invoices
    BEFORE DELETE ON billing.invoices
    FOR EACH ROW
    EXECUTE FUNCTION block_financial_deletion();

CREATE TRIGGER block_delete_payments
    BEFORE DELETE ON billing.payments
    FOR EACH ROW
    EXECUTE FUNCTION block_financial_deletion();

CREATE TRIGGER block_delete_invoice_line_items
    BEFORE DELETE ON billing.invoice_line_items
    FOR EACH ROW
    EXECUTE FUNCTION block_financial_deletion();

-- Last modified triggers
CREATE TRIGGER update_users_last_modified
    BEFORE UPDATE ON users_auth.users
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

CREATE TRIGGER update_patients_last_modified
    BEFORE UPDATE ON patients.patients
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

CREATE TRIGGER update_visits_last_modified
    BEFORE UPDATE ON clinical.visits
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

CREATE TRIGGER update_encounters_last_modified
    BEFORE UPDATE ON clinical.encounters
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

CREATE TRIGGER update_invoices_last_modified
    BEFORE UPDATE ON billing.invoices
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

CREATE TRIGGER update_payments_last_modified
    BEFORE UPDATE ON billing.payments
    FOR EACH ROW
    EXECUTE FUNCTION update_last_modified();

-- =============================================================================
-- 14. VIEWS
-- =============================================================================

-- Active patients view
CREATE OR REPLACE VIEW patients.active_patients AS
SELECT id, mrn, first_name, last_name, date_of_birth, gender, phone, email, status
FROM patients.patients
WHERE status = 'active' AND is_deleted = FALSE;

-- Bed occupancy view
CREATE OR REPLACE VIEW clinical.bed_occupancy AS
SELECT
    w.name AS ward_name,
    w.code AS ward_code,
    r.room_number,
    b.bed_number,
    b.bed_type,
    b.is_occupied,
    b.is_reserved,
    a.patient_id,
    p.mrn,
    p.first_name || ' ' || p.last_name AS patient_name,
    a.admission_date
FROM clinical.wards w
JOIN clinical.rooms r ON w.id = r.ward_id
JOIN clinical.beds b ON r.id = b.room_id
LEFT JOIN clinical.admissions a ON b.id = a.bed_id AND a.status = 'active'
LEFT JOIN patients.patients p ON a.patient_id = p.id
WHERE w.is_active = TRUE AND r.is_active = TRUE AND b.is_active = TRUE;

-- Daily revenue view
CREATE OR REPLACE VIEW billing.daily_revenue AS
SELECT
    payment_date::DATE AS payment_date,
    payment_method,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_amount
FROM billing.payments
WHERE is_deleted = FALSE
GROUP BY payment_date::DATE, payment_method
ORDER BY payment_date DESC;

-- Low stock alert view
CREATE OR REPLACE VIEW inventory.low_stock_items AS
SELECT
    i.id,
    i.name,
    i.code,
    i.unit_of_measure,
    s.store_id,
    st.name AS store_name,
    s.quantity_on_hand,
    i.reorder_level,
    CASE
        WHEN s.quantity_on_hand <= 0 THEN 'OUT_OF_STOCK'
        WHEN s.quantity_on_hand <= i.reorder_level THEN 'LOW_STOCK'
        ELSE 'OK'
    END AS stock_status
FROM inventory.stock s
JOIN inventory.items i ON s.item_id = i.id
JOIN inventory.stores st ON s.store_id = st.id
WHERE i.is_active = TRUE
    AND (s.quantity_on_hand <= i.reorder_level OR s.quantity_on_hand <= 0)
ORDER BY s.quantity_on_hand ASC;

-- Expiring medications view
CREATE OR REPLACE VIEW pharmacy.expiring_medications AS
SELECT
    m.id,
    m.name,
    m.generic_name,
    s.batch_lot_number,
    s.expiry_date,
    s.quantity_on_hand,
    st.name AS store_name,
    s.expiry_date - CURRENT_DATE AS days_until_expiry
FROM pharmacy.medications m
JOIN inventory.stock s ON m.id = s.medication_id
JOIN inventory.stores st ON s.store_id = st.id
WHERE s.expiry_date IS NOT NULL
    AND s.expiry_date <= CURRENT_DATE + INTERVAL '90 days'
    AND s.quantity_on_hand > 0
ORDER BY s.expiry_date ASC;

-- =============================================================================
-- 15. SEED DATA - DEFAULT ROLES
-- =============================================================================

INSERT INTO users_auth.roles (name, code, description, is_system_role) VALUES
('Administrator', 'ADMIN', 'Full system administrator access', TRUE),
('Medical Director', 'MED_DIRECTOR', 'Medical director with full clinical access', TRUE),
('Doctor', 'DOCTOR', 'Physician with clinical documentation access', TRUE),
('Nurse', 'NURSE', 'Nursing staff with patient care access', TRUE),
('Triage Nurse', 'TRIAGE_NURSE', 'Triage nurse with triage-specific access', TRUE),
('Pharmacist', 'PHARMACIST', 'Pharmacy staff with medication management access', TRUE),
('Laboratory Technician', 'LAB_TECH', 'Laboratory staff with diagnostic access', TRUE),
('Radiologist', 'RADIOLOGIST', 'Radiology staff with imaging access', TRUE),
('Cashier', 'CASHIER', 'Billing and payment processing access', TRUE),
('Medical Records Officer', 'MRO', 'Medical records and HMIS reporting access', TRUE),
('Inventory Manager', 'INV_MGR', 'Inventory and supply chain management access', TRUE),
('Nurse Manager', 'NURSE_MGR', 'Nursing management with supervisory access', TRUE),
('Finance Officer', 'FIN_OFF', 'Financial oversight and reporting access', TRUE),
('Internal Auditor', 'INT_AUDIT', 'Audit and compliance access', TRUE),
('System Administrator', 'SYS_ADMIN', 'Technical system administration access', TRUE);

-- Default permissions
INSERT INTO users_auth.permissions (name, code, description, category) VALUES
-- Patient permissions
('View Patients', 'PATIENT_VIEW', 'View patient records', 'Patient'),
('Create Patients', 'PATIENT_CREATE', 'Create new patient records', 'Patient'),
('Edit Patients', 'PATIENT_EDIT', 'Edit patient information', 'Patient'),
('Merge Patients', 'PATIENT_MERGE', 'Merge duplicate patient records', 'Patient'),
-- Clinical permissions
('View Encounters', 'ENCOUNTER_VIEW', 'View clinical encounters', 'Clinical'),
('Create Encounters', 'ENCOUNTER_CREATE', 'Create clinical encounters', 'Clinical'),
('Edit Encounters', 'ENCOUNTER_EDIT', 'Edit clinical encounters', 'Clinical'),
('Sign Encounters', 'ENCOUNTER_SIGN', 'Sign and finalize encounters', 'Clinical'),
-- Orders permissions
('View Orders', 'ORDER_VIEW', 'View clinical orders', 'Orders'),
('Create Orders', 'ORDER_CREATE', 'Create clinical orders', 'Orders'),
('Cancel Orders', 'ORDER_CANCEL', 'Cancel clinical orders', 'Orders'),
-- Pharmacy permissions
('View Prescriptions', 'RX_VIEW', 'View prescriptions', 'Pharmacy'),
('Create Prescriptions', 'RX_CREATE', 'Create prescriptions', 'Pharmacy'),
('Dispense Medications', 'RX_DISPENSE', 'Dispense medications', 'Pharmacy'),
-- Billing permissions
('View Invoices', 'INVOICE_VIEW', 'View invoices', 'Billing'),
('Create Invoices', 'INVOICE_CREATE', 'Create invoices', 'Billing'),
('Process Payments', 'PAYMENT_PROCESS', 'Process payments', 'Billing'),
('Issue Refunds', 'REFUND_ISSUE', 'Issue refunds', 'Billing'),
('Void Transactions', 'TRANSACTION_VOID', 'Void financial transactions', 'Billing'),
-- Inventory permissions
('View Inventory', 'INVENTORY_VIEW', 'View inventory', 'Inventory'),
('Manage Inventory', 'INVENTORY_MANAGE', 'Manage inventory items', 'Inventory'),
('Process Stock Movements', 'STOCK_MOVE', 'Process stock movements', 'Inventory'),
-- Reports permissions
('View Reports', 'REPORT_VIEW', 'View reports', 'Reports'),
('Generate Reports', 'REPORT_GENERATE', 'Generate reports', 'Reports'),
('Export Reports', 'REPORT_EXPORT', 'Export reports', 'Reports'),
-- Admin permissions
('Manage Users', 'USER_MANAGE', 'Manage user accounts', 'Admin'),
('Manage Roles', 'ROLE_MANAGE', 'Manage roles and permissions', 'Admin'),
('View Audit Logs', 'AUDIT_VIEW', 'View audit logs', 'Admin'),
('System Configuration', 'SYS_CONFIG', 'Configure system settings', 'Admin');

-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
