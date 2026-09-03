/* ============================================================
   APP.JS — Main application controller (API-driven)
   ============================================================ */

/* ---- Toast ---- */
function showToast(msg, type = "info") {
  const t = document.getElementById("toast");
  if (!t) return;
  t.textContent = msg;
  t.className   = `toast show ${type}`;
  clearTimeout(t._tmr);
  t._tmr = setTimeout(() => { t.className = "toast"; }, 3500);
}
window.showToast = showToast;

/* ---- Show/hide login ---- */
function showLoginPage() {
  document.getElementById("loginOverlay").style.display = "flex";
  document.getElementById("appShell").style.display     = "none";
}
function showAppShell() {
  document.getElementById("loginOverlay").style.display = "none";
  document.getElementById("appShell").style.display     = "flex";
}
window.showLoginPage = showLoginPage;

/* ---- KPI builder ---- */
function buildKpiCard({ label, value, icon, color, bg, change, changeDir, sub }) {
  return `
  <div class="kpi-card" style="border-left-color:${color}">
    <div class="kpi-icon" style="background:${bg};color:${color}"><i class="fa-solid ${icon}"></i></div>
    <div class="kpi-body">
      <div class="kpi-label">${label}</div>
      <div class="kpi-value" style="color:${color}">${value}</div>
      ${change ? `<div class="kpi-change ${changeDir || "neutral"}"><i class="fa-solid fa-arrow-${changeDir === "up" ? "up" : changeDir === "down" ? "down" : "right"}"></i> ${change}</div>` : ""}
      ${sub ? `<div class="kpi-change neutral">${sub}</div>` : ""}
    </div>
  </div>`;
}

/* ============================================================
   LOGIN
   ============================================================ */
document.getElementById("loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  const errEl  = document.getElementById("loginError");
  const btn    = document.getElementById("loginBtn");
  const txt    = document.getElementById("loginBtnText");
  const spin   = document.getElementById("loginSpinner");
  errEl.textContent = "";
  btn.disabled = true;
  txt.style.display   = "none";
  spin.style.display  = "inline-block";

  try {
    const data = await ApiAuth.login(
      document.getElementById("loginEmail").value,
      document.getElementById("loginPassword").value,
    );
    showAppShell();
    initApp(data.user);
  } catch (err) {
    errEl.textContent = err.message;
  } finally {
    btn.disabled = false;
    txt.style.display  = "inline";
    spin.style.display = "none";
  }
});

document.getElementById("eyeBtn")?.addEventListener("click", () => {
  const inp = document.getElementById("loginPassword");
  const icon = document.getElementById("eyeBtn").querySelector("i");
  if (inp.type === "password") { inp.type = "text";     icon.className = "fa-solid fa-eye-slash"; }
  else                         { inp.type = "password"; icon.className = "fa-solid fa-eye"; }
});

document.getElementById("logoutBtn")?.addEventListener("click", () => {
  Auth.clear();
  showLoginPage();
  showToast("Signed out", "info");
});

/* ============================================================
   INIT APP after login
   ============================================================ */
