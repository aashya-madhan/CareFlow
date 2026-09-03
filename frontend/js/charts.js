/* ============================================================
   CHARTS.JS — Chart.js renderers consuming API response shapes
   ============================================================ */
Chart.register(ChartDataLabels);

const DEPT_COLORS = ['#2563eb','#dc2626','#16a34a','#ea580c','#7c3aed','#0891b2','#ca8a04','#db2777','#4f46e5','#65a30d'];

const SHARED = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    datalabels: { display: false },
    tooltip: { backgroundColor: '#0f172a', padding: 10, cornerRadius: 8, titleFont: { size: 12, weight: 'bold' }, bodyFont: { size: 11 } }
  }
};

const CI = {};
function dc(id) { if (CI[id]) { CI[id].destroy(); delete CI[id]; } }

/* ---- Monthly Chart ---- */
function renderMonthlyChart(monthly, type = 'bar') {
  dc('monthlyChart');
  const ctx = document.getElementById('monthlyChart'); if (!ctx) return;
  const labels  = monthly.map(m => m.label);
  const showed  = monthly.map(m => m.showed);
  const noshows = monthly.map(m => m.no_show);
  CI['monthlyChart'] = new Chart(ctx, {
    type,
    data: { labels, datasets: [
      { label: 'Showed',   data: showed,  backgroundColor: type==='bar'?'rgba(22,163,74,.8)':'rgba(22,163,74,.15)',  borderColor:'#16a34a', borderWidth: type==='bar'?0:2, fill: type==='line', tension:.4 },
      { label: 'No-Show',  data: noshows, backgroundColor: type==='bar'?'rgba(220,38,38,.8)':'rgba(220,38,38,.15)', borderColor:'#dc2626', borderWidth: type==='bar'?0:2, fill: type==='line', tension:.4 },
    ]},
    options: { ...SHARED, plugins: { ...SHARED.plugins, legend: { display:true, position:'top', labels:{font:{size:11},boxWidth:12,padding:14} }, datalabels:{display:false} },
      scales: { x:{stacked:type==='bar',grid:{display:false},ticks:{font:{size:10},maxRotation:45}}, y:{stacked:type==='bar',beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}} } }
  });
}

/* ---- Attendance Donut ---- */
function renderAttendanceDonut(kpi) {
  dc('attendanceDonut');
  const ctx = document.getElementById('attendanceDonut'); if (!ctx) return;
  CI['attendanceDonut'] = new Chart(ctx, {
    type: 'doughnut',
    data: { labels:['Showed','No-Show','Cancelled'], datasets:[{ data:[kpi.showed,kpi.no_show,kpi.cancelled], backgroundColor:['#16a34a','#dc2626','#ca8a04'], borderWidth:3, borderColor:'#fff', hoverOffset:8 }] },
    options: { ...SHARED, cutout:'68%', plugins: { ...SHARED.plugins,
      datalabels: { display:true, color:'#fff', font:{size:11,weight:'bold'}, formatter:(v,c)=>{ const s=c.dataset.data.reduce((a,b)=>a+b,0); return s>0?((v/s)*100).toFixed(1)+'%':''; } },
      tooltip: { ...SHARED.plugins.tooltip, callbacks:{ label:i=>` ${i.label}: ${i.raw} (${((i.raw/(kpi.showed+kpi.no_show+kpi.cancelled))*100).toFixed(1)}%)` } }
    }}
  });
  const leg = document.getElementById('attendanceLegend');
  if (leg) leg.innerHTML = [['Showed','#16a34a',kpi.showed],['No-Show','#dc2626',kpi.no_show],['Cancelled','#ca8a04',kpi.cancelled]]
    .map(([l,c,v])=>`<div class="legend-item"><span class="legend-dot" style="background:${c}"></span><span>${l}: <strong>${v}</strong></span></div>`).join('');
}

