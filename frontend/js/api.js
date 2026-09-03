/* ============================================================
   API.JS — All HTTP calls to the FastAPI backend
   ============================================================ */

const API_BASE = "http://localhost:8000/api";

/* ---- Token storage ---- */
const Auth = {
  getToken()        { return localStorage.getItem("access_token"); },
  setToken(t)       { localStorage.setItem("access_token", t); },
  getRefresh()      { return localStorage.getItem("refresh_token"); },
  setRefresh(t)     { localStorage.setItem("refresh_token", t); },
  getUser()         { try { return JSON.parse(localStorage.getItem("user")); } catch { return null; } },
  setUser(u)        { localStorage.setItem("user", JSON.stringify(u)); },
  clear()           { localStorage.removeItem("access_token"); localStorage.removeItem("refresh_token"); localStorage.removeItem("user"); },
  isLoggedIn()      { return !!this.getToken(); },
  isAdmin()         { const u = this.getUser(); return u && u.role === "admin"; },
};

/* ---- Core fetch wrapper ---- */
async function apiFetch(path, options = {}, retry = true) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = Auth.getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Auto-refresh on 401
  if (res.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch(path, options, false);
    Auth.clear();
    showLoginPage();
    return null;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null;
  return res.json();
}

async function tryRefresh() {
  const rt = Auth.getRefresh();
  if (!rt) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    Auth.setToken(data.access_token);
    Auth.setRefresh(data.refresh_token);
    return true;
  } catch { return false; }
}

/* ---- Multipart upload (no JSON header) ---- */
async function apiUpload(path, formData) {
  const token = Auth.getToken();
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ============================================================
   AUTH
   ============================================================ */
const ApiAuth = {
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Login failed");
    }
    const data = await res.json();
    Auth.setToken(data.access_token);
    Auth.setRefresh(data.refresh_token);
    Auth.setUser(data.user);
    return data;
  },
  async getMe()         { return apiFetch("/auth/me"); },
  async getUsers()      { return apiFetch("/auth/users"); },
  async createUser(b)   { return apiFetch("/auth/register", { method: "POST", body: JSON.stringify(b) }); },
  async updateUser(id, b) { return apiFetch(`/auth/users/${id}`, { method: "PUT", body: JSON.stringify(b) }); },
  async deleteUser(id)  { return apiFetch(`/auth/users/${id}`, { method: "DELETE" }); },
};

/* ============================================================
   ANALYTICS
   ============================================================ */
const ApiAnalytics = {
  async kpi(year)         { return apiFetch(`/analytics/kpi${year ? `?year=${year}` : ""}`); },
  async monthly(year)     { return apiFetch(`/analytics/monthly${year ? `?year=${year}` : ""}`); },
  async departments(year) { return apiFetch(`/analytics/departments${year ? `?year=${year}` : ""}`); },
  async doctors(year)     { return apiFetch(`/analytics/doctors${year ? `?year=${year}` : ""}`); },
  async ageGroups(year)   { return apiFetch(`/analytics/age-groups${year ? `?year=${year}` : ""}`); },
  async dow(year)         { return apiFetch(`/analytics/dow${year ? `?year=${year}` : ""}`); },
  async riskFactors(year) { return apiFetch(`/analytics/risk-factors${year ? `?year=${year}` : ""}`); },
  async smsImpact(year)   { return apiFetch(`/analytics/sms-impact${year ? `?year=${year}` : ""}`); },
  async leadTime(year)    { return apiFetch(`/analytics/lead-time${year ? `?year=${year}` : ""}`); },
};

/* ============================================================
   APPOINTMENTS
   ============================================================ */
const ApiAppointments = {
  async list(params = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== "" && v !== null) qs.set(k, v); });
    return apiFetch(`/appointments?${qs.toString()}`);
  },
  async get(id)      { return apiFetch(`/appointments/${id}`); },
  async create(body) { return apiFetch("/appointments", { method: "POST", body: JSON.stringify(body) }); },
  async update(id, body) { return apiFetch(`/appointments/${id}`, { method: "PUT", body: JSON.stringify(body) }); },
  async delete(id)   { return apiFetch(`/appointments/${id}`, { method: "DELETE" }); },
};

/* ============================================================
   PATIENTS
   ============================================================ */
const ApiPatients = {
  async list(search = "")  { return apiFetch(`/patients?limit=500${search ? `&search=${encodeURIComponent(search)}` : ""}`); },
  async create(body)       { return apiFetch("/patients", { method: "POST", body: JSON.stringify(body) }); },
  async update(id, body)   { return apiFetch(`/patients/${id}`, { method: "PUT", body: JSON.stringify(body) }); },
  async delete(id)         { return apiFetch(`/patients/${id}`, { method: "DELETE" }); },
};

/* ============================================================
   DEPARTMENTS & DOCTORS
   ============================================================ */
const ApiDepts = {
  async list()              { return apiFetch("/departments"); },
  async doctors(deptId)     { return apiFetch(`/departments/doctors${deptId ? `?department_id=${deptId}` : ""}`); },
};

/* ============================================================
   UPLOAD
   ============================================================ */
const ApiUpload = {
  async uploadCsv(file) {
    const fd = new FormData();
    fd.append("file", file);
    return apiUpload("/upload/csv", fd);
  },
};

/* ============================================================
   CSV EXPORT HELPERS
   ============================================================ */
function downloadCSV(content, filename) {
  const blob = new Blob(["\uFEFF" + content], { type: "text/csv;charset=utf-8;" });
  const url  = URL.createObjectURL(blob);
  const a    = Object.assign(document.createElement("a"), { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function toCSV(headers, rows) {
  const esc = v => { const s = String(v ?? ""); return s.includes(",") || s.includes('"') ? `"${s.replace(/"/g, '""')}"` : s; };
  return [headers, ...rows].map(r => r.map(esc).join(",")).join("\r\n");
}

window.Auth         = Auth;
window.ApiAuth      = ApiAuth;
window.ApiAnalytics = ApiAnalytics;
window.ApiAppointments = ApiAppointments;
window.ApiPatients  = ApiPatients;
window.ApiDepts     = ApiDepts;
window.ApiUpload    = ApiUpload;
window.downloadCSV  = downloadCSV;
window.toCSV        = toCSV;
