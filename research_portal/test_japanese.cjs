const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, 'japanese.js'), 'utf8'), context);
context.initializeJapanese(JSON.parse(fs.readFileSync(path.join(__dirname, 'ja.json'), 'utf8')));

test('research statuses and captions have Japanese display names', () => {
  assert.equal(context.japaneseText('Routing Baseline'), '経路計算の基準');
  assert.equal(context.japaneseText('SUPPORTED WITH CONDITIONS'), '条件付きで支持');
  assert.equal(context.japaneseText('DEFINITION DERIVED'), '定義から導出');
  assert.equal(context.japaneseText('Stage: NEXT'), '段階: 次の工程');
});

test('references and quoted executable commands remain exact', () => {
  for (const text of [
    'reproducibility/outputs/traffic_simulation/network_acceptance.json',
    'https://example.com/research/validation',
    '`./research portal validate`',
    'P13-THREE-TIER-RUN-2',
    '4625dbbc150cbcf72964bed0e90a8b33fe03f190ff4264aecaaf89e3aab0e40f',
  ]) assert.equal(context.japaneseText(text), text);
});
