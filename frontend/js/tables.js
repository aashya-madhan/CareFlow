/* ============================================================
   TABLES.JS — Live tables driven by API data
   ============================================================ */

function statusBadge(s) {
  const map = {
    "Showed":    '<span class="badge-status badge-showed"><i class="fa-solid fa-circle-check"></i> Showed</span>',
    "No-Show":   '<span class="badge-status badge-noshow"><i class="fa-solid fa-circle-xmark"></i> No-Show</span>',
    "Cancelled": '<span class="badge-status badge-cancelled"><i class="fa-solid fa-circle-minus"></i> Cancelled</span>',
    "Scheduled": '<span class="badge-status badge-scheduled"><i class="fa-solid fa-clock"></i> Scheduled</span>',
  };
  return map[s] || s;
}

function riskPill(label, score) {
  const cls = { High: "risk-high", Medium: "risk-medium", Low: "risk-low" }[label] || "risk-low";
  return `<span class="risk-pill ${cls}">${label} (${score})</span>`;
}

function smsIcon(v) {
  return v
    ? '<span style="color:var(--green)"><i class="fa-solid fa-check"></i></span>'
    : '<span style="color:var(--red)"><i class="fa-solid fa-xmark"></i></span>';
}

function renderPagination(containerId, currentPage, totalPages, onPage) {
  const c = document.getElementById(containerId);
  if (!c) return;
  c.innerHTML = "";

  const prev = Object.assign(document.createElement("button"), { className: "page-btn", innerHTML: '<i class="fa-solid fa-chevron-left"></i>' });
  prev.disabled = currentPage <= 1;
  prev.onclick  = () => onPage(currentPage - 1);
  c.appendChild(prev);

  const start = Math.max(1, currentPage - 2);
  const end   = Math.min(totalPages, start + 4);
  for (let i = start; i <= end; i++) {
    const btn = Object.assign(document.createElement("button"), { className: `page-btn${i === currentPage ? " active" : ""}`, textContent: i });
    const p = i;
    btn.onclick = () => onPage(p);
    c.appendChild(btn);
  }

  const next = Object.assign(document.createElement("button"), { className: "page-btn", innerHTML: '<i class="fa-solid fa-chevron-right"></i>' });
  next.disabled = currentPage >= totalPages;
  next.onclick  = () => onPage(currentPage + 1);
  c.appendChild(next);
}

/* ============================================================
   RECENT TABLE (Dashboard) — top 8 most recent
   ============================================================ */
