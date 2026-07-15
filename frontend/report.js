const fmt = new Intl.NumberFormat('th-TH', {maximumFractionDigits: 2});
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const documentId = Number(location.pathname.match(/\/(?:documents|reports)\/(\d+)/)?.[1]);
let sourceDocument = {document_type:'pdf', source_uri:''};

const META = {
  1:{code:'UNICEF · NEET THAILAND',summary:'สถานการณ์ ความเหลื่อมล้ำ และความพร้อมของเยาวชนที่ไม่ได้เรียน ทำงาน หรือฝึกอบรม'},
  2:{code:'WEF · FUTURE OF JOBS 2025',summary:'แนวโน้มงาน ทักษะ เทคโนโลยี และภาพอนาคตรายอุตสาหกรรมทั่วโลกในช่วงปี 2025–2030'},
  3:{code:'UNICEF · HUMAN CAPITAL',summary:'ช่องว่างทุนมนุษย์ตั้งแต่การศึกษา การเปลี่ยนผ่านสู่งาน ไปจนถึงการพัฒนาทักษะ'},
  4:{code:'TDRI · STEM WORKFORCE',summary:'ระบบการศึกษา STEM การทำงานตรงสาย และช่องว่างระหว่างการศึกษากับตลาดแรงงาน'},
  5:{code:'TDRI · THAI LABOUR DEMAND',summary:'สัญญาณความต้องการแรงงานและทักษะอาชีพจากประกาศรับสมัครงานออนไลน์'},
  6:{code:'UNICEF · PRESS RELEASE',summary:'ข้อค้นพบเรื่องขนาดของปัญหา เพศ และแรงจูงใจของเยาวชน NEET ในประเทศไทย'},
};

