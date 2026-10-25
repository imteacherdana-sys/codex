// 매물 관리·검색·시세 요약 화면 로직. 매물 금액은 '만원' 단위로 저장한다.
(function () {
  'use strict';

  const STORAGE_KEY = 'realestate.listings.v1';
  const TYPES = ['아파트', '빌라', '오피스텔', '단독주택', '상가'];
  const DEALS = { sale: '매매', jeonse: '전세', monthly: '월세' };

  const SAMPLE = [
    { title: '래미안 푸르지오 84㎡', region: '서울 강남구', dong: '대치동', type: '아파트', deal: 'sale', price: 265000, area: 84.9, floor: 12, rooms: 3, year: 2015 },
    { title: '래미안 푸르지오 84㎡ 전세', region: '서울 강남구', dong: '대치동', type: '아파트', deal: 'jeonse', deposit: 120000, area: 84.9, floor: 7, rooms: 3, year: 2015 },
    { title: '은마아파트 76㎡', region: '서울 강남구', dong: '대치동', type: '아파트', deal: 'sale', price: 228000, area: 76.8, floor: 5, rooms: 3, year: 1979 },
    { title: '마포 래미안 59㎡', region: '서울 마포구', dong: '아현동', type: '아파트', deal: 'sale', price: 158000, area: 59.9, floor: 15, rooms: 3, year: 2014 },
    { title: '마포 래미안 59㎡ 전세', region: '서울 마포구', dong: '아현동', type: '아파트', deal: 'jeonse', deposit: 82000, area: 59.9, floor: 9, rooms: 3, year: 2014 },
    { title: '합정역 신축 오피스텔', region: '서울 마포구', dong: '합정동', type: '오피스텔', deal: 'monthly', deposit: 1000, monthly: 85, area: 26.4, floor: 8, rooms: 1, year: 2022 },
    { title: '망원동 투룸 빌라', region: '서울 마포구', dong: '망원동', type: '빌라', deal: 'jeonse', deposit: 28000, area: 49.5, floor: 3, rooms: 2, year: 2018 },
    { title: '분당 정자동 느티마을', region: '경기 성남시 분당구', dong: '정자동', type: '아파트', deal: 'sale', price: 142000, area: 66.6, floor: 10, rooms: 3, year: 1994 },
    { title: '분당 정자동 느티마을 전세', region: '경기 성남시 분당구', dong: '정자동', type: '아파트', deal: 'jeonse', deposit: 58000, area: 66.6, floor: 4, rooms: 3, year: 1994 },
    { title: '판교역 1층 상가', region: '경기 성남시 분당구', dong: '삼평동', type: '상가', deal: 'monthly', deposit: 10000, monthly: 450, area: 72.0, floor: 1, rooms: 0, year: 2016 },
    { title: '해운대 엘시티 전망세대', region: '부산 해운대구', dong: '중동', type: '아파트', deal: 'sale', price: 310000, area: 144.2, floor: 60, rooms: 4, year: 2019 },
    { title: '센텀 원룸 월세', region: '부산 해운대구', dong: '우동', type: '오피스텔', deal: 'monthly', deposit: 500, monthly: 55, area: 23.1, floor: 11, rooms: 1, year: 2017 },
  ];

  // ---------- 저장소 ----------
  function load() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) { /* 저장소를 쓸 수 없으면 샘플로 시작 */ }
    return SAMPLE.map((x, i) => ({ id: 'sample-' + i, createdAt: Date.now() - i * 86400000, ...x }));
  }
  function save() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(listings)); } catch (e) { /* 무시 */ }
  }
  let listings = load();

  // ---------- 포맷 ----------
  // 만원 단위 숫자 → "12억 3,000만"
  function won(man) {
    if (!man) return '0';
    const eok = Math.floor(man / 10000);
    const rest = Math.round(man % 10000);
    if (eok && rest) return `${eok}억 ${rest.toLocaleString()}만`;
    if (eok) return `${eok}억`;
    return `${rest.toLocaleString()}만`;
  }
  // 원 단위 숫자 → "1,234,000원"
  const wonFull = (n) => Math.round(n).toLocaleString() + '원';
  const pct = (r) => (r * 100).toFixed(2).replace(/\.?0+$/, '') + '%';

  function priceLabel(l) {
    if (l.deal === 'sale') return `매매 ${won(l.price)}`;
    if (l.deal === 'jeonse') return `전세 ${won(l.deposit)}`;
    return `월세 ${won(l.deposit)} / ${l.monthly}만`;
  }
  // 정렬·필터 기준 금액(만원): 매매가 또는 보증금
  const mainPrice = (l) => (l.deal === 'sale' ? l.price : l.deposit) || 0;

  const $ = (sel, el = document) => el.querySelector(sel);
  const $$ = (sel, el = document) => Array.from(el.querySelectorAll(sel));
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const num = (v) => (v === '' || v == null ? null : Number(v));

  // ---------- 탭 ----------
  function showTab(name) {
    $$('.tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === name));
    $$('.panel').forEach((p) => (p.hidden = p.id !== 'panel-' + name));
    if (name === 'market') renderMarket();
  }
  $$('.tab').forEach((t) => t.addEventListener('click', () => showTab(t.dataset.tab)));

  // ---------- 검색/필터 ----------
  function fillSelect(sel, values, allLabel) {
    const cur = sel.value;
    sel.innerHTML = `<option value="">${allLabel}</option>` + values.map((v) => `<option>${esc(v)}</option>`).join('');
    if (values.includes(cur)) sel.value = cur;
  }
  function refreshRegionOptions() {
    const regions = [...new Set(listings.map((l) => l.region))].sort();
    fillSelect($('#f-region'), regions, '전체 지역');
    $('#region-list').innerHTML = regions.map((r) => `<option value="${esc(r)}">`).join('');
  }

  function filtered() {
    const q = $('#f-q').value.trim().toLowerCase();
    const region = $('#f-region').value;
    const type = $('#f-type').value;
    const deal = $('#f-deal').value;
    const pMin = num($('#f-pmin').value), pMax = num($('#f-pmax').value);
    const aMin = num($('#f-amin').value), aMax = num($('#f-amax').value);
    const sort = $('#f-sort').value;

    const res = listings.filter((l) => {
      if (q && !`${l.title} ${l.region} ${l.dong} ${l.memo || ''}`.toLowerCase().includes(q)) return false;
      if (region && l.region !== region) return false;
      if (type && l.type !== type) return false;
      if (deal && l.deal !== deal) return false;
      const p = mainPrice(l);
      if (pMin != null && p < pMin) return false;
      if (pMax != null && p > pMax) return false;
      if (aMin != null && l.area < aMin) return false;
      if (aMax != null && l.area > aMax) return false;
      return true;
    });
    const sorters = {
      new: (a, b) => b.createdAt - a.createdAt,
      priceAsc: (a, b) => mainPrice(a) - mainPrice(b),
      priceDesc: (a, b) => mainPrice(b) - mainPrice(a),
      area: (a, b) => b.area - a.area,
    };
    return res.sort(sorters[sort] || sorters.new);
  }

  function renderList() {
    const items = filtered();
    $('#result-count').textContent = `검색 결과 ${items.length}건 / 전체 ${listings.length}건`;
    $('#list').innerHTML = items.length ? items.map(card).join('')
      : '<p class="empty">조건에 맞는 매물이 없습니다. 필터를 바꾸거나 매물을 등록해 보세요.</p>';
  }

  function card(l) {
    const py = Calc.toPyeong(l.area);
    const perPy = l.deal === 'sale' && l.price ? ` · 평당 ${won(Math.round(l.price / py))}` : '';
    return `
      <article class="card" data-id="${esc(l.id)}">
        <div class="card-top">
          <span class="badge deal-${l.deal}">${DEALS[l.deal]}</span>
          <span class="badge">${esc(l.type)}</span>
        </div>
        <h3>${esc(l.title)}</h3>
        <p class="price">${priceLabel(l)}</p>
        <p class="meta">${esc(l.region)} ${esc(l.dong)}</p>
        <p class="meta">${l.area}㎡ (${py.toFixed(1)}평)${perPy}</p>
        <p class="meta">${l.floor ?? '-'}층 · 방 ${l.rooms ?? '-'}개 · ${l.year ? l.year + '년' : '연식 미상'}</p>
        ${l.memo ? `<p class="memo">${esc(l.memo)}</p>` : ''}
        <div class="card-actions">
          <button class="btn-small" data-act="fee">중개보수 계산</button>
          <button class="btn-small" data-act="edit">수정</button>
          <button class="btn-small danger" data-act="del">삭제</button>
        </div>
      </article>`;
  }

  $('#filters').addEventListener('input', renderList);
  $('#f-reset').addEventListener('click', () => { $('#filters').reset(); renderList(); });

  $('#list').addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-act]');
    if (!btn) return;
    const id = btn.closest('.card').dataset.id;
    const l = listings.find((x) => x.id === id);
    if (btn.dataset.act === 'del') {
      if (confirm(`"${l.title}" 매물을 삭제할까요?`)) {
        listings = listings.filter((x) => x.id !== id);
        save(); refreshRegionOptions(); renderList();
      }
    } else if (btn.dataset.act === 'edit') {
      openForm(l);
    } else if (btn.dataset.act === 'fee') {
      // 계산기 탭으로 넘어가 금액을 채워 넣는다
      showTab('calc');
      $('#fee-deal').value = l.deal;
      $('#fee-price').value = l.price || '';
      $('#fee-deposit').value = l.deposit || '';
      $('#fee-monthly').value = l.monthly || '';
      updateFeeFields(); calcFee();
      $('#calc-fee').scrollIntoView({ behavior: 'smooth' });
    }
  });

  // ---------- 매물 등록/수정 ----------
  const dialog = $('#form-dialog');
  const form = $('#listing-form');

  function syncDealFields() {
    const deal = form.elements.deal.value;
    $$('[data-for]', form).forEach((el) => {
      const show = el.dataset.for.split(' ').includes(deal);
      el.hidden = !show;
      $('input', el).required = show;
    });
  }
  form.elements.deal.addEventListener('change', syncDealFields);

  function openForm(l) {
    form.reset();
    form.dataset.id = l ? l.id : '';
    $('#form-title').textContent = l ? '매물 수정' : '매물 등록';
    if (l) Object.entries(l).forEach(([k, v]) => { if (form.elements[k]) form.elements[k].value = v ?? ''; });
    syncDealFields();
    dialog.showModal();
  }
  $('#btn-add').addEventListener('click', () => openForm(null));
  $('#form-cancel').addEventListener('click', () => dialog.close());

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const f = form.elements;
    const deal = f.deal.value;
    const data = {
      title: f.title.value.trim(), region: f.region.value.trim(), dong: f.dong.value.trim(),
      type: f.type.value, deal,
      price: deal === 'sale' ? num(f.price.value) : null,
      deposit: deal !== 'sale' ? num(f.deposit.value) : null,
      monthly: deal === 'monthly' ? num(f.monthly.value) : null,
      area: num(f.area.value), floor: num(f.floor.value), rooms: num(f.rooms.value), year: num(f.year.value),
      memo: f.memo.value.trim(),
    };
    const id = form.dataset.id;
    if (id) listings = listings.map((x) => (x.id === id ? { ...x, ...data } : x));
    else listings.push({ id: 'l-' + Date.now(), createdAt: Date.now(), ...data });
    save(); refreshRegionOptions(); renderList();
    dialog.close();
  });

  // ---------- 데이터 백업/초기화 ----------
  $('#btn-export').addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(listings, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `매물목록_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  });
  $('#btn-import').addEventListener('click', () => $('#import-file').click());
  $('#import-file').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const data = JSON.parse(await file.text());
      if (!Array.isArray(data)) throw new Error('배열 형식이 아닙니다');
      listings = data;
      save(); refreshRegionOptions(); renderList();
      alert(`${data.length}건을 불러왔습니다.`);
    } catch (err) {
      alert('파일을 읽지 못했습니다: ' + err.message);
    }
    e.target.value = '';
  });
  $('#btn-sample').addEventListener('click', () => {
    if (!confirm('지금 매물 목록을 지우고 샘플 데이터로 되돌릴까요?')) return;
    try { localStorage.removeItem(STORAGE_KEY); } catch (e) { /* 무시 */ }
    listings = load();
    refreshRegionOptions(); renderList();
  });

  // ---------- 시세 요약 ----------
  function renderMarket() {
    const groups = {};
    listings.forEach((l) => {
      const key = `${l.region}|${l.type}`;
      (groups[key] ||= { region: l.region, type: l.type, sale: [], jeonse: [], monthly: [] })[l.deal].push(l);
    });
    const avg = (arr) => (arr.length ? arr.reduce((s, x) => s + x, 0) / arr.length : null);
    const rows = Object.values(groups).sort((a, b) => a.region.localeCompare(b.region) || a.type.localeCompare(b.type)).map((g) => {
      const salePerPy = avg(g.sale.map((l) => l.price / Calc.toPyeong(l.area)));
      const jeonsePerPy = avg(g.jeonse.map((l) => l.deposit / Calc.toPyeong(l.area)));
      const ratio = salePerPy && jeonsePerPy ? jeonsePerPy / salePerPy : null;
      return `<tr>
        <td>${esc(g.region)}</td><td>${esc(g.type)}</td>
        <td class="num">${g.sale.length}</td>
        <td class="num">${salePerPy ? won(Math.round(salePerPy)) : '-'}</td>
        <td class="num">${g.jeonse.length}</td>
        <td class="num">${jeonsePerPy ? won(Math.round(jeonsePerPy)) : '-'}</td>
        <td class="num">${ratio ? (ratio * 100).toFixed(1) + '%' : '-'}</td>
        <td class="num">${g.monthly.length}</td>
      </tr>`;
    });
    $('#market-body').innerHTML = rows.join('') || '<tr><td colspan="8" class="empty">매물이 없습니다.</td></tr>';
  }

  // ---------- 계산기: 중개보수 ----------
  function updateFeeFields() {
    const deal = $('#fee-deal').value;
    $$('#calc-fee [data-for]').forEach((el) => (el.hidden = !el.dataset.for.split(' ').includes(deal)));
  }
  function calcFee() {
    const deal = $('#fee-deal').value;
    const man = (id) => (Number($(id).value) || 0) * 1e4;
    const r = Calc.brokerageFee({ dealType: deal, price: man('#fee-price'), deposit: man('#fee-deposit'), monthly: man('#fee-monthly') });
    $('#fee-result').innerHTML = `
      <dl>
        <dt>거래금액${deal === 'monthly' ? ' (환산)' : ''}</dt><dd>${wonFull(r.base)}</dd>
        <dt>상한요율</dt><dd>${pct(r.rate)}${r.cap ? ` (한도 ${wonFull(r.cap)})` : ''}</dd>
        <dt>중개보수 상한</dt><dd><strong>${wonFull(r.fee)}</strong></dd>
        <dt>부가세 10% 포함 시</dt><dd>${wonFull(r.total)}</dd>
      </dl>`;
  }
  $('#fee-deal').addEventListener('change', () => { updateFeeFields(); calcFee(); });
  $('#calc-fee').addEventListener('input', calcFee);

  // ---------- 계산기: 취득세 ----------
  function calcTax() {
    const price = (Number($('#tax-price').value) || 0) * 1e4;
    const r = Calc.acquisitionTax({
      price, homes: Number($('#tax-homes').value), regulated: $('#tax-regulated').checked, area: Number($('#tax-area').value) || 0,
    });
    $('#tax-result').innerHTML = `
      <dl>
        <dt>취득세 (${pct(r.rate)})</dt><dd>${wonFull(r.tax)}</dd>
        <dt>지방교육세 (${pct(r.eduRate)})</dt><dd>${wonFull(r.edu)}</dd>
        <dt>농어촌특별세 (${pct(r.ruralRate)})</dt><dd>${wonFull(r.rural)}</dd>
        <dt>합계</dt><dd><strong>${wonFull(r.total)}</strong></dd>
      </dl>`;
  }
  $('#calc-tax').addEventListener('input', calcTax);

  // ---------- 계산기: 대출 ----------
  function calcLoan() {
    const principal = (Number($('#loan-amount').value) || 0) * 1e4;
    const months = Math.max(1, Math.round((Number($('#loan-years').value) || 0) * 12));
    const annualRate = (Number($('#loan-rate').value) || 0) / 100;
    const method = $('#loan-method').value;
    const r = Calc.loanSchedule({ principal, annualRate, months, method });
    const last = r.rows[r.rows.length - 1];
    $('#loan-result').innerHTML = `
      <dl>
        <dt>첫 달 상환액</dt><dd><strong>${wonFull(r.firstPayment)}</strong></dd>
        ${method === 'principal' ? `<dt>마지막 달 상환액</dt><dd>${wonFull(last.payment)}</dd>` : ''}
        <dt>총 이자</dt><dd>${wonFull(r.totalInterest)}</dd>
        <dt>총 상환액</dt><dd>${wonFull(r.totalPayment)}</dd>
      </dl>`;
    // 연도별 요약표
    const years = [];
    for (let i = 0; i < r.rows.length; i += 12) {
      const chunk = r.rows.slice(i, i + 12);
      years.push(`<tr><td>${i / 12 + 1}년차</td>
        <td class="num">${wonFull(chunk.reduce((s, x) => s + x.principal, 0))}</td>
        <td class="num">${wonFull(chunk.reduce((s, x) => s + x.interest, 0))}</td>
        <td class="num">${wonFull(chunk[chunk.length - 1].balance)}</td></tr>`);
    }
    $('#loan-table').innerHTML = years.join('');
  }
  $('#calc-loan').addEventListener('input', calcLoan);

  // ---------- 시작 ----------
  fillSelect($('#f-type'), TYPES, '전체 유형');
  form.elements.type.innerHTML = TYPES.map((t) => `<option>${t}</option>`).join('');
  refreshRegionOptions();
  renderList();
  updateFeeFields(); calcFee(); calcTax(); calcLoan();
})();