async function loadRecentTable(year) {
  const tbody = document.getElementById("recentTableBody");
  const info  = document.getElementById("recentTableInfo");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" class="loading-row"><span class="spinner-lg"></span> Loading...</td></tr>`;

  try {
    const search = document.getElementById("dashTableSearch")?.value || "";
    const data   = await ApiAppointments.list({ per_page: 8, page: 1, search, year });
    if (!data) return;

    tbody.innerHTML = data.items.map(r => `
      <tr>
        <td><strong>${r.patient_name || "—"}</strong><br><span class="text-muted" style="font-size:.75rem">${r.patient_code || ""}</span></td>
        <td>${r.department_name || "—"}</td>
        <td>${r.doctor_name || "—"}</td>
        <td>${r.appointment_date}</td>
        <td>${r.time_slot || "—"}</td>
        <td>${statusBadge(r.status)}</td>
        <td>${riskPill(r.risk_label, r.risk_score)}</td>
        <td class="actions-cell">
          <button class="action-btn edit" onclick="openApptModal(${JSON.stringify(r).replace(/"/g,'&quot;')})"><i class="fa-solid fa-pen"></i></button>
          <button class="action-btn delete" onclick="deleteAppt(${r.id})"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`).join("") || '<tr><td colspan="8" class="empty-row">No appointments found</td></tr>';

    if (info) info.textContent = `Showing ${data.items.length} of ${data.total} records`;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="error-row"><i class="fa-solid fa-circle-exclamation"></i> ${err.message}</td></tr>`;
  }
}

/* ============================================================
   FULL APPOINTMENTS TABLE (Appointments page)
   ============================================================ */
let apptTableState = { page: 1, perPage: 12 };

async function loadApptTable() {
  const tbody = document.getElementById("apptTableBody");
  const info  = document.getElementById("apptTableInfo");
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="9" class="loading-row"><span class="spinner-lg"></span> Loading...</td></tr>`;

  const search = document.getElementById("apptSearch")?.value || "";
  const status = document.getElementById("apptStatusFilter")?.value || "";
  const deptId = document.getElementById("apptDeptFilter")?.value || "";
  const year   = document.getElementById("globalDateRange")?.value || "";

  try {
    const data = await ApiAppointments.list({
      page: apptTableState.page,
      per_page: apptTableState.perPage,
      search, status, department_id: deptId || undefined, year,
    });
    if (!data) return;

    tbody.innerHTML = data.items.map(r => `
      <tr>
        <td><strong>${r.patient_name || "—"}</strong><br><span class="text-muted" style="font-size:.75rem">${r.patient_code || ""}</span></td>
        <td>${r.department_name || "—"}</td>
        <td>${r.doctor_name || "—"}</td>
        <td>${r.appointment_date}</td>
        <td>${r.time_slot || "—"}</td>
        <td>${smsIcon(r.sms_received)}</td>
        <td>${statusBadge(r.status)}</td>
        <td>${riskPill(r.risk_label, r.risk_score)}</td>
        <td class="actions-cell">
          <button class="action-btn edit" onclick="openApptModal(${JSON.stringify(r).replace(/"/g,'&quot;')})"><i class="fa-solid fa-pen"></i></button>
          <button class="action-btn delete" onclick="deleteAppt(${r.id})"><i class="fa-solid fa-trash"></i></button>
        </td>
      </tr>`).join("") || '<tr><td colspan="9" class="empty-row">No appointments found</td></tr>';

    if (info) info.textContent = `Showing ${(apptTableState.page - 1) * apptTableState.perPage + 1}–${Math.min(apptTableState.page * apptTableState.perPage, data.total)} of ${data.total}`;
    renderPagination("apptPagination", data.page, data.pages, (p) => { apptTableState.page = p; loadApptTable(); });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="9" class="error-row"><i class="fa-solid fa-circle-exclamation"></i> ${err.message}</td></tr>`;
  }
}

async function deleteAppt(id) {
  showConfirm("Delete this appointment? This cannot be undone.", async () => {
    try {
      await ApiAppointments.delete(id);
      showToast("Appointment deleted", "success");
      loadApptTable();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

/* ============================================================
   DEPT PERFORMANCE TABLE (Operational)
   ============================================================ */
async function loadDeptPerfTable(year) {
  const tbody = document.getElementById("deptPerfBody");
  if (!tbody) return;

  try {
    const depts = await ApiAnalytics.departments(year);
    if (!depts) return;

    tbody.innerHTML = depts.map(d => {
      const rateColor = d.no_show_rate > 25 ? "var(--red)" : d.no_show_rate > 15 ? "var(--yellow)" : "var(--green)";
      const trend = d.no_show_rate > 25
        ? '<span class="trend-up"><i class="fa-solid fa-arrow-trend-up"></i> Rising</span>'
        : d.no_show_rate < 15
        ? '<span class="trend-down"><i class="fa-solid fa-arrow-trend-down"></i> Falling</span>'
        : '<span class="trend-flat"><i class="fa-solid fa-minus"></i> Stable</span>';
      return `<tr>
        <td><strong>${d.department}</strong></td>
        <td>${d.total}</td>
        <td style="color:var(--green)">${d.showed}</td>
        <td style="color:var(--red)">${d.no_show}</td>
        <td style="color:${rateColor};font-weight:700">${d.no_show_rate}%</td>
        <td>${d.avg_wait} min</td>
        <td>${trend}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="7" class="empty-row">No data</td></tr>';
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" class="error-row">${err.message}</td></tr>`;
  }
}

/* ============================================================
   USERS TABLE (Admin)
   ============================================================ */
async function loadUsersTable() {
  const tbody = document.getElementById("usersTableBody");
  if (!tbody) return;

  try {
    const users = await ApiAuth.getUsers();
    if (!users) return;
    const currentUser = Auth.getUser();

    tbody.innerHTML = users.map(u => `
      <tr>
        <td><strong>${u.full_name}</strong></td>
        <td>${u.email}</td>
        <td><span class="badge-status ${u.role === "admin" ? "badge-noshow" : "badge-showed"}">${u.role}</span></td>
        <td><span style="color:${u.is_active ? "var(--green)" : "var(--red)"}">${u.is_active ? "Active" : "Disabled"}</span></td>
        <td>${u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}</td>
        <td class="actions-cell">
          <button class="action-btn edit" onclick="openUserModal(${JSON.stringify(u).replace(/"/g,'&quot;')})"><i class="fa-solid fa-pen"></i></button>
          ${u.id !== currentUser?.id ? `<button class="action-btn delete" onclick="deleteUser(${u.id})"><i class="fa-solid fa-trash"></i></button>` : ""}
        </td>
      </tr>`).join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="error-row">${err.message}</td></tr>`;
  }
}

async function deleteUser(id) {
  showConfirm("Delete this user? This cannot be undone.", async () => {
    try {
      await ApiAuth.deleteUser(id);
      showToast("User deleted", "success");
      loadUsersTable();
    } catch (err) {
      showToast(err.message, "error");
    }
  });
}

window.loadRecentTable  = loadRecentTable;
window.loadApptTable    = loadApptTable;
window.refreshApptTable = loadApptTable;
window.loadDeptPerfTable = loadDeptPerfTable;
window.loadUsersTable   = loadUsersTable;
window.deleteAppt       = deleteAppt;
window.deleteUser       = deleteUser;
window.statusBadge      = statusBadge;
window.riskPill         = riskPill;