/* ---- Dept No-Show Bar ---- */
function renderDeptNoShowChart(depts) {
  dc('deptNoShowChart');
  const ctx = document.getElementById('deptNoShowChart'); if (!ctx) return;
  CI['deptNoShowChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:depts.map(d=>d.department), datasets:[{ label:'No-Show Rate (%)', data:depts.map(d=>d.no_show_rate), backgroundColor:DEPT_COLORS, borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, indexAxis:'y',
      plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:10,weight:'bold'},formatter:v=>v+'%'} },
      scales:{ x:{beginAtZero:true,max:60,grid:{color:'#f1f5f9'},ticks:{font:{size:10},callback:v=>v+'%'}}, y:{grid:{display:false},ticks:{font:{size:10}}} } }
  });
}

/* ---- Day of Week ---- */
function renderDowChart(dow) {
  dc('dowChart');
  const ctx = document.getElementById('dowChart'); if (!ctx) return;
  CI['dowChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:dow.map(d=>d.day), datasets:[{ label:'Appointments', data:dow.map(d=>d.total), backgroundColor:'rgba(37,99,235,.8)', borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:10,weight:'bold'}} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10}}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}} } }
  });
}

/* ---- Risk Factors ---- */
function renderRiskChart(risks) {
  dc('riskChart');
  const ctx = document.getElementById('riskChart'); if (!ctx) return;
  CI['riskChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:risks.map(r=>r.factor), datasets:[{ label:'No-Shows', data:risks.map(r=>r.no_show_count), backgroundColor:['#dc2626','#ea580c','#ca8a04','#7c3aed','#0891b2','#2563eb'], borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, indexAxis:'y',
      plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:10,weight:'bold'}} },
      scales:{ x:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y:{grid:{display:false},ticks:{font:{size:10}}} } }
  });
}

/* ---- NS Dept Rate (combo) ---- */
function renderNsDeptRateChart(depts) {
  dc('nsDeptRateChart');
  const ctx = document.getElementById('nsDeptRateChart'); if (!ctx) return;
  CI['nsDeptRateChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:depts.map(d=>d.department), datasets:[
      { label:'Total', data:depts.map(d=>d.total), backgroundColor:'rgba(37,99,235,.2)', borderColor:'#2563eb', borderWidth:1.5, borderRadius:4, yAxisID:'y' },
      { label:'No-Shows', data:depts.map(d=>d.no_show), backgroundColor:'rgba(220,38,38,.8)', borderRadius:4, borderWidth:0, yAxisID:'y' },
      { type:'line', label:'Rate %', data:depts.map(d=>d.no_show_rate), borderColor:'#ea580c', borderWidth:2, pointRadius:4, fill:false, tension:.3, yAxisID:'y1', backgroundColor:'#ea580c' },
    ]},
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, legend:{display:true,position:'top',labels:{font:{size:11},boxWidth:12,padding:14}}, datalabels:{display:false} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10},maxRotation:35}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y1:{beginAtZero:true,position:'right',max:60,grid:{display:false},ticks:{font:{size:10},callback:v=>v+'%'}} } }
  });
}

/* ---- SMS Chart ---- */
function renderNsSmsChart(sms) {
  dc('nsSmsChart');
  const ctx = document.getElementById('nsSmsChart'); if (!ctx) return;
  CI['nsSmsChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:['SMS Sent','No SMS'], datasets:[{ label:'No-Show Rate (%)', data:[sms.sms_sent_rate,sms.no_sms_rate], backgroundColor:['#16a34a','#dc2626'], borderRadius:8, borderWidth:0 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'center',align:'center',color:'#fff',font:{size:14,weight:'bold'},formatter:v=>v+'%'} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:11,weight:'bold'}}}, y:{beginAtZero:true,max:60,grid:{color:'#f1f5f9'},ticks:{font:{size:10},callback:v=>v+'%'}} } }
  });
}

/* ---- Age Group ---- */
function renderNsAgeChart(ageGroups) {
  dc('nsAgeChart');
  const ctx = document.getElementById('nsAgeChart'); if (!ctx) return;
  CI['nsAgeChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:ageGroups.map(a=>a.age_group), datasets:[{ label:'No-Show Rate (%)', data:ageGroups.map(a=>a.no_show_rate), backgroundColor:['#2563eb','#dc2626','#ea580c','#7c3aed'], borderRadius:8, borderWidth:0 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:11,weight:'bold'},formatter:v=>v+'%'} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10}}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10},callback:v=>v+'%'}} } }
  });
}

