const fmt = new Intl.NumberFormat('th-TH');
const $ = (id) => document.getElementById(id);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const navLinks = [...document.querySelectorAll('.sidebar nav a[href^="#"]')];
const navSections = navLinks.map(link => document.querySelector(link.hash)).filter(Boolean);
let navClickLockUntil = 0;
let navFrame = 0;

function setActiveNav(sectionId) {
  navLinks.forEach(link => {
    const active = link.hash === `#${sectionId}`;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}

function syncActiveNav() {
  navFrame = 0;
  if (Date.now() < navClickLockUntil || !navSections.length) return;
  const marker = window.scrollY + window.innerHeight * 0.35;
  let current = navSections[0];
  navSections.forEach(section => { if (section.offsetTop <= marker) current = section; });
  if (window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 2) current = navSections.at(-1);
  setActiveNav(current.id);
}

navLinks.forEach(link => link.addEventListener('click', () => {
  navClickLockUntil = Date.now() + 800;
  setActiveNav(link.hash.slice(1));
  window.setTimeout(syncActiveNav, 850);
}));
window.addEventListener('scroll', () => {
  if (!navFrame) navFrame = window.requestAnimationFrame(syncActiveNav);
}, {passive: true});
window.addEventListener('resize', syncActiveNav);
setActiveNav(location.hash.slice(1) || 'overview');

async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

function drawChart(rows) {
  const canvas = $('demandChart');
  const ctx = canvas.getContext('2d');
  const colors = ['#1d6a4e', '#ff704d', '#c8f05a'];
  const max = Math.max(...rows.map(r => r.headcount_needed), 1);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  rows.forEach((row, i) => {
    const y = 55 + i * 105;
    const width = (row.headcount_needed / max) * 500;
    ctx.fillStyle = '#edf0e9'; ctx.fillRect(150, y, 500, 48);
    ctx.fillStyle = colors[i % colors.length]; ctx.fillRect(150, y, width, 48);
    ctx.fillStyle = '#162e27'; ctx.font = '500 15px Manrope'; ctx.fillText(row.job_role, 0, y + 30);
    ctx.font = '600 18px Manrope'; ctx.fillText(`${fmt.format(row.headcount_needed / 1e6)}M`, Math.min(620, 160 + width), y + 30);
  });
  $('demandLegend').innerHTML = rows.map((r, i) => `<div class="legend-item"><i class="legend-dot" style="background:${colors[i]}"></i><span>${r.job_role} · ${r.year_start}–${r.year_end}</span></div>`).join('');
  if (rows[0]) $('chartSource').innerHTML = sourceLink(rows[0]);
}

function sourceHref(row, page = row.source_page) {
  if (row.document_type === 'web' && /^https?:\/\//i.test(row.source_uri || '')) return row.source_uri;
  return `/api/documents/${row.document_id}/source#page=${encodeURIComponent(page || 1)}`;
}

function sourceLink(row) {
  const location = row.document_type === 'web' ? 'เว็บไซต์ต้นฉบับ' : `หน้า ${row.source_page}`;
  return `<a class="source-link" target="_blank" rel="noopener noreferrer" href="${esc(sourceHref(row))}">↗ ${esc(row.source_title)} · ${location}</a>`;
}

function renderBars(target, rows, options = {}) {
  const max = Math.max(...rows.map(r => Math.abs(r.value)), 1);
  $(target).innerHTML = rows.map(row => {
    const width = Math.max(2, Math.abs(row.value) / max * 100);
    const tone = row.value < 0 || row.series === 'Declining' ? 'negative' : (row.series === 'Technology' ? 'accent' : '');
    return `<div class="bar-row"><div class="bar-meta"><span>${esc(row.label)}</span><strong>${fmt.format(row.value)}${row.unit.startsWith('%') ? '%' : ''}</strong></div><div class="bar-track"><i class="${tone}" style="width:${width}%"></i></div><div class="bar-foot"><small>${esc(row.series)} · ${esc(row.scope)}</small>${sourceLink(row)}</div></div>`;
  }).join('');
}

function renderGroups(rows) {
  const colors = ['#c8f05a','#65b891','#ffb65c','#ff704d'];
  let stop = 0; const gradient = rows.map((r, i) => { const start = stop; stop += r.value; return `${colors[i]} ${start}% ${stop}%`; }).join(',');
  $('groupChart').innerHTML = `<div class="donut" style="background:conic-gradient(${gradient})"><div><strong>${fmt.format(rows.reduce((s,r)=>s+r.value,0))}%</strong><small>classified NEET</small></div></div><div class="donut-legend">${rows.map((r,i)=>`<div><i style="background:${colors[i]}"></i><span>${esc(r.label)}</span><strong>${r.value}%</strong>${sourceLink(r)}</div>`).join('')}</div>`;
}

function renderDemographics(rows) {
  const grouped = Object.groupBy ? Object.groupBy(rows, r => r.series) : rows.reduce((a,r)=>((a[r.series]??=[]).push(r),a),{});
  $('demographicChart').innerHTML = Object.entries(grouped).map(([name, values]) => `<section><h4>${esc(name)}</h4><div class="bar-chart compact">${values.map(row=>`<div class="bar-row"><div class="bar-meta"><span>${esc(row.label)}</span><strong>${row.value}%</strong></div><div class="bar-track"><i style="width:${Math.min(100,row.value/35*100)}%"></i></div><div class="bar-foot">${sourceLink(row)}</div></div>`).join('')}</div></section>`).join('');
}

function renderGap(gap) {
  const thai = gap.thai_readiness?.[0]; const demand = gap.global_demand || [];
  $('gapChart').innerHTML = `<div class="gap-columns"><div><span class="scope-label global">GLOBAL · WEF</span><h3>Top skill demand signals</h3>${demand.map(r=>`<div class="gap-skill"><span>${esc(r.label)}</span><strong>${r.value}</strong>${sourceLink(r)}</div>`).join('')}</div><div class="gap-divider">≠</div><div><span class="scope-label thai">THAILAND · NEET</span><h3>พร้อมพัฒนาทักษะโดยรวม</h3>${thai ? `<strong class="readiness-number">${thai.value}%</strong><p>ของ classified youth NEET ต้องการพัฒนาทักษะ ไม่ใช่ readiness รายทักษะ</p>${sourceLink(thai)}` : '<p>ยังไม่มีข้อมูล</p>'}</div></div><div class="data-required"><b>DATA REQUIRED</b><p>${esc(gap.message)}</p><small>ชั้นที่ 3 “Thai curriculum coverage” จะแสดงเมื่อมีข้อมูลเชิงปริมาณรายทักษะจากหลักสูตร/STEM</small></div>`;
}

async function load() {
  try {
    const [dashboard, docs] = await Promise.all([api('/api/dashboard'), api('/api/documents')]);
    const t = dashboard.totals;
    $('docCount').textContent = fmt.format(t.documents); $('pageCount').textContent = fmt.format(t.pages);
    $('chunkCount').textContent = fmt.format(t.chunks); $('reviewCount').textContent = fmt.format(t.review_pages);
    $('systemStatus').textContent = `${fmt.format(t.documents)} แหล่งข้อมูลพร้อมใช้`;
    drawChart(dashboard.job_demand);
    renderBars('skillChangeChart', dashboard.charts.skill_change || []);
    renderBars('macroTrendChart', dashboard.charts.macrotrends || []);
    renderBars('provinceChart', dashboard.charts.neet_provinces || []);
    renderGroups(dashboard.charts.neet_groups || []);
    renderDemographics(dashboard.charts.neet_demographics || []);
    renderGap(dashboard.charts.demand_readiness_gap);
    $('documents').innerHTML = docs.map(d => `<a class="document" href="${d.document_type === 'pdf' ? `/api/documents/${d.id}/source` : d.source_uri}" target="_blank" rel="noreferrer"><span class="document-icon">${d.document_type.toUpperCase()}</span><div><h3>${d.title}</h3><p>${d.source} · ${d.topic}</p></div><span>${d.page_count || 1} หน้า</span><small>${d.review_pages ? `review ${d.review_pages}` : 'พร้อมใช้'} ↗</small></a>`).join('') || '<div class="loading">ยังไม่มีเอกสาร — รัน ingestion ก่อน</div>';
  } catch (error) { $('systemStatus').textContent = 'ไม่สามารถโหลดข้อมูล'; console.error(error); }
}

$('chatForm').addEventListener('submit', async (event) => {
  event.preventDefault(); const input = $('question'); const question = input.value.trim(); if (!question) return;
  const messages = $('messages'); const button = event.currentTarget.querySelector('button');
  messages.insertAdjacentHTML('beforeend', `<div class="message user"></div>`); messages.lastElementChild.textContent = question;
  input.value = ''; button.disabled = true;
  const pending = document.createElement('div'); pending.className = 'message assistant'; pending.textContent = 'กำลังค้นหลักฐาน…'; messages.appendChild(pending); messages.scrollTop = messages.scrollHeight;
  try {
    const result = await api('/api/chat', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({question})});
    pending.textContent = result.answer;
    const cites = document.createElement('div'); cites.className = 'citations';
    result.citations.forEach(c => { const a = document.createElement('a'); a.className = 'citation'; a.href = sourceHref(c, c.page_start); a.target = '_blank'; a.rel = 'noopener noreferrer'; const location = c.document_type === 'web' ? 'เว็บไซต์ต้นฉบับ' : `หน้า ${c.page_start}${c.page_end !== c.page_start ? `–${c.page_end}` : ''}`; a.textContent = `[${c.index}] ${c.title} · ${location} · ${c.source_type === 'chart_ocr' ? 'OCR chart' : 'narrative'}`; cites.appendChild(a); });
    pending.after(cites);
  } catch (_) { pending.textContent = 'เกิดข้อผิดพลาดขณะค้นข้อมูล กรุณาลองใหม่'; }
  finally { button.disabled = false; messages.scrollTop = messages.scrollHeight; }
});

load();
