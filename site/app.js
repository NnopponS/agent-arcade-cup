'use strict';
(() => {
  const $ = selector => document.querySelector(selector);
  const e = (tag, cls, value) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value !== undefined) node.textContent = String(value);
    return node;
  };
  const svgNS = 'http://www.w3.org/2000/svg';
  const sv = (tag, traits = {}) => {
    const node = document.createElementNS(svgNS, tag);
    for (const [k, v] of Object.entries(traits)) node.setAttribute(k, String(v));
    return node;
  };
  const icon = name => {
    const svg = sv('svg', {class:'icon', 'aria-hidden':'true'});
    svg.append(sv('use', {href:'#i-' + name}));
    return svg;
  };

  const phases = new Map([['qualifier','รอบคัดเลือก'], ['knockout','รอบแพ้คัดออก'], ['pilot','รอบนำร่อง'], ['exhibition','รอบสาธิต']]);
  const results = new Map([['engine','เล่นจริง'], ['tie','เสมอ'], ['forfeit','แพ้ผ่าน'], ['pilot','รอบนำร่อง'], ['exhibition','รอบสาธิต']]);
  const units = new Map([['hp','HP'], ['points','คะแนน'], ['moves','ครั้ง'], ['hits','ครั้งที่โดนเป้า']]);
  const resultWord = match => results.get(match.result) || 'ผลที่บันทึก';
  const goodID = id => typeof id === 'string' && /^[A-Z][0-9]{2,4}(?:-[A-Z0-9]{1,4})?$/.test(id);
  const nfmt = new Intl.NumberFormat('th-TH');
  const count = n => nfmt.format(n);
  const normalize = text => String(text).normalize('NFKC').trim().toLowerCase();
  const number = n => typeof n === 'number' && Number.isFinite(n) && n >= 0;
  const validPair = pair => Array.isArray(pair) && pair.length === 2 && pair.every(number);
  const textArray = x => Array.isArray(x) ? x.filter(item => typeof item === 'string' && item.trim()) : [];
  const route = id => '#match-' + id;
  const reasonPhrase = reason => ({
    time: 'ครบเวลาตามกติกา',
    'invalid-submission-forfeit': 'แพ้ผ่าน: คำสั่งที่ส่งไม่ผ่านการตรวจสอบ'
  })[reason] || null;
  const pageSize = 15;
  let records = [];
  let byID = new Map();
  let filtered = [];
  let page = 1;
  let selected = null;

  // All data-derived UI is plain text. No log HTML or external URLs are interpreted.
  function verifyData(data) {
    if (!data || data.schema !== 1 || !Array.isArray(data.matches) || !data.summary || !data.matches.length)
      throw new Error('Invalid or empty public dataset');
    if (data.matches.length !== data.summary.rows) throw new Error('Archive total does not match');
    const ids = new Set();
    for (const m of data.matches) {
      if (!m || !goodID(m.id) || ids.has(m.id) || !phases.has(m.stage) || !results.has(m.result) ||
          !['fighting','pilot','exhibition'].includes(m.series) ||
          ![m.game,m.a,m.b].every(v => typeof v === 'string' && v.trim() && v.length <= 55) ||
          (m.winner !== null && m.winner !== m.a && m.winner !== m.b) ||
          (m.score !== null && (!validPair(m.score) || !units.has(m.scoreUnit))) ||
          (m.moves !== null && !validPair(m.moves)) || (m.frame !== null && !number(m.frame)) ||
          !Array.isArray(m.checkpoints) || !m.checkpoints.every(c => c && [c.frame,c.a,c.b].every(number)) ||
          (m.rematchOf !== null && !goodID(m.rematchOf))) throw new Error('Invalid public record');
      ids.add(m.id);
    }
    return data.matches;
  }

  function addOptions(select, choices) {
    for (const [value,label] of choices) {
      const o = e('option', '', label);
      o.value = value;
      select.append(o);
    }
  }

  function displayMetrics(summary) {
    const totals = [records.length, summary.physical, summary.pilotRows];
    if (!totals.every(number)) return;
    ['#stat-matches','#stat-phases','#stat-games'].forEach((id,i) => $(id).textContent = count(totals[i]));
    $('#metrics').hidden = false;
  }

  function criteria() {
    return {
      q: normalize($('#query').value).split(/\s+/u).filter(Boolean),
      stage: $('#phase-filter').value, game: $('#game-filter').value,
      desc: $('#sort').value === 'desc'
    };
  }

  function filterList() {
    const picking = criteria();
    filtered = records.filter(m => {
      if (picking.stage && m.stage !== picking.stage || picking.game && m.game !== picking.game) return false;
      const fields = normalize([m.id,m.a,m.b,m.game,m.winner,m.stage,phases.get(m.stage),m.result,resultWord(m),m.rematchOf].join(' '));
      return picking.q.every(word => fields.includes(word));
    });
    if (picking.desc) filtered.reverse();
    page = 1;
    renderList();
  }

  function matchRow(m) {
    const row = e('li','match-row');
    const link = e('a','record');
    link.href = route(m.id);
    if (selected === m.id) link.setAttribute('aria-current','true');
    const main = e('span','record-main');
    main.append(e('strong','record-title',m.a + ' vs ' + m.b));
    const metadata = [m.game];
    if (m.winner) metadata.push('ชนะ: ' + m.winner);
    else if (m.result === 'tie') metadata.push('ผลเสมอ');
    main.append(e('span','record-meta',metadata.join(' · ')), e('span','record-phase',phases.get(m.stage)));
    const result = e('span','record-result'); result.append(e('span','result-chip ' + m.result,resultWord(m)));
    const arrow = e('span','record-arrow'); arrow.append(icon('right'));
    main.append(result); link.append(e('span','record-id',m.id),main,arrow); row.append(link);
    return row;
  }

  function renderList() {
    const pages = Math.ceil(filtered.length / pageSize);
    page = Math.max(1,Math.min(page,pages || 1));
    const start = (page - 1) * pageSize;
    const end = Math.min(start + pageSize, filtered.length);
    const statusText = filtered.length
      ? `แสดง ${count(start + 1)}–${count(end)} จาก ${count(filtered.length)} รายการ`
      : 'ไม่พบแมตช์';
    $('#list-status').textContent = statusText;
    $('#reset').disabled = !($('#query').value || $('#game-filter').value || $('#phase-filter').value || $('#sort').value !== 'asc');
    $('#match-list').replaceChildren(...filtered.slice(start,end).map(matchRow));
    $('#no-matches').hidden = filtered.length > 0;
    $('#pagination').hidden = pages <= 1;
    $('#page-prev').disabled = page <= 1;
    $('#page-next').disabled = page >= pages;
    $('#page-number').textContent = `หน้า ${count(page)} / ${count(pages)}`;
  }

  function field(list,label,value) {
    if (value === null || value === undefined || value === '') return;
    const el = e('div'), dd = e('dd');
    if (typeof value === 'string') dd.textContent = value;
    else dd.append(value);
    el.append(e('dt','',label),dd); list.append(el);
  }

  function makeHPChart(m) {
    const checkpoints = [...m.checkpoints].sort((a,b) => a.frame - b.frame);
    if (checkpoints.length < 2) return null;
    const figure = e('figure','chart-figure');
    const ns = sv('svg',{viewBox:'0 0 520 172', 'aria-hidden':'true'});
    const maxFrame = Math.max(checkpoints.at(-1).frame, 1);
    const values = checkpoints.flatMap(c => [c.a,c.b]);
    const low = Math.floor(Math.min(...values)/10)*10;
    const high = Math.max(low+10,Math.ceil(Math.max(...values)/10)*10);
    const x = frame => 45 + 459*(frame/maxFrame);
    const y = hp => 139 - 112*((hp-low)/(high-low));
    const label = (text,traits) => {const el = sv('text',traits); el.textContent = text; ns.append(el);};
    const faint = '#b2a68f', muted = '#534738';
    const textStyle = {'font-size':11,fill:muted,'font-family':'system-ui,sans-serif'};
    for (const hp of [...new Set([high, Math.round((high+low)/2), low])]) {
      ns.append(sv('line',{x1:45,x2:504,y1:y(hp),y2:y(hp),stroke:faint,'stroke-opacity':'.65'}));
      label(hp,{...textStyle,x:38,y:y(hp)+4,'text-anchor':'end'});
    }
    ns.append(sv('path',{d:'M45 26v114h460',fill:'none',stroke:faint}));
    label('HP',{...textStyle,x:9,y:16,'font-weight':700});
    label('0',{...textStyle,x:45,y:159,'text-anchor':'middle'});
    label(maxFrame,{...textStyle,x:504,y:159,'text-anchor':'end'});
    label('frame',{...textStyle,x:270,y:159,'text-anchor':'middle'});
    const curves = [['a','#7c3421',false],['b','#305244',true]];
    for (const [key, color, dashed] of curves) {
      const curve = sv('polyline',{
        points: checkpoints.map(c => `${x(c.frame)},${y(c[key])}`).join(' '),
        'stroke-width':2.25,fill:'none',stroke:color,'stroke-linecap':'round','stroke-linejoin':'round'
      });
      if (dashed) curve.setAttribute('stroke-dasharray','5 4');
      ns.append(curve);
      for (const c of [checkpoints[0],checkpoints.at(-1)]) {
        ns.append(dashed
          ? sv('rect',{x:x(c.frame)-2.5,y:y(c[key])-2.5,width:5,height:5,fill:color})
          : sv('circle',{cx:x(c.frame),cy:y(c[key]),r:3,fill:color}));
      }
    }
    const description = `เส้นทึบ: ${m.a} · เส้นประ: ${m.b} · มี ${count(checkpoints.length)} จุดวัด ไม่ใช่ข้อมูลทุกเฟรม · แกน HP ซูมตามค่าที่วัดได้`;
    figure.append(ns,e('figcaption','',description));
    const exact = e('details','checkpoint-details'); exact.append(e('summary','','ดูตัวเลข HP ตามเฟรม'));
    const table = e('table','checkpoint-table'), header = e('thead'), body = e('tbody');
    const headerRow = e('tr');
    for (const labelText of ['เฟรม',m.a + ' (HP)',m.b + ' (HP)']) {
      const cell = e('th','',labelText); cell.scope = 'col'; headerRow.append(cell);
    }
    header.append(headerRow);
    for (const c of checkpoints) {
      const row = e('tr'); row.append(...[c.frame,c.a,c.b].map(item => e('td','',count(item)))); body.append(row);
    }
    table.append(header,body); exact.append(table);
    return [e('h4','','HP ที่บันทึกระหว่างไฟต์'),figure,exact];
  }

  function showMatch(m, useFocus) {
    selected = m.id;
    $('#match-status').hidden = true;
    const panel = $('#match-detail');
    $('#detail-serial').textContent = m.id + ' / ' + phases.get(m.stage);
    $('#detail-title').textContent = m.a + ' vs ' + m.b;
    $('#detail-lead').textContent = m.game + ' · ' + resultWord(m);
    const fields = $('#detail-fields'); fields.replaceChildren();
    field(fields,'ผู้ชนะที่บันทึก', m.winner || (m.result === 'tie' ? 'เสมอ' : 'ไม่มีผู้ชนะในผลที่เผยแพร่'));
    if (m.result !== 'forfeit' && validPair(m.score)) field(fields,'ค่าที่บันทึก (A : B)',m.score.map(count).join(' : ') + ' ' + units.get(m.scoreUnit));
    if (validPair(m.moves) && m.scoreUnit !== 'moves') field(fields,'จำนวนการเดิน (A : B)',m.moves.map(count).join(' : '));
    if (number(m.frame)) field(fields,m.result === 'forfeit' ? 'เฟรมที่ยุติก่อนเล่นต่อ' : 'เฟรมสิ้นสุด',count(m.frame));
    field(fields,'สาเหตุที่บันทึก',reasonPhrase(m.reason));
    if (m.rematchOf && byID.has(m.rematchOf)) {
      const link = e('a','',m.rematchOf); link.href = route(m.rematchOf);
      field(fields,'แข่งซ้ำจาก',link);
    }
    const rematches = records.filter(r => r.rematchOf === m.id);
    if (rematches.length) {
      const link = e('a','',rematches[0].id); link.href = route(rematches[0].id);
      field(fields,'แมตช์ที่แข่งซ้ำ',link);
    }
    const notes = [];
    if (m.series === 'pilot') {
      notes.push('รอบนำร่องใช้บอตคนละชุดกับ FightingICE และไม่รวมอยู่ในผลการแข่งขันชุดหลัก');
      if (m.scoreUnit === 'moves' || m.scoreUnit === 'hits') notes.push('จำนวนการเดินหรือจำนวนครั้งที่โดนเป้าอย่างเดียวไม่จำเป็นต้องตัดสินผู้ชนะ ยังขึ้นอยู่กับความสำเร็จ อันดับ หรือกติกาตัดสินเสมอของเกม');
    }
    if (m.result === 'forfeit') notes.push('แมตช์นี้แพ้ผ่าน ไม่ใช่ไฟต์ที่เล่นจริง เฟรมที่แสดงเป็นจุดยุติ ไม่ใช่ระยะเวลาการต่อสู้ และไม่มีผล HP');
    if (m.result === 'tie') notes.push('แมตช์นี้จบเสมอ หากแข่งซ้ำ ผลของแมตช์ใหม่แสดงเป็นอีกรายการหนึ่ง');
    $('#detail-notes').hidden = !notes.length;
    $('#detail-notes-list').replaceChildren(...notes.map(note => e('li','',note)));
    const chart = m.series === 'fighting' && m.result !== 'forfeit' ? makeHPChart(m) : null;
    $('#detail-chart').hidden = !chart;
    $('#detail-chart').replaceChildren(...(chart || []));
    const pos = records.indexOf(m);
    [['#match-before',records[pos-1]],['#match-after',records[pos+1]]].forEach(([id,adjacent]) => {
      const a = $(id); a.hidden = !adjacent;
      if (adjacent) { a.href = route(adjacent.id); a.setAttribute('aria-label',(id.endsWith('before') ? 'แมตช์ก่อนหน้า ' : 'แมตช์ถัดไป ') + adjacent.id); }
    });
    $('#copy-status').textContent = '';
    $('#fallback-link').hidden = true;
    panel.hidden = false;
    void window.CupReplay?.show(m);
    renderList();
    if (useFocus) { $('#detail-title').focus({preventScroll:true}); panel.scrollIntoView({block:'start'}); }
  }

  function selectHash(useFocus) {
    const hash = location.hash;
    if (hash.startsWith('#match-')) {
      const id = hash.slice(7).toUpperCase();
      if (byID.has(id)) { showMatch(byID.get(id),useFocus); return; }
      $('#match-status').textContent = 'ไม่พบแมตช์ตามลิงก์นี้ ลองค้นหาจากรายการด้านล่าง';
      $('#match-status').hidden = false;
    } else if (records.length) $('#match-status').hidden = true;
    if (selected) {
      const prior = selected;
      selected = null;
      $('#match-detail').hidden = true;
      window.CupReplay?.clear();
      renderList();
      if (useFocus && hash === '#matches') {
        const visible = document.querySelector(`a.record[href="${route(prior)}"]`);
        (visible || $('#query')).focus({preventScroll:true});
      }
    }
  }

  $('#filter-form').addEventListener('submit', event => event.preventDefault());
  $('#query').addEventListener('input',filterList);
  ['#phase-filter','#game-filter','#sort'].forEach(id => $(id).addEventListener('change',filterList));
  $('#reset').addEventListener('click',() => { $('#filter-form').reset(); filterList(); $('#query').focus(); });
  for (const [selector, increment] of [['#page-prev',-1],['#page-next',1]]) {
    $(selector).addEventListener('click',() => {
      page += increment; renderList();
      if ($(selector).disabled) $(increment < 0 ? '#page-next' : '#page-prev').focus({preventScroll:true});
      $('#match-list').scrollIntoView({block:'nearest'});
    });
  }
  $('#copy-link').addEventListener('click', async () => {
    if (!selected) return;
    const link = new URL(location.href);
    link.hash = route(selected);
    try {
      await navigator.clipboard.writeText(link.href);
      $('#copy-status').textContent = 'คัดลอกลิงก์แมตช์แล้ว';
    } catch {
      const input = $('#copy-value');
      input.value = link.href;
      $('#fallback-link').hidden = false;
      input.focus(); input.select();
      $('#copy-status').textContent = 'เลือกและคัดลอกลิงก์จากช่องด้านบน';
    }
  });
  window.addEventListener('hashchange',() => selectHash(true));

  function defaultFailure(id, message) {
    $(id).textContent = message;
    $(id).hidden = false;
  }

  async function getJson(relative) {
    const response = await fetch(relative, {credentials:'omit',referrerPolicy:'no-referrer'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async function loadMatches() {
    try {
      const data = await getJson('./data.json');
      records = verifyData(data);
      byID = new Map(records.map(row => [row.id,row]));
      const keys = new Set(records.map(row => row.stage));
      addOptions($('#phase-filter'),[...phases].filter(([key]) => keys.has(key)));
      addOptions($('#game-filter'),[...new Set(records.map(row => row.game))].sort().map(key => [key,key]));
      displayMetrics(data.summary);
      $('#match-status').hidden = true;
      $('#match-interface').hidden = false;
      $('#download-data').hidden = false;
      filterList();
      selectHash(location.hash.startsWith('#match-'));
    } catch {
      defaultFailure('#match-status','โหลดข้อมูลแมตช์ไม่สำเร็จ ลองรีเฟรชหน้านี้อีกครั้ง');
    }
  }

  function reportLink(href) {
    if (typeof href !== 'string') return null;
    if (/^\.\/[\w-]+\.(?:md|csv|json|py)$/i.test(href)) return href;
    try {
      const url = new URL(href);
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
    } catch { return null; }
  }

  function renderReport(report) {
    if (!report || !Array.isArray(report.sections) || !Array.isArray(report.takeaways)) throw new Error('Invalid report schema');
    if (typeof report.intro === 'string' && report.intro.trim()) $('#report-intro').textContent = report.intro;
    const cards = report.takeaways.filter(r => r && typeof r.title === 'string' && typeof r.body === 'string');
    $('#takeaway-list').replaceChildren(...cards.map(({title,body}) => { const item = e('li'); item.append(e('h4','',title),e('p','',body)); return item; }));
    $('.takeaways').hidden = !cards.length;
    const sections = [], menu = [];
    for (const [i, part] of report.sections.entries()) {
      if (!part || typeof part.title !== 'string') continue;
      const safeID = typeof part.id === 'string' && /^[a-z0-9-]+$/i.test(part.id) ? part.id : String(i + 1);
      const id = 'report-' + safeID;
      if (id === 'report-title' || sections.some(section => section.id === id)) continue;
      const node = e('section','report-section');
      node.id = id;
      node.append(e('h3','',part.title));
      node.append(...textArray(typeof part.body === 'string' ? [part.body] : part.body).map(p => e('p','',p)));
      const bullets = textArray(part.bullets);
      if (bullets.length) {
        const ul = e('ul'); ul.append(...bullets.map(value => e('li','',value))); node.append(ul);
      }
      sections.push(node);
      const a = e('a','',part.title); a.href = '#' + id;
      const li = e('li'); li.append(a); menu.push(li);
    }
    $('#report-contents').replaceChildren(...menu);
    $('#contents-nav').hidden = !menu.length;
    $('#report-sections').replaceChildren(...sections);
    const links = [];
    for (const link of Array.isArray(report.links) ? report.links : []) {
      if (!link || typeof link.label !== 'string') continue;
      const href = reportLink(link.href);
      if (!href) continue;
      const a = e('a','button small button-line',link.label); a.href = href;
      a.prepend(icon(href.startsWith('./') ? 'download' : 'out'));
      if (href.startsWith('./')) a.download = '';
      const li = e('li'); li.append(a); links.push(li);
    }
    $('#report-links').replaceChildren(...links);
    $('#report-status').hidden = true;
    $('#report-interface').hidden = false;
    if (location.hash.startsWith('#report-')) {
      const target = document.getElementById(location.hash.slice(1));
      if (target && target.classList.contains('report-section')) target.scrollIntoView({block:'start'});
    }
  }

  async function loadReport() {
    try { renderReport(await getJson('./report.json')); }
    catch { defaultFailure('#report-status','โหลดรายงานไม่สำเร็จ รายการแมตช์ยังเปิดดูแยกได้'); }
  }

  void loadMatches();
  void loadReport();
})();