async function api(path){const response=await fetch(path);if(!response.ok)throw new Error(await response.text());return response.json();}
function pageHref(page){
  if(sourceDocument.document_type==='pdf')return `/api/documents/${documentId}/source#page=${encodeURIComponent(page||1)}`;
  if(/^https?:\/\//i.test(sourceDocument.source_uri||''))return sourceDocument.source_uri;
  return `/api/documents/${documentId}/pages/${page||1}`;
}
function sourceBadge(page,note=''){return `<div class="evidence"><a href="${pageHref(page)}" target="_blank" rel="noopener">หลักฐาน · หน้า ${fmt.format(page)} ↗</a>${note?`<span title="${esc(note)}">หมายเหตุ ⓘ</span>`:''}</div>`;}
function valueText(row){const unit=row.unit||row.demand_unit||'';if(unit.startsWith('%'))return `${fmt.format(row.value)}%`;if(unit==='positions')return `${fmt.format(row.value)} ตำแหน่ง`;return `${fmt.format(row.value)} ${esc(unit)}`;}

function bars(rows){
  const max=Math.max(...rows.map(r=>Math.abs(r.value||0)),1);
  return `<div class="bars">${rows.map(row=>`<article class="bar-item"><div class="bar-label"><span>${esc(row.label)}</span><strong>${valueText(row)}</strong></div><div class="bar-track"><i class="${row.value<0||row.series==='Declining'?'negative':''}" style="width:${Math.max(2,Math.abs(row.value)/max*100)}%"></i></div><div class="bar-context"><span>${esc(row.series)}${row.period?` · ${esc(row.period)}`:''}${row.scope?` · ${esc(row.scope)}`:''}</span>${sourceBadge(row.source_page,row.note)}</div></article>`).join('')}</div>`;
}
function grouped(rows){
  const groups=rows.reduce((all,row)=>((all[row.series]??=[]).push(row),all),{});
  return `<div class="group-grid">${Object.entries(groups).map(([name,items])=>`<section><h3>${esc(name)}</h3>${bars(items)}</section>`).join('')}</div>`;
}
function donut(rows){
  const colors=['#c8f05a','#76c9ac','#ffb65c','#ff7559'];let cursor=0;
  const stops=rows.map((r,i)=>{const start=cursor;cursor+=r.value;return `${colors[i]} ${start}% ${cursor}%`;}).join(',');
  return `<div class="donut-wrap"><div class="donut" style="background:conic-gradient(${stops})"><div><strong>${fmt.format(rows.reduce((s,r)=>s+r.value,0))}%</strong><span>รวมจากตาราง</span></div></div><div class="donut-list">${rows.map((r,i)=>`<div><i style="background:${colors[i]}"></i><span>${esc(r.label)}</span><strong>${fmt.format(r.value)}%</strong>${sourceBadge(r.source_page,r.note)}</div>`).join('')}</div></div>`;
}
function lineChart(rows){
  const groups=rows.reduce((all,row)=>((all[row.series]??=[]).push(row),all),{}), values=rows.map(r=>r.value||0);
  const min=Math.min(...values,0),max=Math.max(...values,1),span=max-min||1,colors=['#1d6a4e','#ff7559','#5579b8','#b27b22'];
  const paths=Object.entries(groups).map(([name,items],index)=>{const points=items.map((r,i)=>`${items.length===1?50:i/(items.length-1)*100},${92-(r.value-min)/span*84}`).join(' ');return `<polyline points="${points}" fill="none" stroke="${colors[index%colors.length]}" stroke-width="2" vector-effect="non-scaling-stroke"><title>${esc(name)}</title></polyline>`;}).join('');
  const labels=(Object.values(groups)[0]||[]).map((r,i,a)=>`<span style="left:${a.length===1?50:i/(a.length-1)*100}%">${esc(r.label)}</span>`).join('');
  return `<div class="line-chart"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="trend chart">${paths}</svg><div class="line-labels">${labels}</div><div class="line-legend">${Object.keys(groups).map((name,i)=>`<span><i style="background:${colors[i%colors.length]}"></i>${esc(name)}</span>`).join('')}</div>${sourceBadge(rows[0]?.source_page,rows[0]?.note)}</div>`;
}
function statCards(rows){return `<div class="stat-grid">${rows.map(r=>`<article><strong>${valueText(r)}</strong><p>${esc(r.label)}</p>${sourceBadge(r.source_page,r.note)}</article>`).join('')}</div>`;}
function section(id,kicker,title,visual,index){return `<section class="story-section" id="${id}"><div class="story-head"><span>${String(index).padStart(2,'0')}</span><div><p>${esc(kicker)}</p><h2>${esc(title)}</h2></div></div><div class="visual-card">${visual}</div></section>`;}
function normalizedDemand(rows,metric){return rows.filter(r=>r.metric_type===metric).map(r=>({label:r.job_role,value:metric==='net-growth-percent'?r.demand_value:r.headcount_needed/1e6,unit:metric==='net-growth-percent'?r.demand_unit:'million jobs',series:r.industry,period:`${r.year_start}–${r.year_end}`,source_page:r.source_page,note:r.note}));}

function industryCards(rows){
  const items=rows.filter(r=>r.metric_type==='net-growth-percent').sort((a,b)=>a.industry.localeCompare(b.industry));
  return `<div class="industry-grid">${items.map(r=>`<article><small>${esc(r.industry)}</small><strong>${fmt.format(r.demand_value)}%</strong><span>net role growth</span>${sourceBadge(r.source_page,r.note)}</article>`).join('')}</div>`;
}
function roleTable(demand,requirements){
  const roles=demand.filter(r=>r.metric_type==='net-growth-percent').sort((a,b)=>a.industry.localeCompare(b.industry));
  const skillMap=requirements.reduce((map,r)=>{(map[r.industry]??=[]).push(r);return map;},{});
  return `<div class="table-scroll"><table><thead><tr><th>Industry</th><th>Top growing role</th><th>Net growth</th><th>All skill signals in SQL</th><th>Source</th></tr></thead><tbody>${roles.map(r=>{const skills=(skillMap[r.industry]||[]).sort((a,b)=>b.importance_level-a.importance_level);return `<tr><td>${esc(r.industry)}</td><td>${esc(r.job_role)}</td><td><strong>${fmt.format(r.demand_value)}%</strong></td><td>${skills.length?skills.map(s=>`${esc(s.skill)} (${fmt.format(s.importance_level)}%) ${sourceBadge(s.source_page)}`).join('<br>'):'—'}</td><td>${sourceBadge(r.source_page,r.note)}</td></tr>`;}).join('')}</tbody></table></div>`;
}
const CHARTS={
  hc_stunting_trend:['ภาวะเตี้ยแคระแกร็น เด็ก 0–5 ปี','line'],hc_wasting_trend:['ภาวะผอมแห้ง เด็ก 0–5 ปี','line'],hc_overweight_trend:['ภาวะน้ำหนักเกิน เด็ก 0–5 ปี','line'],
  hc_ecdi:['เด็กที่บรรลุเกณฑ์ ECDI 2030 — 6 มิติ','grouped'],hc_foundational_skills:['ทักษะพื้นฐานแยกตามชั้นเรียน','grouped'],hc_reading_equity:['ทักษะอ่านพื้นฐานตามปัจจัยความเหลื่อมล้ำ','bar'],hc_numeracy_equity:['ทักษะคำนวณพื้นฐานตามปัจจัยความเหลื่อมล้ำ','bar'],
  hc_pisa_country:['คะแนน PISA ไทยเทียบ OECD ปี 2561 และ 2565','grouped'],hc_pisa_school_quartile:['PISA 2022 ตามควอร์ไทล์ฐานะโรงเรียน','grouped'],hc_upper_secondary_completion:['ผู้มีการศึกษา ม.ปลายขึ้นไป อายุ 25–34 ปี','bar'],human_capital_training:['การเข้าถึงและความต้องการฝึกอบรม','grouped'],
  stem_pisa_2018:['PISA 2018 คณิตศาสตร์และวิทยาศาสตร์: ไทยเทียบ OECD','grouped'],stem_school_leavers:['ผู้สำเร็จ ม.3 และ ม.6','line'],stem_vocational_students:['นักเรียนอาชีวศึกษาแยกประเภทวิชาและวุฒิ','grouped'],stem_vocational_budget:['งบประมาณอาชีวศึกษาย้อนหลัง 5 ปี','line'],stem_career_alignment:['ผู้จบ STEM ที่ทำงานในอาชีพ STEM','bar'],
  thai_job_postings:['ตำแหน่งงานออนไลน์ที่เปิดรับสูงสุด','bar'],neet_press_release:['ตัวเลขสำคัญจากข่าว UNICEF','stat']
};
function metricSection(key,rows,title,index,type){const kind=type||CHARTS[key]?.[1]||(key==='neet_groups'?'donut':key==='neet_demographics'?'grouped':'bar');const visual=kind==='donut'?donut(rows):kind==='grouped'?grouped(rows):kind==='line'?lineChart(rows):kind==='stat'?statCards(rows):bars(rows);return section(`section-${key}`,'SQL METRICS · PAGE CITED',title,visual,index);}

function renderSections(data){
  const charts=data.charts;let html='',i=1;
  if(documentId===2){
    html+=metricSection('skill_change',charts.skill_change||[],'ทักษะที่กำลังเติบโตและลดลง',i++);
    html+=section('section-transition','GLOBAL JOB TRANSITION · MILLION JOBS','งานที่เกิดขึ้น งานที่หายไป และการเปลี่ยนแปลงสุทธิ',bars(normalizedDemand(data.job_demand,'creation').concat(normalizedDemand(data.job_demand,'displacement'),normalizedDemand(data.job_demand,'net-growth'))),i++);
    html+=metricSection('macrotrends',(charts.macrotrends||[]).filter(r=>r.series!=='Technology'),'Macrotrends ที่เปลี่ยนธุรกิจ',i++);
    html+=metricSection('technology',(charts.macrotrends||[]).filter(r=>r.series==='Technology'),'Technology adoption ถึงปี 2030',i++);
    html+=section('section-industries',`${data.job_demand.filter(r=>r.metric_type==='net-growth-percent').length} INDUSTRY PROFILES`,'ภาพรวมงานรายอุตสาหกรรม',industryCards(data.job_demand),i++);
    html+=section('section-roles','ROLE + SKILL EVIDENCE','Top roles และสัญญาณทักษะรายอุตสาหกรรม',roleTable(data.job_demand,data.skill_requirements),i++);
  }else if(documentId===1){
    html+=metricSection('neet_provinces',charts.neet_provinces||[],'อัตรา NEET ตามจังหวัดและภูมิภาค',i++);
    html+=metricSection('neet_groups',charts.neet_groups||[],'เยาวชน NEET 4 กลุ่ม',i++);
    html+=metricSection('neet_demographics',charts.neet_demographics||[],'NEET ตามเพศ อายุ และการศึกษา',i++);
  }else{
    if(documentId===4||documentId===6)html+=`<aside class="quality-note"><strong>แสดงเท่าที่หลักฐานรองรับ</strong><p>เนื้อหาส่วนใหญ่เป็นเชิงคุณภาพ หน้านี้จึงไม่สร้างกราฟจากตารางนิยาม โครงสร้างหลักสูตร หรือค่าที่จับคู่กับป้ายกำกับไม่ได้อย่างแน่นอน</p></aside>`;
    Object.entries(charts).forEach(([key,rows])=>{if(rows.length)html+=metricSection(key,rows,CHARTS[key]?.[0]||key.replaceAll('_',' '),i++,CHARTS[key]?.[1]);});
    if(!Object.values(charts).flat().length)html+=`<section class="empty-state"><h2>ยังไม่มีตัวเลขที่ผ่านการถอดเป็น SQL</h2><p>เนื้อหาเอกสารยังค้นหาได้ แต่จะไม่ถูกนำมาสร้าง visualization จนกว่าจะมีค่าพร้อมแหล่งอ้างอิง</p></section>`;
  }
  document.getElementById('reportSections').innerHTML=html;
}

function setupToc(){
  const sections=[...document.querySelectorAll('.story-section')];const nav=document.getElementById('sectionNav');
  nav.innerHTML=sections.map(s=>`<a href="#${s.id}">${esc(s.querySelector('h2').textContent)}</a>`).join('');
  const links=[...nav.querySelectorAll('a')];const activate=id=>links.forEach(a=>{const active=a.hash===`#${id}`;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
  if(sections[0])activate(sections[0].id);
  const observer=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];if(visible)activate(visible.target.id);},{rootMargin:'-18% 0px -62% 0px',threshold:[0,.2,.5]});
  sections.forEach(s=>observer.observe(s));links.forEach(a=>a.addEventListener('click',()=>{activate(a.hash.slice(1));document.body.classList.remove('toc-open');}));
}

