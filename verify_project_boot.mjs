// Regression tests for the project-list bootstrap (cold start handling).
//
// Opening the deployed app used to show "Loading projects..." for minutes: the
// first /projects read was aborted at the fast list budget while the free-tier
// instance was still booting, and the nested retry ladders multiplied the wait.
// These checks pin the behaviour that fixes it:
//   1. the first read of a session gets the cold-start budget;
//   2. a failed session still gives up after a bounded number of attempts inside
//      one cold boot, instead of retrying for minutes;
//   3. a proxy 502 falls through to the deployed backend directly;
//   4. concurrent callers share one in-flight request.
//
// Timers are recorded and released immediately, so no test actually waits.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const DEPLOYED = 'https://map-compete.onrender.com/api';
const COLD_START_BUDGET_CEILING = 120000; // one boot + retries, never minutes

const timers = [];
const realSetTimeout = globalThis.setTimeout;
globalThis.setTimeout = (fn, ms = 0, ...args) => {
  timers.push(ms);
  return realSetTimeout(fn, 0, ...args);
};

// Record abort budgets; the fake signal is never actually aborted.
class RecordingAbortController {
  constructor() {
    this.signal = { aborted: false, addEventListener: () => {} };
  }
  abort() {
    this.signal.aborted = true;
  }
}
globalThis.AbortController = RecordingAbortController;

// A browser-like host so the module resolves the production relative path.
globalThis.window = { location: { hostname: 'map-compete.vercel.app' } };

const urls = [];
let behaviours = [];
globalThis.fetch = async (url) => {
  urls.push(String(url));
  const behaviour = behaviours[Math.min(urls.length - 1, behaviours.length - 1)];
  if (behaviour === 'network-error') throw new TypeError('Failed to fetch');
  if (typeof behaviour === 'number') {
    return { ok: false, status: behaviour, json: async () => ({ error: 'gateway' }) };
  }
  return { ok: true, status: 200, json: async () => behaviour };
};

function reset(nextBehaviours) {
  behaviours = nextBehaviours;
  urls.length = 0;
  timers.length = 0;
}

const source = await readFile(new URL('./frontend/js/components/api.js', import.meta.url), 'utf8');
const { initAPI } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
const api = await initAPI();

// 1. A first read that fails while the instance boots is retried, and the budget
//    of that first attempt leaves room for the boot.
reset(['network-error', { projects: [{ id: 11, name: 'test' }, { id: 7, name: 'bcafe' }] }]);
const projects = await api.getProjects();
assert.deepEqual(projects.projects.map(p => p.name), ['test', 'bcafe']);
assert.equal(urls.length, 2, 'the cold start is retried inside the same call');
assert.equal(timers[0], 60000, `first attempt budget was ${timers[0]}ms, expected the cold-start budget`);

// 2. When nothing answers, the call still ends within one boot's worth of time
//    (three attempts), so the UI cannot sit on "Loading projects..." for minutes.
reset(['network-error']);
await assert.rejects(() => api.getProjects(), /Failed to fetch/);
// Each attempt tries the proxy and then the deployed backend directly, so the
// three attempts appear as six requests - but only three of them wait on a
// budget, and that wait is what must stay inside one cold boot.
const attemptBudgets = timers.filter(ms => ms >= 20000);
assert.equal(attemptBudgets.length, 3, `expected 3 attempts, saw ${attemptBudgets.length}`);
assert.equal(urls.length, 6, `expected 2 requests per attempt, saw ${urls.length}`);
const worstCase = timers.reduce((sum, ms) => sum + ms, 0);
assert.ok(worstCase <= COLD_START_BUDGET_CEILING,
  `worst case ${worstCase}ms must stay inside ${COLD_START_BUDGET_CEILING}ms`);

// 3. A sleeping instance behind the Vercel rewrite (502) is retried against the
//    deployed backend directly, in the same attempt.
reset([502, { projects: [{ id: 11, name: 'test' }] }]);
const after502 = await api.getProjects();
assert.equal(after502.projects.length, 1);
assert.equal(urls[1], `${DEPLOYED}/projects`, `expected a direct backend retry, saw ${urls[1]}`);
assert.equal(urls.length, 2, 'the 502 answered attempt resolves without another ladder');

// 4. Concurrent callers share a single in-flight request.
reset([{ projects: [{ id: 11, name: 'test' }] }]);
await Promise.all([api.getProjects(), api.getProjects()]);
assert.equal(urls.length, 1, `expected one shared request, saw ${urls.length}`);

console.log('Project bootstrap regressions passed');
