const API = {
    baseURL: '/api',

    async request(method, endpoint, data = null) {
        const config = {
            method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCSRFToken() },
            credentials: 'same-origin'
        };
        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, config);
            if (response.status === 204) return null;
            const contentType = response.headers.get('content-type') || '';
            if (!contentType.includes('application/json')) {
                const text = await response.text();
                throw new Error(`Server returned ${response.status} instead of JSON. ${text.substring(0, 200)}`);
            }
            const result = await response.json();
            if (!response.ok) {
                const errorMsg = result.detail || result.error || Object.values(result).flat().join(', ') || 'Request failed';
                throw new Error(errorMsg);
            }
            return result;
        } catch (err) {
            if (err.message === 'Failed to fetch') {
                throw new Error('Network error. Please check your connection.');
            }
            throw err;
        }
    },

    getCSRFToken() {
        const name = 'csrftoken';
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name + '=')) {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        return '';
    },

    get(endpoint) { return this.request('GET', endpoint); },
    post(endpoint, data) { return this.request('POST', endpoint, data); },
    patch(endpoint, data) { return this.request('PATCH', endpoint, data); },
    put(endpoint, data) { return this.request('PUT', endpoint, data); },
    delete(endpoint) { return this.request('DELETE', endpoint); },

    // ==================== PATIENTS ====================
    searchPatients(query) { return this.get(`/patients/search/?q=${encodeURIComponent(query)}`); },
    getPatients(params = '') { return this.get(`/patients/${params}`); },
    getPatient(id) { return this.get(`/patients/${id}/`); },
    createPatient(data) { return this.post('/patients/', data); },
    registerWalkIn(data) { return this.post('/patients/register/', data); },
    updatePatient(id, data) { return this.patch(`/patients/${id}/`, data); },
    getPatientAllergies(patientId) { return this.get(`/patients/${patientId}/allergies/`); },

    // ==================== CLINICAL - VISITS & TRIAGE ====================
    getTriageQueue() { return this.get('/clinical/triage-queue/'); },
    submitTriage(visitId, data) { return this.post(`/clinical/visits/${visitId}/triage/submit/`, data); },
    getVisits(params = '') { return this.get(`/clinical/visits/${params}`); },
    getVisit(id) { return this.get(`/clinical/visits/${id}/`); },
    createVisit(data) { return this.post('/clinical/visits/', data); },
    updateVisitStatus(visitId, status) { return this.patch(`/clinical/visits/${visitId}/status/`, { status }); },
    getTriageRecords(visitId) { return this.get(`/clinical/visits/${visitId}/triage/`); },

    // ==================== CLINICAL - ENCOUNTERS ====================
    getEncounters(visitId) { return this.get(`/clinical/visits/${visitId}/encounters/`); },
    createEncounter(visitId, data) { return this.post(`/clinical/visits/${visitId}/encounters/`, data); },
    getEncounter(id) { return this.get(`/clinical/encounters/${id}/`); },
    finalizeEncounter(encounterId) { return this.post(`/clinical/encounters/${encounterId}/finalize/`); },

    // ==================== CLINICAL - VITALS ====================
    getVitals(visitId) { return this.get(`/clinical/visits/${visitId}/vitals/`); },
    createVitals(visitId, data) { return this.post(`/clinical/visits/${visitId}/vitals/`, data); },

    // ==================== CLINICAL - DIAGNOSIS ====================
    getDiagnoses(encounterId) { return this.get(`/clinical/encounters/${encounterId}/diagnoses/`); },
    createDiagnosis(encounterId, data) { return this.post(`/clinical/encounters/${encounterId}/diagnoses/`, data); },
    getICDLookup(query = '') { return this.get(`/clinical/icd-lookup/${query ? '?q=' + encodeURIComponent(query) : ''}`); },

    // ==================== CLINICAL - ORDERS ====================
    getOrders(visitId) { return this.get(`/clinical/visits/${visitId}/orders/`); },
    placeOrder(visitId, data) { return this.post(`/clinical/visits/${visitId}/place-order/`, data); },
    getAllOrders() { return this.get('/clinical/orders/'); },
    updateOrder(id, data) { return this.patch(`/clinical/orders/${id}/`, data); },

    // ==================== CLINICAL - LAB & RADIOLOGY ====================
    getLabTestCatalogue() { return this.get('/clinical/lab-tests/'); },
    getRadiologyTestCatalogue() { return this.get('/clinical/radiology-tests/'); },
    getAllOrders(params = '') { return this.get(`/clinical/orders/${params}`); },
    getOrdersByType(type, params = '') { return this.get(`/clinical/orders/?type=${type}${params}`); },

    // ==================== CLINICAL - NOTES ====================
    getProgressNotes(encounterId) { return this.get(`/clinical/encounters/${encounterId}/notes/`); },
    createProgressNote(encounterId, data) { return this.post(`/clinical/encounters/${encounterId}/notes/`, data); },

    // ==================== CLINICAL - DIAGNOSTIC RESULTS ====================
    getDiagnosticResults(visitId) { return this.get(`/clinical/visits/${visitId}/diagnostic-results/`); },
    createDiagnosticResult(data) { return this.post('/clinical/diagnostic-results/', data); },
    getDiagnosticResult(id) { return this.get(`/clinical/diagnostic-results/${id}/`); },
    updateDiagnosticResult(id, data) { return this.patch(`/clinical/diagnostic-results/${id}/`, data); },

    // ==================== CLINICAL - ADMISSIONS & BEDS ====================
    getAdmissions(params = '') { return this.get(`/clinical/admissions/${params}`); },
    getAdmission(id) { return this.get(`/clinical/admissions/${id}/`); },
    createAdmission(data) { return this.post('/clinical/admissions/', data); },
    dischargePatient(admissionId, data) { return this.post(`/clinical/admissions/${admissionId}/discharge/`, data); },
    getBeds(params = '') { return this.get(`/clinical/beds/${params}`); },
    getSurgicalBeds() { return this.get('/clinical/beds/?ward_type=surgical'); },
    getMaternityBeds() { return this.get('/clinical/beds/?ward_type=maternity'); },
    getWards() { return this.get('/clinical/wards/'); },
    getBedOccupancy(wardId = '') {
        const params = wardId ? `?ward=${wardId}` : '';
        return this.get(`/clinical/bed-occupancy/${params}`);
    },

    // ==================== CLINICAL - OBGYN ====================
    getAntenatalVisits(params = '') { return this.get(`/clinical/antenatal/${params}`); },
    createAntenatalVisit(data) { return this.post('/clinical/antenatal/', data); },
    updateAntenatalVisit(id, data) { return this.patch(`/clinical/antenatal/${id}/`, data); },
    getLaborRecords(params = '') { return this.get(`/clinical/labor/${params}`); },
    createLaborRecord(data) { return this.post('/clinical/labor/', data); },
    updateLaborRecord(id, data) { return this.patch(`/clinical/labor/${id}/`, data); },
    getDeliveryRecords(params = '') { return this.get(`/clinical/delivery/${params}`); },
    createDeliveryRecord(data) { return this.post('/clinical/delivery/', data); },
    createBirthRecord(data) { return this.post('/clinical/birth/', data); },
    getPostnatalVisits(params = '') { return this.get(`/clinical/postnatal/${params}`); },
    createPostnatalVisit(data) { return this.post('/clinical/postnatal/', data); },
    updatePostnatalVisit(id, data) { return this.patch(`/clinical/postnatal/${id}/`, data); },

    // ==================== CLINICAL - SURGERY ====================
    getSurgicalCases(params = '') { return this.get(`/clinical/surgical/${params}`); },
    createSurgicalCase(data) { return this.post('/clinical/surgical/', data); },
    updateSurgicalCase(id, data) { return this.patch(`/clinical/surgical/${id}/`, data); },

    // ==================== CLINICAL - CATALOGUES ====================
    getLabTests() { return this.get('/clinical/lab-tests/'); },
    getRadiologyTests() { return this.get('/clinical/radiology-tests/'); },

    // ==================== CLINICAL - REFERRALS ====================
    getReferrals(params = '') { return this.get(`/clinical/referrals/${params}`); },
    createReferral(data) { return this.post('/clinical/referrals/', data); },

    // ==================== CLINICAL - APPOINTMENTS ====================
    getAppointments(params = '') { return this.get(`/clinical/appointments/${params}`); },
    createAppointment(data) { return this.post('/clinical/appointments/', data); },
    updateAppointment(id, data) { return this.patch(`/clinical/appointments/${id}/`, data); },

    // ==================== PHARMACY ====================
    getMedications(params = '') { return this.get(`/pharmacy/medications/${params}`); },
    getPrescriptions(params = '') { return this.get(`/pharmacy/prescriptions/${params}`); },
    getPrescription(id) { return this.get(`/pharmacy/prescriptions/${id}/`); },
    createPrescription(data) { return this.post('/pharmacy/prescriptions/', data); },
    getPrescriptionItems(rxId) { return this.get(`/pharmacy/prescriptions/${rxId}/items/`); },
    dispenseMedication(data) { return this.post('/pharmacy/dispense/', data); },
    getDispensingRecords(params = '') { return this.get(`/pharmacy/dispensing/${params}`); },

    // ==================== BILLING ====================
    getInvoices(params = '') { return this.get(`/billing/invoices/${params}`); },
    getInvoice(id) { return this.get(`/billing/invoices/${id}/`); },
    processPayment(data) { return this.post('/billing/pay/', data); },
    getCashierShifts(params = '') { return this.get(`/billing/cashier-shifts/${params}`); },
    closeCashierShift(shiftId, data) { return this.post(`/billing/cashier-shifts/${shiftId}/close/`, data || {}); },
    getDailyRevenue() { return this.get('/billing/daily-revenue/'); },
    getRevenueSummary() { return this.get('/billing/revenue-summary/'); },
    postCharge(data) { return this.post('/billing/post-charge/', data); },

    // ==================== INVENTORY ====================
    getStock(params = '') { return this.get(`/inventory/stock/${params}`); },
    receiveStock(data) { return this.post('/inventory/receive/', data); },
    transferStock(data) { return this.post('/inventory/transfer/', data); },
    getItems(params = '') { return this.get(`/inventory/items/${params}`); },
    getCategories() { return this.get('/inventory/categories/'); },
    getLowStock() { return this.get('/inventory/low-stock/'); },
    getStockSummary() { return this.get('/inventory/stock-summary/'); },
    getStores() { return this.get('/inventory/stores/'); },

    // ==================== REPORTS ====================
    getHMISSummary(params = '') { return this.get(`/reports/hmis/${params}`); },
    getDHIS2Export() { return this.get('/reports/hmis/dhis2/'); },
    getTopDiagnoses() { return this.get('/reports/diagnoses/top/'); },
    getMonthlyRevenue() { return this.get('/reports/revenue/monthly/'); },
    getPatientDemographics() { return this.get('/reports/patients/demographics/'); },
    getDepartmentUtilization() { return this.get('/reports/departments/utilization/'); },

    // ==================== USERS & AUTH ====================
    getDepartments() { return this.get('/auth/departments/'); },
    getUsers(params = '') { return this.get(`/auth/users/${params}`); },
    getRoles() { return this.get('/auth/roles/'); },
    getProfile() { return this.get('/auth/profile/'); },

    // ==================== PATIENT EMR (aggregated) ====================
    getPatientVisits(patientId, params = '') { return this.get(`/clinical/visits/?patient=${patientId}${params}`); },
    getPatientAdmissions(patientId, params = '') { return this.get(`/clinical/admissions/?patient=${patientId}${params}`); },
    getPatientAlerts(patientId) { return this.get(`/patients/${patientId}/allergies/`); },

    // ==================== AUDIT ====================
    getAuditLogs(params = '') { return this.get(`/audit/logs/${params}`); },
};
