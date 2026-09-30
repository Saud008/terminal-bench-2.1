// Writes the registry snapshot and example projects shipped in environment/app.
const fs = require('fs');
const path = require('path');

let clock = Date.parse('2022-11-14T10:30:00Z');
function rel(version, deps = {}, extra = {}) {
  clock += 29 * 3600 * 1000;
  return { version, published: new Date(clock).toISOString().replace('.000Z', 'Z'), yanked: false, dependencies: deps, ...extra };
}
const Y = { yanked: true };

const registry = {
  'ansi-glyphs': [rel('0.9.5'), rel('1.0.0'), rel('1.2.1')],
  'ember-uuid': [rel('1.4.1'), rel('1.4.2', {}, Y), rel('1.5.0')],
  'fern-config': [
    rel('2.0.0', { 'ansi-glyphs': '^1.0.0' }),
    rel('2.1.0', { 'ansi-glyphs': '^1.0.0' }),
    rel('2.3.0', { 'json-lattice': '^3.0.0' }),
  ],
  'json-lattice': [rel('3.0.0'), rel('3.1.2')],
  'lru-cellar': [
    rel('0.8.0+b1', {}, { published: '2023-06-01T12:00:00Z' }),
    rel('0.8.0+b2', {}, { published: '2023-06-09T12:00:00Z' }),
    rel('0.8.1', {}, { published: '2023-07-02T12:00:00Z' }),
    rel('0.9.0', {}, { published: '2023-09-15T12:00:00Z' }),
  ],
  'mesh-http': [rel('1.3.2'), rel('1.4.0'), rel('1.6.3', { 'rivet-retry': '^1.2.0' }), rel('1.9.0-rc.2', { 'rivet-retry': '^1.8.0' }), rel('2.0.0')],
  'quill-log': [rel('0.3.0'), rel('0.4.0'), rel('0.4.1'), rel('0.4.7'), rel('0.5.0'), rel('0.9.2')],
  'rivet-retry': [rel('1.0.0'), rel('1.2.0'), rel('1.8.3'), rel('2.0.0')],
  'spindle-tasks': [rel('1.1.0'), rel('1.2.0', { 'fern-config': '<2.2' })],
  'tidy-args': [rel('2.0.0'), rel('2.0.4'), rel('2.1.0-beta.2'), rel('2.1.0-beta.11')],
};

const projects = {
  storefront: {
    name: 'storefront',
    dependencies: { 'fern-config': '^2.0.0', 'spindle-tasks': '^1.1.0', 'quill-log': '^0.4.1', 'mesh-http': '^1.4.0' },
  },
  'ledger-cli': {
    name: 'ledger-cli',
    dependencies: { 'ember-uuid': '1.4.2', 'tidy-args': '>=2.1.0-beta.2 <2.2', 'rivet-retry': '~1' },
  },
  'batch-worker': {
    name: 'batch-worker',
    prefer: 'lowest',
    dependencies: { 'lru-cellar': '^0.8.0', 'rivet-retry': '>=1.2 <=1.8', 'fern-config': '2.0.x || 2.1.x' },
    overrides: { 'ansi-glyphs': '0.9.x' },
  },
};

const root = process.argv[2];
fs.mkdirSync(path.join(root, 'registry'), { recursive: true });
for (const [name, versions] of Object.entries(registry)) {
  fs.writeFileSync(path.join(root, 'registry', `${name}.json`), JSON.stringify({ name, versions }, null, 2) + '\n');
}
for (const [dir, m] of Object.entries(projects)) {
  fs.mkdirSync(path.join(root, 'examples', dir), { recursive: true });
  fs.writeFileSync(path.join(root, 'examples', dir, 'pin.json'), JSON.stringify(m, null, 2) + '\n');
}
