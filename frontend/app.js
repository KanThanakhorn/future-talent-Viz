const fmt = new Intl.NumberFormat('th-TH');
const $ = (id) => document.getElementById(id);

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
  if (rows[0]) $('chartSource').textContent = `ที่มา: ${rows[0].source_title}, หน้า ${rows[0].source_page}`;
}

async function load() {
  try {
    const [dashboard, docs] = await Promise.all([api('/api/dashboard'), api('/api/documents')]);
    const t = dashboard.totals;
    $('docCount').textContent = fmt.format(t.documents); $('pageCount').textContent = fmt.format(t.pages);
    $('chunkCount').textContent = fmt.format(t.chunks); $('reviewCount').textContent = fmt.format(t.review_pages);
    $('systemStatus').textContent = `${fmt.format(t.documents)} แหล่งข้อมูลพร้อมใช้`;
    drawChart(dashboard.job_demand);
    $('skillGrid').innerHTML = dashboard.skills.map((s, i) => `<article class="skill"><span class="rank">${String(i + 1).padStart(2, '0')}</span><h3>${s.name}</h3><span class="tag">${s.category}</span></article>`).join('');
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
    result.citations.forEach(c => { const a = document.createElement('a'); a.className = 'citation'; a.href = `/api/documents/${c.document_id}/pages/${c.page_start}`; a.target = '_blank'; a.textContent = `[${c.index}] ${c.title} · หน้า ${c.page_start}${c.page_end !== c.page_start ? `–${c.page_end}` : ''}`; cites.appendChild(a); });
    pending.after(cites);
  } catch (_) { pending.textContent = 'เกิดข้อผิดพลาดขณะค้นข้อมูล กรุณาลองใหม่'; }
  finally { button.disabled = false; messages.scrollTop = messages.scrollHeight; }
});

load();
