/* ============================================================
   REPORTS.JS — Export CSV from live API data
   ============================================================ */

async function exportReport(type) {
  const year = document.getElementById("globalDateRange")?.value || "";

  try {
    showToast("Preparing export...", "info");
    const ts = new Date().toISOString().slice(0, 10);

    if (type === "summary") {
      const [kpi, depts] = await Promise.all([
        ApiAnalytics.kpi(year),
        ApiAnalytics.departments(year),
      ]);
      const headers = ["Metric", "Value"];
      const rows = [
        ["Total Appointments",    kpi.total],
        ["Total Showed",          kpi.showed],
        ["Total No-Show",         kpi.no_show],
        ["Total Cancelled",       kpi.cancelled],
        ["No-Show Rate (%)",      kpi.no_show_rate],
        ["Attendance Rate (%)",   kpi.attendance_rate],
        ["Avg Wait Time (min)",   kpi.avg_wait_minutes],
        ["Avg Lead Days",         kpi.avg_lead_days],
        ["SMS No-Show Rate (%)",  kpi.sms_no_show_rate],
        ["No-SMS No-Show Rate (%)", kpi.no_sms_no_show_rate],
        ["High Risk Count",       kpi.high_risk_count],
        ["", ""],
        ["Department", "No-Show Rate (%)"],
        ...depts.map(d => [d.department, d.no_show_rate]),
      ];
      downloadCSV(toCSV(headers, rows), `hospital_summary_${ts}.csv`);

    } else if (type === "noshow") {
      const data = await ApiAppointments.list({ status: "No-Show", per_page: 1000, year });
      const headers = ["ID", "Patient", "Age", "Gender", "Dept", "Doctor", "Date", "Lead Days", "SMS", "Prev No-Shows", "Risk Score", "Risk Level"];
      const rows = (data?.items || []).map(r => [
        r.id, r.patient_name, r.patient_age, r.patient_gender,
        r.department_name, r.doctor_name, r.appointment_date,
        r.lead_days, r.sms_received ? "Yes" : "No",
        r.previous_no_shows, r.risk_score, r.risk_label,
      ]);
      downloadCSV(toCSV(headers, rows), `hospital_noshow_${ts}.csv`);

    } else if (type === "department") {
      const depts = await ApiAnalytics.departments(year);
      const headers = ["Department", "Total", "Showed", "No-Show", "Cancelled", "No-Show Rate (%)", "Avg Wait (min)"];
      const rows = (depts || []).map(d => [
        d.department, d.total, d.showed, d.no_show, d.cancelled, d.no_show_rate, d.avg_wait,
      ]);
      downloadCSV(toCSV(headers, rows), `hospital_departments_${ts}.csv`);

    } else if (type === "doctor") {
      const docs = await ApiAnalytics.doctors(year);
      const headers = ["Doctor", "Department", "Total", "Showed", "No-Show", "No-Show Rate (%)", "Avg Wait (min)"];
      const rows = (docs || []).map(d => [
        d.doctor, d.department, d.total, d.showed, d.no_show, d.no_show_rate, d.avg_wait,
      ]);
      downloadCSV(toCSV(headers, rows), `hospital_doctors_${ts}.csv`);

    } else if (type === "full") {
      const data = await ApiAppointments.list({ per_page: 2000, year });
      const headers = ["ID", "Patient Code", "Patient Name", "Age", "Gender", "Department", "Doctor", "Date", "Time", "SMS", "Lead Days", "Prev No-Shows", "Wait Min", "Status", "Risk Score", "Risk"];
      const rows = (data?.items || []).map(r => [
        r.id, r.patient_code, r.patient_name, r.patient_age, r.patient_gender,
        r.department_name, r.doctor_name, r.appointment_date, r.time_slot || "",
        r.sms_received ? "Yes" : "No", r.lead_days, r.previous_no_shows,
        r.wait_minutes, r.status, r.risk_score, r.risk_label,
      ]);
      downloadCSV(toCSV(headers, rows), `hospital_full_${ts}.csv`);
    }

    showToast("Export downloaded successfully!", "success");
  } catch (err) {
    showToast(`Export failed: ${err.message}`, "error");
  }
}

function initReports() {
  document.querySelectorAll(".btn-report").forEach(btn => {
    btn.addEventListener("click", () => exportReport(btn.dataset.report));
  });
}

window.Reports = { initReports };