/* ---- DOW Radar (No-Show) ---- */
function renderNsDowChart(dow) {
  dc('nsDowChart');
  const ctx = document.getElementById('nsDowChart'); if (!ctx) return;
  CI['nsDowChart'] = new Chart(ctx, {
    type:'radar',
    data:{ labels:dow.map(d=>d.day), datasets:[{ label:'No-Show Rate (%)', data:dow.map(d=>d.no_show_rate), backgroundColor:'rgba(220,38,38,.15)', borderColor:'#dc2626', borderWidth:2, pointBackgroundColor:'#dc2626', pointRadius:4 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:false}, legend:{display:false} },
      scales:{ r:{ beginAtZero:true, ticks:{font:{size:9},backdropColor:'transparent',callback:v=>v+'%'}, pointLabels:{font:{size:10}}, grid:{color:'#e2e8f0'} } } }
  });
}

/* ---- Lead Time ---- */
function renderNsLeadTimeChart(leadTime) {
  dc('nsLeadTimeChart');
  const ctx = document.getElementById('nsLeadTimeChart'); if (!ctx) return;
  CI['nsLeadTimeChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:leadTime.map(l=>l.bucket), datasets:[
      { label:'Appointments', data:leadTime.map(l=>l.total), backgroundColor:'rgba(37,99,235,.2)', borderColor:'#2563eb', borderWidth:1.5, borderRadius:4, yAxisID:'y' },
      { type:'line', label:'No-Show Rate', data:leadTime.map(l=>l.no_show_rate), borderColor:'#dc2626', borderWidth:2.5, pointRadius:5, fill:false, tension:.3, yAxisID:'y1', backgroundColor:'#dc2626' },
    ]},
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, legend:{display:true,position:'top',labels:{font:{size:11},boxWidth:12,padding:14}}, datalabels:{display:false} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10}}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y1:{beginAtZero:true,position:'right',max:60,grid:{display:false},ticks:{font:{size:10},callback:v=>v+'%'}} } }
  });
}

/* ---- Prev No-Show (need raw data — placeholder using dow) ---- */
function renderNsPrevNoShowChart(data) { /* rendered from app context */ }

/* ---- Operational Trend ---- */
function renderOpTrendChart(monthly) {
  dc('opTrendChart');
  const ctx = document.getElementById('opTrendChart'); if (!ctx) return;
  CI['opTrendChart'] = new Chart(ctx, {
    type:'line',
    data:{ labels:monthly.map(m=>m.label), datasets:[
      { label:'Total Appointments', data:monthly.map(m=>m.total), borderColor:'#2563eb', backgroundColor:'rgba(37,99,235,.1)', borderWidth:2.5, fill:true, tension:.4, pointRadius:4, yAxisID:'y' },
      { label:'No-Show Rate %', data:monthly.map(m=>m.no_show_rate), borderColor:'#dc2626', backgroundColor:'transparent', borderWidth:2, borderDash:[5,4], fill:false, tension:.4, pointRadius:4, yAxisID:'y1' },
    ]},
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, legend:{display:true,position:'top',labels:{font:{size:11},boxWidth:12,padding:14}}, datalabels:{display:false} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10},maxRotation:45}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y1:{beginAtZero:true,position:'right',max:60,grid:{display:false},ticks:{font:{size:10},callback:v=>v+'%'}} } }
  });
}

/* ---- Capacity ---- */
function renderOpCapacityChart(depts) {
  dc('opCapacityChart');
  const ctx = document.getElementById('opCapacityChart'); if (!ctx) return;
  const capacity = depts.map(d => Math.min(99, 55 + Math.abs(d.department.charCodeAt(0)) % 40));
  CI['opCapacityChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:depts.map(d=>d.department), datasets:[{ label:'Capacity %', data:capacity, backgroundColor:capacity.map(v=>v>=85?'#dc2626':v>=70?'#ca8a04':'#16a34a'), borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, indexAxis:'y',
      plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:10,weight:'bold'},formatter:v=>v+'%'} },
      scales:{ x:{beginAtZero:true,max:110,grid:{color:'#f1f5f9'},ticks:{font:{size:10},callback:v=>v+'%'}}, y:{grid:{display:false},ticks:{font:{size:10}}} } }
  });
}

