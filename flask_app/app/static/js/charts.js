/**
 * charts.js — ONLY chart rendering.
 * Reads pre-computed JSON embedded by Python/Jinja2.
 * No analytics, no aggregations, no data transformations.
 */

const DEPT_COLORS = [
  '#2563eb','#dc2626','#16a34a','#ea580c','#7c3aed',
  '#0891b2','#ca8a04','#db2777','#4f46e5','#65a30d',
];

const BASE_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    datalabels: { display: false },
    tooltip: {
      backgroundColor: '#0f172a', padding: 10,
      cornerRadius: 8,
      titleFont: { size: 11, weight: 'bold' },
      bodyFont: { size: 10 },
    },
  },
};

/** Read data-chart attribute and call renderer */
function initChart(canvasId, rendererFn) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  try {
    const data = JSON.parse(canvas.dataset.chart);
    rendererFn(canvas, data);
  } catch (e) {
    console.warn(`Chart ${canvasId}: bad data`, e);
  }
}

/* ── Monthly bar/line (dashboard + operational) ──────────── */
function renderMonthlyChart(canvas, d, type = 'bar') {
  return new Chart(canvas, {
    type,
    data: {
      labels: d.labels,
      datasets: [
        {
          label: 'Showed',
          data: d.showed,
          backgroundColor: type === 'bar' ? 'rgba(22,163,74,.8)' : 'rgba(22,163,74,.15)',
          borderColor: '#16a34a', borderWidth: type === 'bar' ? 0 : 2,
          fill: type === 'line', tension: .4,
        },
        {
          label: 'No-Show',
          data: d.no_show,
          backgroundColor: type === 'bar' ? 'rgba(220,38,38,.8)' : 'rgba(220,38,38,.15)',
          borderColor: '#dc2626', borderWidth: type === 'bar' ? 0 : 2,
          fill: type === 'line', tension: .4,
        },
      ],
    },
    options: {
      ...BASE_OPTS,
      plugins: {
        ...BASE_OPTS.plugins,
        legend: { display: true, position: 'top', labels: { font: { size: 11 }, boxWidth: 11, padding: 12 } },
      },
      scales: {
        x: { stacked: type === 'bar', grid: { display: false }, ticks: { font: { size: 9 }, maxRotation: 45 } },
        y: { stacked: type === 'bar', beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
      },
    },
  });
}

/* ── Donut (attendance / loyalty) ────────────────────────── */
function renderDonutChart(canvas, d) {
  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: d.labels,
      datasets: [{ data: d.values, backgroundColor: d.colors || DEPT_COLORS, borderWidth: 3, borderColor: '#fff', hoverOffset: 7 }],
    },
    options: {
      ...BASE_OPTS,
      cutout: '65%',
      plugins: {
        ...BASE_OPTS.plugins,
        datalabels: {
          display: true, color: '#fff', font: { size: 11, weight: 'bold' },
          formatter: (v, ctx) => {
            const sum = ctx.dataset.data.reduce((a, b) => a + b, 0);
            return sum > 0 ? ((v / sum) * 100).toFixed(1) + '%' : '';
          },
        },
      },
    },
  });
}

/* ── Dept horizontal bar (no-show rate) ──────────────────── */
function renderDeptBarChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ label: 'No-Show Rate (%)', data: d.rates, backgroundColor: DEPT_COLORS, borderRadius: 5, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      indexAxis: 'y',
      plugins: {
        ...BASE_OPTS.plugins,
        datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 9, weight: 'bold' }, formatter: v => v + '%' },
      },
      scales: {
        x: { beginAtZero: true, max: 60, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } },
      },
    },
  });
}

/* ── Dept combo (no-show + rate line) ────────────────────── */
function renderDeptComboChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [
        { label: 'Total', data: d.totals, backgroundColor: 'rgba(37,99,235,.2)', borderColor: '#2563eb', borderWidth: 1.5, borderRadius: 4, yAxisID: 'y' },
        { label: 'No-Show', data: d.no_show, backgroundColor: 'rgba(220,38,38,.8)', borderRadius: 4, borderWidth: 0, yAxisID: 'y' },
        { type: 'line', label: 'Rate %', data: d.rates, borderColor: '#ea580c', borderWidth: 2, pointRadius: 3, fill: false, tension: .3, yAxisID: 'y1', backgroundColor: '#ea580c' },
      ],
    },
    options: {
      ...BASE_OPTS,
      plugins: {
        ...BASE_OPTS.plugins,
        legend: { display: true, position: 'top', labels: { font: { size: 10 }, boxWidth: 10, padding: 12 } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 }, maxRotation: 35 } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y1: { beginAtZero: true, position: 'right', max: 60, grid: { display: false }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Day-of-week bar ─────────────────────────────────────── */
function renderDowChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ label: 'Appointments', data: d.totals, backgroundColor: 'rgba(37,99,235,.8)', borderRadius: 5, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 9, weight: 'bold' } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
      },
    },
  });
}

