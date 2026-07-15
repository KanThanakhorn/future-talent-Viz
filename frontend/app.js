const fmt = new Intl.NumberFormat('th-TH', {maximumFractionDigits: 2});
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

const CARD_META = {
  1: {number:'01', code:'UNICEF · NEET', description:'สถานการณ์เยาวชนที่ไม่ได้เรียน ทำงาน หรือฝึกอบรมในประเทศไทย'},
  2: {number:'02', code:'WEF · GLOBAL', description:'แนวโน้มงาน ทักษะ เทคโนโลยี และอุตสาหกรรมทั่วโลกถึงปี 2030'},
  3: {number:'03', code:'UNICEF · HUMAN CAPITAL', description:'ช่องว่าง อุปสรรค และทางเลือกเชิงนโยบายเพื่อพัฒนาทุนมนุษย์ไทย'},
  4: {number:'04', code:'TDRI · STEM', description:'การศึกษา STEM การทำงานตรงสาย และการผลิตกำลังคนของประเทศไทย'},
  5: {number:'05', code:'TDRI · LABOUR', description:'สัญญาณความต้องการแรงงานและทักษะอาชีพจากประกาศงานออนไลน์'},
  6: {number:'06', code:'UNICEF · PRESS RELEASE', description:'ข้อค้นพบเรื่องแรงจูงใจและการกลับเข้าสู่การศึกษาและตลาดงานของเยาวชน NEET'},
};

function valueText(row) {
  if (row.unit === 'jobs') return `${fmt.format(row.value / 1e6)} ล้านตำแหน่ง`;
  if (row.unit?.startsWith('%')) return `${fmt.format(row.value)}%`;
  if (row.unit === 'positions') return `${fmt.format(row.value)} ตำแหน่ง`;
  return `${fmt.format(row.value)} ${esc(row.unit || '')}`;
}

function evidenceHref(doc, page) {
  return `/api/documents/${doc.id}/pages/${page || 1}`;
}

function card(doc) {
  const meta = CARD_META[doc.id] || {number:String(doc.id).padStart(2,'0'),code:doc.source,description:doc.topic};
  const facts = doc.highlights.length ? doc.highlights.map(fact => `<li><strong>${valueText(fact)}</strong><span>${esc(fact.label)}</span><a href="${evidenceHref(doc,fact.source_page)}" target="_blank" rel="noopener" aria-label="เปิดหลักฐานหน้า ${fact.source_page}">หลักฐาน · หน้า ${fmt.format(fact.source_page)} ↗</a></li>`).join('') : '<li class="no-data"><span>ยังไม่มีตัวเลขเชิงโครงสร้างที่มีหลักฐานในฐานข้อมูล</span></li>';
  return `<article class="document-card"><a class="card-main" href="/documents/${doc.id}" aria-label="เปิด ${esc(doc.title)}"><div class="card-top"><span>${meta.number}</span><small>${esc(meta.code)}</small><i>↗</i></div><h2>${esc(doc.title)}</h2><p>${esc(meta.description)}</p></a><ul class="highlights">${facts}</ul><div class="card-foot"><span>${esc(doc.source)}</span><a href="/documents/${doc.id}">สำรวจเอกสารเต็ม →</a></div></article>`;
}

fetch('/api/documents/highlights').then(response => {
  if (!response.ok) throw new Error('โหลดข้อมูลไม่สำเร็จ');
  return response.json();
}).then(documents => {
  document.getElementById('documentCards').innerHTML = documents.map(card).join('');
  document.getElementById('systemStatus').textContent = `${fmt.format(documents.length)} แหล่งข้อมูลพร้อมสำรวจ`;
}).catch(error => {
  document.getElementById('documentCards').innerHTML = `<p class="loading">${esc(error.message)}</p>`;
  document.getElementById('systemStatus').textContent = 'ไม่สามารถโหลดข้อมูล';
});