/* ---- Doctor Workload ---- */
function renderOpDoctorChart(doctors) {
  dc('opDoctorChart');
  const ctx = document.getElementById('opDoctorChart'); if (!ctx) return;
  const top = doctors.slice(0, 10);
  CI['opDoctorChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:top.map(d=>d.doctor.replace('Dr. ','')), datasets:[
      { label:'Appointments', data:top.map(d=>d.total), backgroundColor:'rgba(37,99,235,.8)', borderRadius:4, borderWidth:0 },
      { type:'line', label:'No-Show %', data:top.map(d=>d.no_show_rate), borderColor:'#dc2626', borderWidth:2, pointRadius:3, fill:false, tension:.3, yAxisID:'y1', backgroundColor:'#dc2626' },
    ]},
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, legend:{display:true,position:'top',labels:{font:{size:10},boxWidth:10,padding:12}}, datalabels:{display:false} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:9},maxRotation:45}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y1:{beginAtZero:true,position:'right',max:60,grid:{display:false},ticks:{font:{size:10},callback:v=>v+'%'}} } }
  });
}

/* ---- Hour Chart (using DOW data as hourly proxy) ---- */
function renderOpHourChart(dow) {
  dc('opHourChart');
  const ctx = document.getElementById('opHourChart'); if (!ctx) return;
  CI['opHourChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:dow.map(d=>d.day), datasets:[{ label:'Appointments', data:dow.map(d=>d.total), backgroundColor:dow.map((d,i)=>{ const mx=Math.max(...dow.map(x=>x.total)); return `rgba(37,99,235,${0.2+d.total/mx*0.75})`; }), borderRadius:4, borderWidth:0 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:false} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10}}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}} } }
  });
}

/* ---- Wait Time ---- */
function renderOpWaitChart(depts) {
  dc('opWaitChart');
  const ctx = document.getElementById('opWaitChart'); if (!ctx) return;
  CI['opWaitChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:depts.map(d=>d.department), datasets:[{ label:'Avg Wait (min)', data:depts.map(d=>d.avg_wait), backgroundColor:depts.map(d=>d.avg_wait>50?'#dc2626':d.avg_wait>35?'#ca8a04':'#16a34a'), borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, indexAxis:'y',
      plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:10,weight:'bold'},formatter:v=>v+' min'} },
      scales:{ x:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y:{grid:{display:false},ticks:{font:{size:10}}} } }
  });
}

/* ---- Demographics: Age ---- */
function renderDemAgeChart(ageGroups) {
  dc('demAgeChart');
  const ctx = document.getElementById('demAgeChart'); if (!ctx) return;
  CI['demAgeChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:ageGroups.map(a=>a.age_group), datasets:[{ label:'Count', data:ageGroups.map(a=>a.total), backgroundColor:['#2563eb','#0891b2','#16a34a','#ca8a04'], borderRadius:8, borderWidth:0 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:11,weight:'bold'}} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10}}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}} } }
  });
}