function initApp(user) {
  document.getElementById("sidebarUserName").textContent = user.full_name;
  document.getElementById("sidebarUserRole").textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);

  // Show admin nav only for admins
  if (user.role === "admin") {
    document.getElementById("adminNav").style.display = "";
  }

  // Nav links
  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", e => { e.preventDefault(); navigateTo(link.dataset.page); });
  });

  // Sidebar toggle
  const sidebar = document.getElementById("sidebar");
  const main    = document.getElementById("mainContent");
  [document.getElementById("sidebarToggle"), document.getElementById("menuBtn")].forEach(btn => {
    btn?.addEventListener("click", () => { sidebar.classList.toggle("collapsed"); main.classList.toggle("expanded"); });
  });

  // Global date range
  document.getElementById("globalDateRange")?.addEventListener("change", () => renderPage(window.currentPage));

  // Refresh
  document.getElementById("refreshBtn")?.addEventListener("click", () => {
    const btn = document.getElementById("refreshBtn");
    btn.classList.add("spinning");
    setTimeout(() => { renderPage(window.currentPage); btn.classList.remove("spinning"); showToast("Data refreshed", "success"); }, 400);
  });

  // Chart type toggle
  document.querySelectorAll(".chart-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(`.chart-btn[data-chart="${btn.dataset.chart}"]`).forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      if (btn.dataset.chart === "monthly") {
        const year = document.getElementById("globalDateRange")?.value;
        renderMonthlyChartFromAPI(year, btn.dataset.type);
      }
    });
  });

  // Dashboard search
  document.getElementById("dashTableSearch")?.addEventListener("input", () => loadRecentTable(getYear()));

  // Appointments page filters
  ["apptSearch", "apptStatusFilter", "apptDeptFilter"].forEach(id => {
    document.getElementById(id)?.addEventListener("input",  () => { apptTableState.page = 1; loadApptTable(); });
    document.getElementById(id)?.addEventListener("change", () => { apptTableState.page = 1; loadApptTable(); });
  });

  // No-show filters
  ["nsDeptFilter", "nsAgeFilter", "nsGenderFilter", "nsSmsFilter"].forEach(id => {
    document.getElementById(id)?.addEventListener("change", renderNoShowPage);
  });
  document.getElementById("nsResetFilters")?.addEventListener("click", () => {
    ["nsDeptFilter", "nsAgeFilter", "nsGenderFilter", "nsSmsFilter"].forEach(id => {
      const el = document.getElementById(id); if (el) el.value = "";
    });
    renderNoShowPage();
    showToast("Filters reset", "info");
  });

  // Upload
  initUploadPage();

  // Reports
  Reports.initReports();

  // Dept filter on appointments page
  ApiDepts.list().then(depts => {
    const sel = document.getElementById("apptDeptFilter");
    if (sel && depts) depts.forEach(d => sel.append(Object.assign(document.createElement("option"), { value: d.id, textContent: d.name })));
    // Noshow dept filter
    const nsSel = document.getElementById("nsDeptFilter");
    if (nsSel && depts) depts.forEach(d => nsSel.append(Object.assign(document.createElement("option"), { value: d.name, textContent: d.name })));
  });

  navigateTo("dashboard");
  setTimeout(() => showToast(`Welcome back, ${user.full_name}!`, "success"), 500);
}

/* ============================================================
   PAGE TITLES & NAVIGATION
   ============================================================ */
const PAGE_TITLES = {
  dashboard: "Dashboard", noshow: "No-Show Analysis",
  operational: "Operational Analysis", demographics: "Patient Demographics",
  appointments: "Appointments", upload: "Upload Data",
  reports: "Reports & Export", admin: "Admin — User Management",
};

window.currentPage = "dashboard";

function navigateTo(pageId) {
  if (!document.getElementById("page-" + pageId)) return;
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  document.querySelector(`.nav-link[data-page="${pageId}"]`)?.classList.add("active");
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById("page-" + pageId)?.classList.add("active");
  document.getElementById("pageTitle").textContent = PAGE_TITLES[pageId] || pageId;
  window.currentPage = pageId;
  renderPage(pageId);
  window.scrollTo(0, 0);
}
window.renderPage = renderPage;

function getYear() { return document.getElementById("globalDateRange")?.value || ""; }

async function renderPage(pageId) {
  const year = getYear();
  switch (pageId) {
    case "dashboard":    await renderDashboardPage(year); break;
    case "noshow":       await renderNoShowPage(); break;
    case "operational":  await renderOperationalPage(year); break;
    case "demographics": await renderDemographicsPage(year); break;
    case "appointments": await loadApptTable(); break;
    case "upload":       /* static */ break;
    case "reports":      /* static */ break;
    case "admin":        await loadUsersTable(); break;
  }
}

/* ============================================================
   DASHBOARD PAGE
   ============================================================ */
