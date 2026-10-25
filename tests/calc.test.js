// 실행: node --test tests/
const test = require('node:test');
const assert = require('node:assert/strict');
const Calc = require('../js/calc.js');

test('중개보수: 매매 구간별 요율과 한도', () => {
  assert.equal(Calc.brokerageFee({ dealType: 'sale', price: 40e6 }).fee, 240000);
  assert.equal(Calc.brokerageFee({ dealType: 'sale', price: 190e6 }).fee, 800000); // 0.5% = 95만 → 한도 80만
  assert.equal(Calc.brokerageFee({ dealType: 'sale', price: 500e6 }).fee, 2000000);
  assert.equal(Calc.brokerageFee({ dealType: 'sale', price: 1000e6 }).fee, 5000000);
  assert.equal(Calc.brokerageFee({ dealType: 'sale', price: 2000e6 }).fee, 14000000);
});

test('중개보수: 전세·월세', () => {
  assert.equal(Calc.brokerageFee({ dealType: 'jeonse', deposit: 300e6 }).fee, 900000);
  assert.equal(Calc.brokerageFee({ dealType: 'jeonse', deposit: 80e6 }).fee, 300000); // 0.4% = 32만 → 한도 30만
  // 보증금 1000만 + 월세 50만: 1000만+5000만=6000만 (≥5천만) → 0.4% = 24만
  const r = Calc.brokerageFee({ dealType: 'monthly', deposit: 10e6, monthly: 0.5e6 });
  assert.equal(r.base, 60e6);
  assert.equal(r.fee, 240000);
  // 보증금 500만 + 월세 30만: ×100 = 3500만 (<5천만) → ×70 = 2600만, 0.5% = 13만
  assert.equal(Calc.monthlyRentBase(5e6, 0.3e6), 26e6);
});

test('취득세: 1주택 6억 이하 / 6~9억 / 9억 초과', () => {
  const a = Calc.acquisitionTax({ price: 500e6, area: 84 });
  assert.equal(a.rate, 0.01);
  assert.equal(a.total, 5500000); // 취득세 1% + 교육세 0.1%
  const b = Calc.acquisitionTax({ price: 750e6, area: 84 });
  assert.equal(b.rate, 0.02); // 7.5억 × 2/3 − 3 = 2%
  const c = Calc.acquisitionTax({ price: 1000e6, area: 100 });
  assert.equal(c.rate, 0.03);
  assert.equal(c.rural, 2000000); // 85㎡ 초과 농특세 0.2%
});

test('취득세: 다주택 중과', () => {
  assert.equal(Calc.acquisitionTax({ price: 500e6, homes: 2, regulated: true }).rate, 0.08);
  assert.equal(Calc.acquisitionTax({ price: 500e6, homes: 2, regulated: false }).rate, 0.01);
  assert.equal(Calc.acquisitionTax({ price: 500e6, homes: 3, regulated: true }).rate, 0.12);
  assert.equal(Calc.acquisitionTax({ price: 500e6, homes: 4 }).eduRate, 0.004);
});

test('대출: 원리금균등 월 상환액', () => {
  // 3억, 연 4.2%, 30년 → 약 1,467,052원
  const r = Calc.loanSchedule({ principal: 300e6, annualRate: 0.042, months: 360 });
  assert.ok(Math.abs(r.firstPayment - 1467052) < 1, r.firstPayment);
  assert.ok(r.rows[359].balance < 1e-3);
});

test('대출: 원금균등·만기일시', () => {
  const p = Calc.loanSchedule({ principal: 120e6, annualRate: 0.06, months: 12, method: 'principal' });
  assert.equal(p.firstPayment, 10e6 + 600000);
  const b = Calc.loanSchedule({ principal: 100e6, annualRate: 0.06, months: 12, method: 'bullet' });
  assert.equal(b.firstPayment, 500000);
  assert.equal(Math.round(b.totalInterest), 6000000);
});