/* ── Risk factors horizontal bar ─────────────────────────── */
function renderRiskChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ label: 'No-Shows', data: d.values, backgroundColor: ['#dc2626','#ea580c','#ca8a04','#7c3aed','#0891b2','#2563eb'], borderRadius: 5, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      indexAxis: 'y',
      plugins: { ...BASE_OPTS.plugins, datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 9, weight: 'bold' } } },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } },
      },
    },
  });
}

/* ── SMS impact bar ──────────────────────────────────────── */
function renderSmsChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ data: d.rates, backgroundColor: ['#16a34a', '#dc2626'], borderRadius: 7, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      plugins: {
        ...BASE_OPTS.plugins,
        datalabels: { display: true, anchor: 'center', align: 'center', color: '#fff', font: { size: 13, weight: 'bold' }, formatter: v => v + '%' },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 10, weight: 'bold' } } },
        y: { beginAtZero: true, max: 60, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Age group rate bar ───────────────────────────────────── */
function renderAgeRateChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ data: d.rates, backgroundColor: ['#2563eb','#dc2626','#ea580c','#7c3aed'], borderRadius: 7, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 10, weight: 'bold' }, formatter: v => v + '%' } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Gender donut ────────────────────────────────────────── */
function renderGenderDonut(canvas, d) {
  new Chart(canvas, {
    type: 'doughnut',
    data: {
      labels: d.labels.map((l, i) => `${l} (${d.rates[i]}%)`),
      datasets: [{ data: d.values, backgroundColor: ['#2563eb','#db2777'], borderWidth: 3, borderColor: '#fff', hoverOffset: 7 }],
    },
    options: {
      ...BASE_OPTS,
      cutout: '60%',
      plugins: {
        ...BASE_OPTS.plugins,
        legend: { display: true, position: 'bottom', labels: { font: { size: 10 }, boxWidth: 10, padding: 12 } },
        datalabels: {
          display: true, color: '#fff', font: { size: 12, weight: 'bold' },
          formatter: (v, ctx) => { const s = ctx.dataset.data.reduce((a, b) => a + b, 0); return ((v / s) * 100).toFixed(0) + '%'; },
        },
      },
    },
  });
}

/* ── DOW radar ───────────────────────────────────────────── */
function renderRadarChart(canvas, d) {
  new Chart(canvas, {
    type: 'radar',
    data: {
      labels: d.labels,
      datasets: [{ label: 'No-Show Rate (%)', data: d.rates, backgroundColor: 'rgba(220,38,38,.15)', borderColor: '#dc2626', borderWidth: 2, pointBackgroundColor: '#dc2626', pointRadius: 3 }],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, legend: { display: false } },
      scales: {
        r: { beginAtZero: true, ticks: { font: { size: 8 }, backdropColor: 'transparent', callback: v => v + '%' }, pointLabels: { font: { size: 9 } }, grid: { color: '#e2e8f0' } },
      },
    },
  });
}