async function renderDashboardPage(year) {
  const [kpi, monthly, depts, dow, risks] = await Promise.all([
    ApiAnalytics.kpi(year),
    ApiAnalytics.monthly(year),
    ApiAnalytics.departments(year),
    ApiAnalytics.dow(year),
    ApiAnalytics.riskFactors(year),
  ]).catch(() => [null, null, null, null, null]);

  if (!kpi) { showToast("Failed to load dashboard data", "error"); return; }

  // KPIs
  const grid = document.getElementById("kpiGrid");
  if (grid) grid.innerHTML = [
    { label: "Total Appointments", value: kpi.total.toLocaleString(), icon: "fa-calendar-check",   color: "var(--blue)",   bg: "var(--blue-light)",   change: "All records", changeDir: "neutral" },
    { label: "Attendance Rate",    value: kpi.attendance_rate + "%",  icon: "fa-user-check",        color: "var(--green)",  bg: "var(--green-light)",  change: kpi.showed + " showed up",   changeDir: "up" },
    { label: "No-Show Rate",       value: kpi.no_show_rate + "%",     icon: "fa-user-xmark",        color: "var(--red)",    bg: "var(--red-light)",    change: kpi.no_show + " no-shows",   changeDir: "down" },
    { label: "Cancelled",          value: kpi.cancelled.toLocaleString(), icon: "fa-calendar-xmark", color: "var(--yellow)", bg: "var(--yellow-light)", change: kpi.total > 0 ? ((kpi.cancelled / kpi.total) * 100).toFixed(1) + "% of total" : "", changeDir: "neutral" },
    { label: "SMS Impact",         value: kpi.sms_no_show_rate + "%", icon: "fa-comment-sms",       color: "var(--teal)",   bg: "var(--teal-light)",   sub: `vs ${kpi.no_sms_no_show_rate}% without SMS` },
    { label: "High Risk Patients", value: kpi.high_risk_count.toLocaleString(), icon: "fa-triangle-exclamation", color: "var(--orange)", bg: "var(--orange-light)", change: kpi.total > 0 ? ((kpi.high_risk_count / kpi.total) * 100).toFixed(1) + "% of total" : "" },
    { label: "Avg Wait Time",      value: kpi.avg_wait_minutes + " min", icon: "fa-stopwatch",      color: "var(--purple)", bg: "var(--purple-light)" },
    { label: "Avg Lead Days",      value: kpi.avg_lead_days + " days",   icon: "fa-calendar-days",  color: "#4f46e5",       bg: "#ede9fe" },
  ].map(buildKpiCard).join("");

  // Charts
  if (monthly) Charts.renderMonthlyChart(monthly, "bar");
  if (kpi)     Charts.renderAttendanceDonut(kpi);
  if (depts)   Charts.renderDeptNoShowChart(depts);
  if (dow)     Charts.renderDowChart(dow);
  if (risks)   Charts.renderRiskChart(risks);

  // Table
  await loadRecentTable(year);
}

async function renderMonthlyChartFromAPI(year, type = "bar") {
  const monthly = await ApiAnalytics.monthly(year).catch(() => null);
  if (monthly) Charts.renderMonthlyChart(monthly, type);
}

/* ============================================================
   NO-SHOW PAGE
   ============================================================ */
async function renderNoShowPage() {
  const year    = getYear();
  const dept    = document.getElementById("nsDeptFilter")?.value    || "";
  const ageGrp  = document.getElementById("nsAgeFilter")?.value     || "";
  const gender  = document.getElementById("nsGenderFilter")?.value  || "";
  const sms     = document.getElementById("nsSmsFilter")?.value     || "";

  const [kpi, depts, smsImp, ageGroups, dow, leadTime] = await Promise.all([
    ApiAnalytics.kpi(year),
    ApiAnalytics.departments(year),
    ApiAnalytics.smsImpact(year),
    ApiAnalytics.ageGroups(year),
    ApiAnalytics.dow(year),
    ApiAnalytics.leadTime(year),
  ]).catch(() => Array(6).fill(null));

  if (!kpi) return;

  // Find top no-show dept
  const topDept = depts ? [...depts].sort((a, b) => b.no_show_rate - a.no_show_rate)[0] : null;

  const grid = document.getElementById("nsKpiGrid");
  if (grid) grid.innerHTML = [
    { label: "No-Show Rate",      value: kpi.no_show_rate + "%",       icon: "fa-user-xmark",          color: "var(--red)",    bg: "var(--red-light)",    change: kpi.no_show + " patients", changeDir: "down" },
    { label: "SMS Reduces Rate",  value: smsImp ? (smsImp.no_sms_rate - smsImp.sms_sent_rate).toFixed(1) + "%" : "—", icon: "fa-comment-sms", color: "var(--teal)", bg: "var(--teal-light)", sub: smsImp ? `${smsImp.sms_sent_rate}% with SMS vs ${smsImp.no_sms_rate}% without` : "" },
    { label: "Highest NS Dept",   value: topDept?.department || "—",   icon: "fa-building-columns",    color: "var(--orange)", bg: "var(--orange-light)", change: topDept ? topDept.no_show_rate + "% rate" : "" },
    { label: "High Risk Appts",   value: kpi.high_risk_count.toLocaleString(), icon: "fa-triangle-exclamation", color: "var(--purple)", bg: "var(--purple-light)", change: kpi.total > 0 ? ((kpi.high_risk_count / kpi.total) * 100).toFixed(1) + "% of total" : "" },
    { label: "Total No-Shows",    value: kpi.no_show.toLocaleString(), icon: "fa-ban",                 color: "var(--red)",    bg: "var(--red-light)" },
    { label: "Avg Lead Days",     value: kpi.avg_lead_days + " days",  icon: "fa-calendar-days",       color: "var(--blue)",   bg: "var(--blue-light)",   change: "longer = more risk" },
  ].map(buildKpiCard).join("");

  if (depts)    Charts.renderNsDeptRateChart(depts);
  if (smsImp)   Charts.renderNsSmsChart(smsImp);
  if (ageGroups)Charts.renderNsAgeChart(ageGroups);
  if (dow)      Charts.renderNsDowChart(dow);
  if (leadTime) Charts.renderNsLeadTimeChart(leadTime);
}

