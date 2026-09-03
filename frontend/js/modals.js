/* ============================================================
   MODALS.JS — appointment CRUD modals, user modal, confirm
   ============================================================ */

let _confirmCallback = null;

/* ---- Open / close ---- */
function openModal(id)  { document.getElementById(id).style.display = "flex"; }
function closeModal(id) { document.getElementById(id).style.display = "none"; }

document.addEventListener("click", e => {
  const btn = e.target.closest("[data-modal]");
  if (btn) closeModal(btn.dataset.modal);
  if (e.target.classList.contains("modal-overlay")) closeModal(e.target.id);
});

document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-overlay").forEach(m => {
      if (m.style.display !== "none") closeModal(m.id);
    });
  }
});

/* ============================================================
   CONFIRM MODAL
   ============================================================ */
function showConfirm(message, onConfirm) {
  document.getElementById("confirmMsg").textContent = message;
  _confirmCallback = onConfirm;
  openModal("confirmModal");
}

document.getElementById("confirmDeleteBtn").addEventListener("click", () => {
  closeModal("confirmModal");
  if (_confirmCallback) { _confirmCallback(); _confirmCallback = null; }
});

/* ============================================================
   APPOINTMENT MODAL
   ============================================================ */
let _apptEditId = null;

async function openApptModal(apptData = null) {
  _apptEditId = apptData?.id || null;
  document.getElementById("apptModalTitle").textContent = apptData ? "Edit Appointment" : "Add Appointment";
  document.getElementById("apptModalError").textContent = "";
  document.getElementById("apptForm").reset();
  document.getElementById("apptId").value = "";

  // Populate departments dropdown
  const depts = await ApiDepts.list().catch(() => []);
  const deptSel = document.getElementById("apptDeptId");
  deptSel.innerHTML = '<option value="">Select department...</option>';
  depts.forEach(d => deptSel.append(Object.assign(document.createElement("option"), { value: d.id, textContent: d.name })));

  // Populate patients dropdown
  const patients = await ApiPatients.list().catch(() => []);
  const patSel = document.getElementById("apptPatientId");
  patSel.innerHTML = '<option value="">Select patient...</option>';
  patients.forEach(p => patSel.append(Object.assign(document.createElement("option"), { value: p.id, textContent: `${p.full_name} (${p.patient_code})` })));

  // Dept→Doctor cascade
  deptSel.onchange = async () => {
    const dId = deptSel.value;
    const doctors = await ApiDepts.doctors(dId || null).catch(() => []);
    const docSel = document.getElementById("apptDoctorId");
    docSel.innerHTML = '<option value="">Select doctor...</option>';
    doctors.forEach(d => docSel.append(Object.assign(document.createElement("option"), { value: d.id, textContent: d.name })));
  };

  // Pre-fill if editing
  if (apptData) {
    document.getElementById("apptId").value          = apptData.id;
    document.getElementById("apptDate").value        = apptData.appointment_date;
    document.getElementById("apptTime").value        = apptData.time_slot || "";
    document.getElementById("apptStatus").value      = apptData.status;
    document.getElementById("apptLeadDays").value    = apptData.lead_days;
    document.getElementById("apptPrevNS").value      = apptData.previous_no_shows;
    document.getElementById("apptWait").value        = apptData.wait_minutes;
    document.getElementById("apptSms").checked       = apptData.sms_received;
    document.getElementById("apptNotes").value       = apptData.notes || "";

    // Set dept then trigger cascade then set doctor
    deptSel.value = apptData.department_id;
    await deptSel.onchange();
    document.getElementById("apptDoctorId").value  = apptData.doctor_id;
    document.getElementById("apptPatientId").value = apptData.patient_id;
  } else {
    // Pre-load doctors for first dept
    if (depts.length) {
      deptSel.value = depts[0].id;
      await deptSel.onchange();
    }
  }

  openModal("apptModal");
}

document.getElementById("apptForm").addEventListener("submit", async e => {
  e.preventDefault();
  const errEl = document.getElementById("apptModalError");
  errEl.textContent = "";
  const saveBtn = document.getElementById("apptSaveBtn");
  const saveTxt = document.getElementById("apptSaveTxt");
  const spinner = document.getElementById("apptSaveSpinner");
  saveBtn.disabled = true;
  saveTxt.style.display = "none";
  spinner.style.display = "inline-block";

  const body = {
    patient_id:       parseInt(document.getElementById("apptPatientId").value),
    department_id:    parseInt(document.getElementById("apptDeptId").value),
    doctor_id:        parseInt(document.getElementById("apptDoctorId").value),
    appointment_date: document.getElementById("apptDate").value,
    time_slot:        document.getElementById("apptTime").value || null,
    status:           document.getElementById("apptStatus").value,
    lead_days:        parseInt(document.getElementById("apptLeadDays").value) || 0,
    previous_no_shows:parseInt(document.getElementById("apptPrevNS").value) || 0,
    wait_minutes:     parseInt(document.getElementById("apptWait").value) || 0,
    sms_received:     document.getElementById("apptSms").checked,
    notes:            document.getElementById("apptNotes").value || null,
  };

  try {
    if (_apptEditId) {
      await ApiAppointments.update(_apptEditId, body);
      showToast("Appointment updated", "success");
    } else {
      await ApiAppointments.create(body);
      showToast("Appointment created", "success");
    }
    closeModal("apptModal");
    if (window.refreshApptTable) window.refreshApptTable();
    if (window.renderPage && window.currentPage === "dashboard") window.renderPage("dashboard");
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    saveBtn.disabled = false;
    saveTxt.style.display = "inline";
    spinner.style.display = "none";
  }
});

document.getElementById("btnAddAppt")?.addEventListener("click", () => openApptModal());

/* ============================================================
   USER MODAL
   ============================================================ */
let _userEditId = null;

async function openUserModal(userData = null) {
  _userEditId = userData?.id || null;
  document.getElementById("userModalTitle").textContent = userData ? "Edit User" : "Add User";
  document.getElementById("userModalError").textContent = "";
  document.getElementById("userForm").reset();
  document.getElementById("userId").value = "";

  if (userData) {
    document.getElementById("userId").value      = userData.id;
    document.getElementById("userFullName").value = userData.full_name;
    document.getElementById("userEmail").value   = userData.email;
    document.getElementById("userRole").value    = userData.role;
    document.getElementById("userPassword").placeholder = "Leave blank to keep current";
    document.getElementById("userPassword").required = false;
  } else {
    document.getElementById("userPassword").required = true;
  }

  openModal("userModal");
}

document.getElementById("userForm").addEventListener("submit", async e => {
  e.preventDefault();
  const errEl = document.getElementById("userModalError");
  errEl.textContent = "";

  const body = {
    full_name: document.getElementById("userFullName").value,
    email:     document.getElementById("userEmail").value,
    role:      document.getElementById("userRole").value,
  };
  const pw = document.getElementById("userPassword").value;
  if (pw) body.password = pw;

  try {
    if (_userEditId) {
      await ApiAuth.updateUser(_userEditId, body);
      showToast("User updated", "success");
    } else {
      if (!pw) { errEl.textContent = "Password is required"; return; }
      await ApiAuth.createUser(body);
      showToast("User created", "success");
    }
    closeModal("userModal");
    if (window.loadUsersTable) window.loadUsersTable();
  } catch (err) {
    errEl.textContent = err.message;
  }
});

document.getElementById("btnAddUser")?.addEventListener("click", () => openUserModal());

window.openApptModal = openApptModal;
window.openUserModal = openUserModal;
window.showConfirm   = showConfirm;
window.openModal     = openModal;
window.closeModal    = closeModal;
