// Random differential cases: node-semver verdicts for satisfies/compare.
const fs = require('fs');
const semver = require('semver');

let seed = 20260927;
const rnd = n => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed % n; };
const pick = a => a[rnd(a.length)];
const num = () => pick(['0', '0', '1', '1', '2', '3', '10']);
const preId = () => pick(['alpha', 'beta', 'rc', '0', '1', '2', '11', 'x-y']);
function version() {
  let v = `${num()}.${num()}.${num()}`;
  if (rnd(3) === 0) { v += '-' + preId(); if (rnd(2)) v += '.' + preId(); }
  if (rnd(6) === 0) v += '+b.' + rnd(9);
  return v;
}
function partial() {
  const k = rnd(5);
  if (k === 0) return pick(['*', 'x']);
  if (k === 1) return num();
  if (k === 2) return `${num()}.${pick([num(), 'x'])}`;
  return version().replace(/\+.*/, '');
}
function simple() {
  switch (rnd(4)) {
    case 0: return '^' + partial();
    case 1: return pick(['~', '~>']) + partial();
    case 2: return pick(['<', '<=', '>', '>=', '=', '']) + partial();
    default: return partial();
  }
}
function range() {
  const alts = [];
  const n = 1 + rnd(2);
  for (let i = 0; i < n; i++) {
    if (rnd(5) === 0) alts.push(`${partial()} - ${partial()}`);
    else alts.push(Array.from({ length: 1 + rnd(2) }, simple).join(' '));
  }
  return alts.join(pick([' || ', '||']));
}
const sat = [], cmp = [];
while (sat.length < 3000) {
  const v = version(), r = range();
  if (semver.valid(v) === null || semver.validRange(r) === null) continue;
  sat.push([v, r, semver.satisfies(v, r)]);
}
for (let i = 0; i < 1000; i++) { const a = version(), b = version(); cmp.push([a, b, semver.compare(a, b)]); }
fs.writeFileSync(process.argv[2], JSON.stringify({ sat, cmp }));
console.log('true verdicts', sat.filter(x => x[2]).length, 'of', sat.length);