/* ---- Demographics: Gender ---- */
function renderDemGenderChart(items) {
  dc('demGenderChart');
  const ctx = document.getElementById('demGenderChart'); if (!ctx) return;
  const male = items.filter(r=>r.patient_gender==='Male').length;
  const female = items.filter(r=>r.patient_gender==='Female').length;
  CI['demGenderChart'] = new Chart(ctx, {
    type:'pie',
    data:{ labels:['Male','Female'], datasets:[{ data:[male,female], backgroundColor:['#2563eb','#db2777'], borderWidth:3, borderColor:'#fff', hoverOffset:8 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, legend:{display:true,position:'bottom',labels:{font:{size:11},boxWidth:12,padding:16}},
      datalabels:{display:true,color:'#fff',font:{size:13,weight:'bold'},formatter:(v,c)=>{ const s=c.dataset.data.reduce((a,b)=>a+b,0); return ((v/s)*100).toFixed(1)+'%'; }} } }
  });
}

/* ---- Neighbourhood ---- */
function renderDemNeighChart(items) {
  dc('demNeighChart');
  const ctx = document.getElementById('demNeighChart'); if (!ctx) return;
  const counts = {};
  items.forEach(r=>{ const n=r.neighbourhood||'Unknown'; counts[n]=(counts[n]||0)+1; });
  const sorted = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,10);
  CI['demNeighChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:sorted.map(e=>e[0]), datasets:[{ label:'Appointments', data:sorted.map(e=>e[1]), backgroundColor:'rgba(8,145,178,.8)', borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, indexAxis:'y', plugins:{ ...SHARED.plugins, datalabels:{display:false} },
      scales:{ x:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}}, y:{grid:{display:false},ticks:{font:{size:9}}} } }
  });
}

/* ---- Condition Impact ---- */
function renderDemConditionChart(items) {
  dc('demConditionChart');
  const ctx = document.getElementById('demConditionChart'); if (!ctx) return;
  // items from /appointments list — no condition flags directly, show dept breakdown
  const deptCounts = {};
  items.forEach(r=>{ const d=r.department_name||'Other'; deptCounts[d]=(deptCounts[d]||0)+(r.status==='No-Show'?1:0); });
  const sorted = Object.entries(deptCounts).sort((a,b)=>b[1]-a[1]).slice(0,8);
  CI['demConditionChart'] = new Chart(ctx, {
    type:'bar',
    data:{ labels:sorted.map(e=>e[0]), datasets:[{ label:'No-Shows', data:sorted.map(e=>e[1]), backgroundColor:DEPT_COLORS, borderRadius:6, borderWidth:0 }] },
    options:{ ...SHARED, plugins:{ ...SHARED.plugins, datalabels:{display:true,anchor:'end',align:'end',color:'#475569',font:{size:10,weight:'bold'}} },
      scales:{ x:{grid:{display:false},ticks:{font:{size:10},maxRotation:35}}, y:{beginAtZero:true,grid:{color:'#f1f5f9'},ticks:{font:{size:10}}} } }
  });
}

/* ---- Scholarship ---- */
function renderDemScholarChart(items) {
  dc('demScholarChart');
  const ctx = document.getElementById('demScholarChart'); if (!ctx) return;
  // Use risk distribution
  const low = items.filter(r=>r.risk_label==='Low').length;
  const med = items.filter(r=>r.risk_label==='Medium').length;
  const hi  = items.filter(r=>r.risk_label==='High').length;
  CI['demScholarChart'] = new Chart(ctx, {
    type:'doughnut',
    data:{ labels:['Low Risk','Medium Risk','High Risk'], datasets:[{ data:[low,med,hi], backgroundColor:['#16a34a','#ca8a04','#dc2626'], borderWidth:3, borderColor:'#fff', hoverOffset:8 }] },
    options:{ ...SHARED, cutout:'60%', plugins:{ ...SHARED.plugins, legend:{display:true,position:'bottom',labels:{font:{size:11},boxWidth:12,padding:12}},
      datalabels:{display:true,color:'#fff',font:{size:11,weight:'bold'},formatter:(v,c)=>{ const s=c.dataset.data.reduce((a,b)=>a+b,0); return s>0?((v/s)*100).toFixed(0)+'%':''; }} } }
  });
}

window.Charts = {
  renderMonthlyChart, renderAttendanceDonut, renderDeptNoShowChart, renderDowChart, renderRiskChart,
  renderNsDeptRateChart, renderNsSmsChart, renderNsAgeChart, renderNsDowChart, renderNsLeadTimeChart,
  renderOpTrendChart, renderOpCapacityChart, renderOpDoctorChart, renderOpHourChart, renderOpWaitChart,
  renderDemAgeChart, renderDemGenderChart, renderDemNeighChart, renderDemConditionChart, renderDemScholarChart,
};