/* ============================================================
   OPERATIONAL PAGE
   ============================================================ */
async function renderOperationalPage(year) {
  const [kpi, monthly, depts, doctors, dow] = await Promise.all([
    ApiAnalytics.kpi(year),
    ApiAnalytics.monthly(year),
    ApiAnalytics.departments(year),
    ApiAnalytics.doctors(year),
    ApiAnalytics.dow(year),
  ]).catch(() => Array(5).fill(null));

  if (!kpi) return;

  const uniqueDepts = depts ? depts.length : 0;
  const uniqueDoctors = doctors ? doctors.length : 0;

  const grid = document.getElementById("opKpiGrid");
  if (grid) grid.innerHTML = [
    { label: "Total Appointments", value: kpi.total.toLocaleString(), icon: "fa-calendar-check", color: "var(--blue)",   bg: "var(--blue-light)" },
    { label: "Active Departments", value: uniqueDepts,                icon: "fa-building-columns",color: "var(--teal)",   bg: "var(--teal-light)" },
    { label: "Active Doctors",     value: uniqueDoctors,              icon: "fa-user-doctor",     color: "var(--green)",  bg: "var(--green-light)" },
    { label: "Avg Wait Time",      value: kpi.avg_wait_minutes + " min", icon: "fa-stopwatch",   color: "var(--orange)", bg: "var(--orange-light)" },
    { label: "Attendance Rate",    value: kpi.attendance_rate + "%",  icon: "fa-user-check",      color: "var(--green)",  bg: "var(--green-light)", change: kpi.showed + " attended", changeDir: "up" },
    { label: "No-Show Rate",       value: kpi.no_show_rate + "%",     icon: "fa-user-xmark",      color: "var(--red)",    bg: "var(--red-light)",   change: kpi.no_show + " missed",  changeDir: "down" },
  ].map(buildKpiCard).join("");

  if (monthly) Charts.renderOpTrendChart(monthly);
  if (depts)   { Charts.renderOpCapacityChart(depts); Charts.renderOpWaitChart(depts); }
  if (doctors) Charts.renderOpDoctorChart(doctors);
  if (dow)     Charts.renderOpHourChart(dow);
  await loadDeptPerfTable(year);
}

/* ============================================================
   DEMOGRAPHICS PAGE
   ============================================================ */
