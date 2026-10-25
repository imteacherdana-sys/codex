// 부동산 계산 로직 (브라우저/Node 공용). 금액 단위는 모두 '원'.
(function (root) {
  'use strict';

  // 주택 중개보수 상한요율 (2021.10.19 시행 공인중개사법 시행규칙 기준)
  const SALE_BRACKETS = [
    { max: 50e6, rate: 0.006, cap: 250000 },
    { max: 200e6, rate: 0.005, cap: 800000 },
    { max: 900e6, rate: 0.004 },
    { max: 1200e6, rate: 0.005 },
    { max: 1500e6, rate: 0.006 },
    { max: Infinity, rate: 0.007 },
  ];
  const LEASE_BRACKETS = [
    { max: 50e6, rate: 0.005, cap: 200000 },
    { max: 100e6, rate: 0.004, cap: 300000 },
    { max: 600e6, rate: 0.003 },
    { max: 1200e6, rate: 0.004 },
    { max: 1500e6, rate: 0.005 },
    { max: Infinity, rate: 0.006 },
  ];

  // 월세 거래금액 환산: 보증금 + 월세×100, 그 값이 5천만원 미만이면 보증금 + 월세×70
  function monthlyRentBase(deposit, monthly) {
    const base = deposit + monthly * 100;
    return base < 50e6 ? deposit + monthly * 70 : base;
  }

  // dealType: 'sale' | 'jeonse' | 'monthly'
  function brokerageFee({ dealType, price = 0, deposit = 0, monthly = 0 }) {
    const base = dealType === 'sale' ? price
      : dealType === 'jeonse' ? deposit
      : monthlyRentBase(deposit, monthly);
    const brackets = dealType === 'sale' ? SALE_BRACKETS : LEASE_BRACKETS;
    const b = brackets.find((x) => base < x.max) || brackets[brackets.length - 1];
    let fee = Math.floor(base * b.rate);
    if (b.cap) fee = Math.min(fee, b.cap);
    const vat = Math.floor(fee * 0.1);
    return { base, rate: b.rate, cap: b.cap || null, fee, vat, total: fee + vat };
  }

  // 주택 취득세 (유상 매매). homes: 취득 후 보유 주택 수(1~4), regulated: 조정대상지역 여부
  function acquisitionTax({ price, homes = 1, regulated = false, area = 85 }) {
    let rate;
    let heavy = false;
    if (homes >= 4 || (homes === 3 && regulated)) { rate = 0.12; heavy = true; }
    else if (homes === 3 || (homes === 2 && regulated)) { rate = 0.08; heavy = true; }
    else if (price <= 600e6) rate = 0.01;
    else if (price <= 900e6) {
      // 6억~9억 구간: (취득가액 × 2/3억 − 3) / 100, 소수점 다섯째자리 반올림
      rate = Math.round(((price * 2) / 3e8 - 3) * 1e4) / 1e6;
    } else rate = 0.03;

    const eduRate = heavy ? 0.004 : rate / 10;
    const ruralRate = area <= 85 ? 0 : rate === 0.12 ? 0.01 : rate === 0.08 ? 0.006 : 0.002;
    const tax = Math.floor(price * rate);
    const edu = Math.floor(price * eduRate);
    const rural = Math.floor(price * ruralRate);
    return { rate, eduRate, ruralRate, tax, edu, rural, total: tax + edu + rural };
  }

  // 대출 상환. method: 'equal' (원리금균등) | 'principal' (원금균등) | 'bullet' (만기일시)
  function loanSchedule({ principal, annualRate, months, method = 'equal' }) {
    const r = annualRate / 12;
    const rows = [];
    let balance = principal;
    const fixedPay = r === 0 ? principal / months
      : (principal * r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
    for (let i = 1; i <= months; i++) {
      const interest = balance * r;
      let princ;
      if (method === 'equal') princ = fixedPay - interest;
      else if (method === 'principal') princ = principal / months;
      else princ = i === months ? balance : 0;
      if (i === months) princ = balance;
      balance -= princ;
      rows.push({ month: i, payment: princ + interest, principal: princ, interest, balance: Math.max(balance, 0) });
    }
    const totalInterest = rows.reduce((s, x) => s + x.interest, 0);
    return { rows, firstPayment: rows[0] ? rows[0].payment : 0, totalInterest, totalPayment: principal + totalInterest };
  }

  const PYEONG = 3.305785; // 1평 = 3.305785㎡
  const toPyeong = (m2) => m2 / PYEONG;

  const api = { brokerageFee, acquisitionTax, loanSchedule, monthlyRentBase, toPyeong, PYEONG };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.Calc = api;
})(typeof window !== 'undefined' ? window : globalThis);
