'use strict';
const vm = require('node:vm'), fs = require('node:fs'), path = require('node:path');
const assert = require('node:assert/strict');
const dir = process.argv[2];
const index = JSON.parse(fs.readFileSync(path.join(dir, 'cup100-data.json'), 'utf8'));
const script = fs.readFileSync(path.join(dir, 'cup100.html'), 'utf8').match(/<script>([\s\S]+)<\/script>/)[1];
const choices = index.results.map(result => ({value:result.match}));
const first = choices[0].value, last = choices.at(-1).value;
assert.notEqual(first, last);
function verify(search, expected) {
  const elements = {match:{options:choices, value:first}};
  const el = id => elements[id] ??= {value:0, setAttribute() {}};
  const requests = [];
  vm.runInNewContext(script, {
    Response, Blob, DecompressionStream, URLSearchParams, atob,
    location:{search}, document:{getElementById:el},
    fetch: async url => { requests.push(url); return new Promise(()=>{}); },
    requestAnimationFrame: () => {throw new Error('a link must not start playback');},
    cancelAnimationFrame: () => {},
  });
  assert.deepEqual(requests, [index.results.find(r=>r.match===expected).replay]);
  assert.equal(el('match').value, expected);
}
verify('', first);
verify('?match=../other', first);
verify('?match='+last.toLowerCase(), first);
verify('?match='+last, last);
console.log('Replay routes: missing, invalid, case mismatch, and valid match; no autoplay.');
