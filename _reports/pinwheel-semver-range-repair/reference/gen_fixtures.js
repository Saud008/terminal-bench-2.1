// Writes tests/fixtures/{registry,projects,expected} using an independent
// JavaScript implementation of docs/resolution.md on top of node-semver 7.6.3.
const fs = require('fs');
const path = require('path');
const semver = require('semver');

let clock = Date.parse('2023-03-01T09:00:00Z');
function rel(version, deps = {}, extra = {}) {
  clock += 36 * 3600 * 1000;
  return { version, published: new Date(clock).toISOString().replace('.000Z', 'Z'), yanked: false, dependencies: deps, ...extra };
}
const Y = { yanked: true };

const registry = {
  'brook-io': [rel('1.0.0'), rel('1.1.0'), rel('1.2.0'), rel('1.2.5')],
  'cask-store': [rel('2.0.0', { 'nettle-crypto': '^3.2.0' }), rel('2.1.0', { 'nettle-crypto': '^3.2.0' })],
  'dune-parse': [
    rel('1.0.0+build.1', {}, { published: '2024-01-10T08:00:00Z' }),
    rel('1.0.0+build.2', {}, { published: '2024-03-02T08:00:00Z' }),
    rel('1.1.0', {}, { published: '2024-05-01T08:00:00Z' }),
  ],
  'elm-signal': [rel('0.9.2'), rel('0.9.3', {}, Y), rel('0.9.4')],
  'flint-auth': [rel('2.0.0-beta.2'), rel('2.0.0-beta.3', {}, Y), rel('2.0.0')],
  'gale-queue': [rel('1.4.0'), rel('1.6.2'), rel('2.0.0'), rel('2.1.0'), rel('2.1.4'), rel('2.2.0')],
  'hollow-db': [
    rel('3.1.0', { 'brook-io': '^1.0.0' }),
    rel('3.2.0', { 'brook-io': '^1.2.0' }),
    rel('3.4.1', { 'cask-store': '^2.0.0', 'iris-fmt': '^0.3.0' }),
  ],
  'iris-fmt': [
    rel('0.3.0+r1', {}, { published: '2024-02-01T00:00:00Z' }),
    rel('0.3.0+r2', {}, { published: '2024-02-01T00:00:00Z' }),
    rel('0.3.4'),
    rel('0.4.0'),
  ],
  'jade-cli': [rel('1.3.0', { 'gale-queue': '^1.4.0' })],
  'kelp-cache': [rel('2.2.0', { 'gale-queue': '>=1.0.0 <3', 'brook-io': '^1.0.0' })],
  'loom-sched': [
    rel('2.4.0', { 'hollow-db': '>=3.0.0 <3.3' }),
    rel('2.4.3', { 'hollow-db': '<3.3', 'moss-trace': '1.x' }),
    rel('2.5.0'),
  ],
  'moss-trace': [rel('1.0.0'), rel('1.3.0'), rel('2.0.0')],
  'nettle-crypto': [rel('3.2.0'), rel('3.2.1', {}, Y), rel('3.3.0')],
  'opal-ui': [
    rel('4.0.0'),
    rel('4.1.0', { 'elm-signal': '=0.9.3', 'flint-auth': '2.0.0-beta.3', 'nettle-crypto': '^3.2.0' }),
    rel('4.2.0', {}, Y),
  ],
  'quartz-http': [rel('0.4.1'), rel('0.4.6', { 'sable-log': '^1.3.0' }), rel('0.5.0'), rel('0.9.2')],
  'rune-cli': [rel('1.0.2'), rel('1.4.0'), rel('1.9.1'), rel('2.0.0')],
  'sable-log': [rel('1.1.0'), rel('1.3.2'), rel('1.4.7'), rel('1.5.0')],
  'tarn-db': [rel('2.1.5'), rel('2.2.0'), rel('2.3.4'), rel('2.4.0')],
  'umber-ui': [rel('2.5.0'), rel('3.1.0'), rel('4.0.0')],
  'vale-core': [rel('1.2.0'), rel('1.3.0-beta.1'), rel('1.3.0-beta.2'), rel('1.3.0-beta.11'), rel('1.4.0-rc.1')],
  'wisp-io': [rel('1.0.0+linux')],
};