async function renderDemographicsPage(year) {
  const [kpi, ageGroups, depts] = await Promise.all([
    ApiAnalytics.kpi(year),
    ApiAnalytics.ageGroups(year),
    ApiAnalytics.departments(year),
  ]).catch(() => Array(3).fill(null));

  if (!kpi) return;

  // Get raw patient data via appointments list for demo charts
  const appts = await ApiAppointments.list({ per_page: 1000, year }).catch(() => null);
  const items = appts?.items || [];

  const uniquePatients = new Set(items.map(r => r.patient_code)).size;
  const female = items.filter(r => r.patient_gender === "Female").length;
  const total  = items.length || 1;

  const grid = document.getElementById("demKpiGrid");
  if (grid) grid.innerHTML = [
    { label: "Unique Patients",   value: uniquePatients.toLocaleString(), icon: "fa-users",         color: "var(--blue)",   bg: "var(--blue-light)" },
    { label: "Total Appointments",value: kpi.total.toLocaleString(),      icon: "fa-calendar-check",color: "var(--teal)",   bg: "var(--teal-light)" },
    { label: "Female Patients",   value: ((female / total) * 100).toFixed(0) + "%", icon: "fa-venus", color: "#db2777", bg: "#fce7f3", change: female + " records" },
    { label: "No-Show Rate",      value: kpi.no_show_rate + "%",          icon: "fa-user-xmark",    color: "var(--red)",    bg: "var(--red-light)" },
    { label: "Avg Lead Days",     value: kpi.avg_lead_days + " days",     icon: "fa-calendar-days", color: "var(--purple)", bg: "var(--purple-light)" },
    { label: "High Risk",         value: kpi.high_risk_count.toLocaleString(), icon: "fa-triangle-exclamation", color: "var(--orange)", bg: "var(--orange-light)" },
  ].map(buildKpiCard).join("");

  if (ageGroups) Charts.renderDemAgeChart(ageGroups);
  if (items.length) {
    Charts.renderDemGenderChart(items);
    Charts.renderDemNeighChart(items);
    Charts.renderDemScholarChart(items);
    Charts.renderDemConditionChart(items);
  }
}

/* ============================================================
   UPLOAD PAGE
   ============================================================ */
function initUploadPage() {
  const area   = document.getElementById("uploadArea");
  const input  = document.getElementById("csvFileInput");
  const preview = document.getElementById("uploadPreview");
  const result  = document.getElementById("uploadResult");
  let selectedFile = null;

  document.getElementById("btnBrowse")?.addEventListener("click", () => input.click());

  input?.addEventListener("change", () => {
    if (input.files[0]) setFile(input.files[0]);
  });

  area?.addEventListener("dragover", e => { e.preventDefault(); area.classList.add("drag-over"); });
  area?.addEventListener("dragleave", () => area.classList.remove("drag-over"));
  area?.addEventListener("drop", e => {
    e.preventDefault();
    area.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) setFile(file);
  });

  document.getElementById("btnRemoveFile")?.addEventListener("click", () => {
    selectedFile = null;
    preview.style.display  = "none";
    result.style.display   = "none";
    input.value = "";
  });

  document.getElementById("btnImport")?.addEventListener("click", async () => {
    if (!selectedFile) return;
    const btn = document.getElementById("btnImport");
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Importing...';
    result.style.display = "none";

    try {
      const res = await ApiUpload.uploadCsv(selectedFile);
      result.style.display = "block";
      result.className = "upload-result success";
      result.innerHTML = `
        <i class="fa-solid fa-circle-check"></i>
        <div>
          <strong>Import Successful!</strong><br>
          ${res.inserted} records inserted, ${res.skipped} skipped.
          ${res.errors?.length ? `<br><small>${res.errors.join("; ")}</small>` : ""}
        </div>`;
      showToast(`Imported ${res.inserted} records`, "success");
    } catch (err) {
      result.style.display = "block";
      result.className = "upload-result error";
      result.innerHTML = `<i class="fa-solid fa-circle-exclamation"></i> <div><strong>Import Failed:</strong> ${err.message}</div>`;
      showToast("Import failed: " + err.message, "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-database"></i> Import to Database';
    }
  });

  function setFile(file) {
    selectedFile = file;
    document.getElementById("uploadFileName").textContent = file.name;
    document.getElementById("uploadFileSize").textContent = (file.size / 1024).toFixed(1) + " KB";
    preview.style.display = "flex";
    result.style.display  = "none";
  }
}

/* ============================================================
   BOOTSTRAP
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  // Check existing token
  if (Auth.isLoggedIn()) {
    ApiAuth.getMe().then(user => {
      if (user) {
        Auth.setUser(user);
        showAppShell();
        initApp(user);
      } else {
        showLoginPage();
      }
    }).catch(() => showLoginPage());
  } else {
    showLoginPage();
  }
});
