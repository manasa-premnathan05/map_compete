// Verifies the frontend API base-URL resolution in frontend/js/components/api.js
//
// The same frontend runs on (a) Vercel, where it must use the relative "/api"
// path so Vercel's rewrite proxies to the Render backend, and (b) localhost,
// where it must auto-detect a running local backend and never point at a
// non-MapCompete server. This script imports the real module and feeds it
// canned /api/health responses for each environment.
//
// Usage: node verify_api_base.mjs     (exit code 0 = all scenarios passed)

import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const API_MODULE = path.resolve('frontend/js/components/api.js');
const RENDER_BASE = 'https://map-compete.onrender.com/api';
const LOCAL_BASE = 'http://localhost:10000/api';

let failures = 0;

function check(name, ok, detail = '') {
  console.log(`[${ok ? 'PASS' : 'FAIL'}] ${name}${detail ? ` - ${detail}` : ''}`);
  if (!ok) failures += 1;
}

function jsonResponse(payload, status = 200) {
  return {
    ok: status < 400,
    status,
    json: async () => payload,
  };
}

// --- load the real module (no imports inside it, so a data: URL works) -------
const source = fs.readFileSync(API_MODULE, 'utf8');
const { initAPI } = await import(
  `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`
);

// A backend that is up and connected to MongoDB
const HEALTHY = { status: 'healthy', database: 'connected' };
// The right backend, but its MongoDB is unreachable (Atlas IP not allowlisted)
const DEGRADED = { status: 'degraded', database: 'disconnected', database_error: 'MongoDB is unreachable' };
// An old SQLite build / unrelated server: answers health WITHOUT `database`
const FOREIGN = { status: 'healthy' };

async function runScenario(name, hostname, behaviours, override, expected) {
  globalThis.window = { location: { hostname }, __API_BASE__: override };
  let projectsUrl = null;

  globalThis.fetch = async (url) => {
    const target = String(url);
    if (target.endsWith('/health')) {
      const base = target.replace(/\/health$/, '');
      const behaviour = behaviours[base];
      if (!behaviour) throw new TypeError('fetch failed');
      if (behaviour === 'healthy') return jsonResponse(HEALTHY);
      if (behaviour === 'degraded') return jsonResponse(DEGRADED, 503);
      if (behaviour === 'foreign') return jsonResponse(FOREIGN);
      throw new Error(`unknown behaviour ${behaviour}`);
    }
    projectsUrl = target;
    return jsonResponse({ projects: [] });
  };

  const api = await initAPI();
  await api.getProjects();
  check(
    name,
    projectsUrl === `${expected}/projects`,
    `requests went to ${projectsUrl} (expected ${expected}/projects)`
  );
}

await runScenario(
  'Vercel: uses the relative /api path (rewrite -> Render)',
  'map-compete.vercel.app',
  {},
  undefined,
  '/api'
);

await runScenario(
  'localhost: healthy local backend on :10000 wins',
  'localhost',
  { [LOCAL_BASE]: 'healthy' },
  undefined,
  LOCAL_BASE
);

await runScenario(
  'localhost: skips a legacy server on :5000 and uses the healthy deployed API',
  'localhost',
  {
    [LOCAL_BASE]: 'degraded',
    'http://localhost:5000/api': 'foreign',
    'http://127.0.0.1:5000/api': 'foreign',
    [RENDER_BASE]: 'healthy',
  },
  undefined,
  RENDER_BASE
);

await runScenario(
  'localhost: nothing but a legacy server answers -> never uses it',
  'localhost',
  { 'http://localhost:5000/api': 'foreign' },
  undefined,
  LOCAL_BASE
);

await runScenario(
  'localhost: no backend at all -> documented local port (clear errors)',
  'localhost',
  {},
  undefined,
  LOCAL_BASE
);

await runScenario(
  'window.__API_BASE__ override always wins',
  'localhost',
  { [LOCAL_BASE]: 'healthy' },
  'http://192.168.1.50:10000/api',
  'http://192.168.1.50:10000/api'
);

console.log('-'.repeat(72));
if (failures) {
  console.log(`${failures} scenario(s) FAILED`);
  process.exit(1);
}
console.log('ALL API BASE RESOLUTION SCENARIOS PASSED');
