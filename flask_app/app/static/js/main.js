/* ============================================================
   main.js — UI interactions only. Zero analytics logic.
   ============================================================ */
Chart.register(ChartDataLabels);

document.addEventListener('DOMContentLoaded', () => {

  // ── Sidebar toggle ──────────────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const main    = document.getElementById('mainContent');
  [document.getElementById('sidebarToggle'), document.getElementById('menuBtn')]
    .forEach(btn => btn?.addEventListener('click', () => {
      sidebar?.classList.toggle('collapsed');
      main?.classList.toggle('expanded');
    }));

  // ── Auto-dismiss flash messages ─────────────────────────────
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity .4s'; }, 4000);
    setTimeout(() => el.remove(), 4500);
  });

  // ── Dark mode ───────────────────────────────────────────────
  const html     = document.getElementById('htmlRoot');
  const darkBtn  = document.getElementById('darkToggle');
  const darkIcon = document.getElementById('darkIcon');

  function applyTheme(dark) {
    if (dark) {
      html?.setAttribute('data-theme', 'dark');
      if (darkIcon) darkIcon.className = 'fa-solid fa-sun';
      if (darkBtn)  darkBtn.title = 'Switch to light mode';
    } else {
      html?.removeAttribute('data-theme');
      if (darkIcon) darkIcon.className = 'fa-solid fa-moon';
      if (darkBtn)  darkBtn.title = 'Switch to dark mode';
    }
  }

  // Restore saved preference
  const savedTheme = localStorage.getItem('careflow-theme');
  applyTheme(savedTheme === 'dark');

  darkBtn?.addEventListener('click', () => {
    const isDark = html?.getAttribute('data-theme') === 'dark';
    applyTheme(!isDark);
    localStorage.setItem('careflow-theme', isDark ? 'light' : 'dark');
  });

  // ── Reminder badge (topbar + sidebar) ───────────────────────
  async function loadReminderCount() {
    try {
      const res   = await fetch('/reminders/api/upcoming');
      const data  = await res.json();
      const count = data.due_soon || 0;

      const topBadge = document.getElementById('topbarReminderBadge');
      const navBadge = document.getElementById('reminderBadge');

      if (count > 0) {
        const label = count > 99 ? '99+' : String(count);
        if (topBadge) { topBadge.textContent = label; topBadge.style.display = 'flex'; }
        if (navBadge) { navBadge.textContent = label; navBadge.style.display = 'inline'; }
      } else {
        if (topBadge) topBadge.style.display = 'none';
        if (navBadge) navBadge.style.display = 'none';
      }
    } catch (_) { /* silent fail */ }
  }

  loadReminderCount();

});

// ── Chart type toggle (monthly chart on dashboard) ───────────
let monthlyChartInstance = null;
function setChartType(chartId, type, btn) {
  document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const canvas = document.getElementById(chartId + 'Chart');
  if (!canvas) return;
  const data = JSON.parse(canvas.dataset.chart);
  if (monthlyChartInstance) { monthlyChartInstance.destroy(); }
  monthlyChartInstance = renderMonthlyChart(canvas, data, type);
}
