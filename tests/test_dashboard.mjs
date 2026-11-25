import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const html = readFileSync(new URL('../web/dashboard.html', import.meta.url), 'utf8');
const helper = html.match(/function formatRecoveryValue\(metrics = \{\}\) \{[\s\S]*?\n\}/)?.[0];
assert.ok(helper, 'Load the formatting function used by the dashboard');
const format = vm.runInNewContext(`${helper}; formatRecoveryValue`);

test('mixed currencies never become a dollar zero or an unconverted total', () => {
  for (const amount of [null, 49]) {
    assert.equal(format({currency:'MIXED', recoverable_value_identified:amount}), 'MULTIPLE CURRENCIES');
  }
});

test('missing or invalid recovery amounts and currencies stay unverified', () => {
  for (const metrics of [{}, {currency:'USD', recoverable_value_identified:null},
    {currency:'USD', recoverable_value_identified:'0'},
    {currency:'USD', recoverable_value_identified:NaN},
    {currency:'USD', recoverable_value_identified:Infinity},
    {currency:'USD', recoverable_value_identified:-1},
    {currency:'UNKNOWN', recoverable_value_identified:49},
    {currency:'ZZZ', recoverable_value_identified:49},
    {recoverable_value_identified:49}]) {
    assert.equal(format(metrics), 'UNVERIFIED');
  }
});

test('known single-currency values retain their currency, including a genuine zero', () => {
  for (const currency of ['USD', 'EUR', 'GBP']) {
    assert.match(format({currency, recoverable_value_identified:49}), new RegExp(currency));
  }
  assert.match(format({currency:'EUR', recoverable_value_identified:0}), /EUR.*0/);
  assert.doesNotMatch(format({currency:'EUR', recoverable_value_identified:49}), /\$/);
});