/* ── Lead time combo ─────────────────────────────────────── */
function renderLeadComboChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [
        { label: 'Appointments', data: d.totals, backgroundColor: 'rgba(37,99,235,.2)', borderColor: '#2563eb', borderWidth: 1.5, borderRadius: 4, yAxisID: 'y' },
        { type: 'line', label: 'No-Show Rate', data: d.rates, borderColor: '#dc2626', borderWidth: 2.5, pointRadius: 4, fill: false, tension: .3, yAxisID: 'y1', backgroundColor: '#dc2626' },
      ],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, legend: { display: true, position: 'top', labels: { font: { size: 10 }, boxWidth: 10, padding: 12 } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y1: { beginAtZero: true, position: 'right', max: 60, grid: { display: false }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Prev no-show impact bar ─────────────────────────────── */
function renderPrevNoShowChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ data: d.rates, backgroundColor: ['#16a34a','#ca8a04','#ea580c','#dc2626','#7c3aed'], borderRadius: 7, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 10, weight: 'bold' }, formatter: v => v + '%' } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Trend line (operational) ────────────────────────────── */
function renderTrendChart(canvas, d) {
  new Chart(canvas, {
    type: 'line',
    data: {
      labels: d.labels,
      datasets: [
        { label: 'Total Appointments', data: d.totals, borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,.1)', borderWidth: 2.5, fill: true, tension: .4, pointRadius: 3, yAxisID: 'y' },
        { label: 'No-Show Rate %', data: d.rates, borderColor: '#dc2626', backgroundColor: 'transparent', borderWidth: 2, borderDash: [5, 4], fill: false, tension: .4, pointRadius: 3, yAxisID: 'y1' },
      ],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, legend: { display: true, position: 'top', labels: { font: { size: 10 }, boxWidth: 10, padding: 12 } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 }, maxRotation: 45 } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y1: { beginAtZero: true, position: 'right', max: 60, grid: { display: false }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Capacity bar ────────────────────────────────────────── */
function renderCapacityChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ data: d.values, backgroundColor: d.colors, borderRadius: 5, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      indexAxis: 'y',
      plugins: { ...BASE_OPTS.plugins, datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 9, weight: 'bold' }, formatter: v => v + '%' } },
      scales: {
        x: { beginAtZero: true, max: 110, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } },
      },
    },
  });
}

/* ── Doctor workload combo ───────────────────────────────── */
function renderDoctorChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [
        { label: 'Appointments', data: d.totals, backgroundColor: 'rgba(37,99,235,.8)', borderRadius: 4, borderWidth: 0 },
        { type: 'line', label: 'No-Show %', data: d.rates, borderColor: '#dc2626', borderWidth: 2, pointRadius: 3, fill: false, tension: .3, yAxisID: 'y1', backgroundColor: '#dc2626' },
      ],
    },
    options: {
      ...BASE_OPTS,
      plugins: { ...BASE_OPTS.plugins, legend: { display: true, position: 'top', labels: { font: { size: 10 }, boxWidth: 10, padding: 10 } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 8 }, maxRotation: 45 } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y1: { beginAtZero: true, position: 'right', max: 60, grid: { display: false }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}

/* ── Wait time horizontal bar ────────────────────────────── */
function renderWaitChart(canvas, d) {
  const colors = d.avg_wait
    ? d.avg_wait.map(v => v > 50 ? '#dc2626' : v > 35 ? '#ca8a04' : '#16a34a')
    : DEPT_COLORS;
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ data: d.avg_wait || d.rates, backgroundColor: colors, borderRadius: 5, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      indexAxis: 'y',
      plugins: { ...BASE_OPTS.plugins, datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 9, weight: 'bold' }, formatter: v => v + ' min' } },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 9 } } },
      },
    },
  });
}

/* ── Neighbourhood bar ───────────────────────────────────── */
function renderNeighChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [{ data: d.values, backgroundColor: 'rgba(8,145,178,.8)', borderRadius: 5, borderWidth: 0 }],
    },
    options: {
      ...BASE_OPTS,
      indexAxis: 'y',
      plugins: { ...BASE_OPTS.plugins },
      scales: {
        x: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 } } },
        y: { grid: { display: false }, ticks: { font: { size: 8 } } },
      },
    },
  });
}

/* ── Condition impact grouped bar ────────────────────────── */
function renderConditionChart(canvas, d) {
  new Chart(canvas, {
    type: 'bar',
    data: {
      labels: d.labels,
      datasets: [
        { label: 'With Condition',    data: d.with_rate,    backgroundColor: 'rgba(220,38,38,.8)',  borderRadius: 5, borderWidth: 0 },
        { label: 'Without Condition', data: d.without_rate, backgroundColor: 'rgba(37,99,235,.5)',  borderRadius: 5, borderWidth: 0 },
      ],
    },
    options: {
      ...BASE_OPTS,
      plugins: {
        ...BASE_OPTS.plugins,
        legend: { display: true, position: 'top', labels: { font: { size: 10 }, boxWidth: 10, padding: 12 } },
        datalabels: { display: true, anchor: 'end', align: 'end', color: '#475569', font: { size: 9, weight: 'bold' }, formatter: v => v + '%' },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { size: 9 } } },
        y: { beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { font: { size: 9 }, callback: v => v + '%' } },
      },
    },
  });
}