function render(data){
  const doc=data.document,meta=META[doc.id]||{code:doc.source,summary:doc.topic};sourceDocument=doc;document.title=`${doc.title} · Future Ready Talent`;
  const source=doc.document_type==='pdf'?`/api/documents/${doc.id}/source`:(/^https?:\/\//i.test(doc.source_uri||'')?doc.source_uri:`/api/documents/${doc.id}/pages/1`);
  document.getElementById('reportHero').className='report-hero';document.getElementById('reportHero').innerHTML=`<a class="back" href="/">← คลังเอกสาร</a><div><p class="hero-code">${esc(meta.code)}</p><h1>${esc(doc.title)}</h1><p class="hero-summary">${esc(meta.summary)}</p><div class="hero-meta"><span>${fmt.format(doc.page_count)} หน้า</span><span>${fmt.format(Object.values(data.charts).flat().length)} metrics</span><span>${fmt.format(data.job_demand.length)} job records</span></div></div><a class="open-source" href="${source}" target="_blank" rel="noopener">เปิดต้นฉบับ ↗</a>`;
  renderSections(data);setupToc();
}

const button=document.getElementById('tocButton');button.addEventListener('click',()=>{const open=!document.body.classList.contains('toc-open');document.body.classList.toggle('toc-open',open);button.setAttribute('aria-expanded',String(open));});document.getElementById('tocBackdrop').addEventListener('click',()=>document.body.classList.remove('toc-open'));
api(`/api/documents/${documentId}/full-data`).then(render).catch(error=>{document.getElementById('reportHero').innerHTML=`<h1>ไม่สามารถเปิดเอกสารได้</h1><p>${esc(error.message)}</p>`;});