const projects = {
  prune: { name: 'prune-app', dependencies: { 'hollow-db': '^3.1.0', 'loom-sched': '~2.4.0' } },
  overrides: {
    name: 'override-app',
    dependencies: { 'jade-cli': '^1.0.0', 'kelp-cache': '^2.0.0' },
    overrides: { 'gale-queue': '2.1.x', 'brook-io': '1.1.0', 'moss-trace': '1.0.0' },
  },
  yanked: { name: 'yanked-app', dependencies: { 'nettle-crypto': '3.2.1', 'opal-ui': '^4.0.0' } },
  lowest: {
    name: 'lowest-app',
    prefer: 'lowest',
    dependencies: { 'iris-fmt': '^0.3.0', 'dune-parse': '>=1.0.0', 'kelp-cache': '^2.0.0' },
  },
  mixed: {
    name: 'mixed-app',
    dependencies: {
      'quartz-http': '^0.4.1',
      'rune-cli': '~1',
      'sable-log': '1.2 - 1.4',
      'tarn-db': '>2.1 <=2.3',
      'umber-ui': '^2.0.0||^3.0.0',
      'vale-core': '^1.3.0-beta.1',
      'wisp-io': '1.0.0',
      'dune-parse': '1.0.x',
    },
  },
  small: { name: 'small-app', dependencies: { 'rune-cli': '^1.4.0', 'moss-trace': '>=1.0.0 <2' } },
  unsat: { name: 'unsat-app', dependencies: { 'quartz-http': '^0.3.1', 'rune-cli': '^1.0.0' } },
  missing: { name: 'missing-app', dependencies: { 'rune-cli': '^1.0.0', 'ghost-pkg': '^1.0.0' } },
};

function isExactPin(raw) {
  const r = new semver.Range(raw);
  if (r.set.length !== 1 || r.set[0].length !== 1) return false;
  const c = r.set[0][0];
  return c.semver !== semver.Comparator.ANY && c.operator === '';
}

function gather(m, sel) {
  const cons = new Map();
  const queue = [];
  const add = (from, name, raw) => {
    if (!cons.has(name)) { cons.set(name, []); queue.push(name); }
    cons.get(name).push({ from, raw });
  };
  for (const name of Object.keys(m.dependencies || {}).sort()) add('<root>', name, m.dependencies[name]);
  while (queue.length) {
    const name = queue.shift();
    if (!sel.has(name)) continue;
    const deps = registry[name][sel.get(name)].dependencies;
    for (const dep of Object.keys(deps).sort()) add(name, dep, deps[dep]);
  }
  return cons;
}

function better(a, b, lowest) {
  const c = semver.compare(a.version, b.version);
  if (c !== 0) return lowest ? c < 0 : c > 0;
  const pa = Date.parse(a.published), pb = Date.parse(b.published);
  if (pa !== pb) return pa > pb;
  return a.index > b.index;
}

function resolve(m) {
  const lowest = m.prefer === 'lowest';
  let sel = new Map();
  for (let round = 0; round < 100; round++) {
    const cons = gather(m, sel);
    const next = new Map();
    for (const name of [...cons.keys()].sort()) {
      if (!registry[name]) return { error: 'unknown', pkg: name };
      const eff = m.overrides && name in m.overrides ? [{ from: '<overrides>', raw: m.overrides[name] }] : cons.get(name);
      const eligible = registry[name]
        .map((r, index) => ({ ...r, index }))
        .filter(r => eff.every(c => semver.satisfies(r.version, c.raw)))
        .filter(r => !r.yanked || eff.some(c => isExactPin(c.raw) && semver.satisfies(r.version, c.raw)));
      if (!eligible.length) return { error: 'unsat', pkg: name };
      let best = eligible[0];
      for (const r of eligible.slice(1)) if (better(r, best, lowest)) best = r;
      next.set(name, best.index);
    }
    const same = next.size === sel.size && [...next].every(([k, v]) => sel.get(k) === v);
    if (same) return { sel: next, cons, rounds: round + 1 };
    sel = next;
  }
  return { error: 'loop' };
}

function lockText(m, res) {
  const packages = {};
  for (const name of [...res.sel.keys()].sort()) {
    const r = registry[name][res.sel.get(name)];
    const deps = {};
    for (const k of Object.keys(r.dependencies).sort()) deps[k] = r.dependencies[k];
    packages[name] = {
      version: r.version,
      requiredBy: [...new Set(res.cons.get(name).map(c => c.from))].sort(),
      dependencies: deps,
    };
  }
  return JSON.stringify({ lockfileVersion: 1, name: m.name, packages }, null, 2) + '\n';
}

const root = process.argv[2];
const regDir = path.join(root, 'registry');
const projDir = path.join(root, 'projects');
const expDir = path.join(root, 'expected');
for (const d of [regDir, projDir, expDir]) fs.mkdirSync(d, { recursive: true });

for (const [name, versions] of Object.entries(registry)) {
  const doc = { name, versions: versions.map(v => ({ version: v.version, published: v.published, yanked: v.yanked, dependencies: v.dependencies })) };
  fs.writeFileSync(path.join(regDir, `${name}.json`), JSON.stringify(doc, null, 2) + '\n');
}
for (const [dir, m] of Object.entries(projects)) {
  fs.mkdirSync(path.join(projDir, dir), { recursive: true });
  fs.writeFileSync(path.join(projDir, dir, 'pin.json'), JSON.stringify(m, null, 2) + '\n');
  const res = resolve(m);
  if (res.error) {
    console.log(`${dir}: ${res.error} ${res.pkg || ''}`);
    continue;
  }
  fs.writeFileSync(path.join(expDir, `${dir}.lock`), lockText(m, res));
  console.log(`${dir}: ${res.sel.size} packages in ${res.rounds} rounds: ` +
    [...res.sel].map(([k, i]) => `${k}@${registry[k][i].version}`).join(' '));
}
