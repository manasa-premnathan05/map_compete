import assert from 'node:assert/strict';
import fs from 'node:fs';

const source = fs.readFileSync(new URL('./frontend/js/components/api.js', import.meta.url), 'utf8');
const { initAPI } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
globalThis.window = { location: { hostname: 'map-compete.vercel.app' } };
const reply = (status, payload) => ({ ok: status < 400, status, json: async () => payload });
let calls = [];
globalThis.fetch = async (url) => {
  calls.push(url);
  return url.startsWith('/api') ? reply(502, {}) : reply(200, { projects: [{ id: 7 }] });
};
const api = await initAPI();
const results = await Promise.all([api.getProjects(), api.getProjects()]);
assert.equal(results[0].projects[0].id, 7);
assert.equal(calls.length, 2, 'concurrent loads must share recovery');
assert.equal(calls[1], 'https://map-compete.onrender.com/api/projects');

calls = [];
globalThis.fetch = async (url) => {
  calls.push(url);
  if (url.startsWith('/api')) throw new TypeError('Failed to fetch');
  return reply(200, { projects: [] });
};
assert.deepEqual(await api.getProjects(), { projects: [] });
assert.equal(calls.length, 2);

calls = [];
globalThis.fetch = async (url) => { calls.push(url); return reply(502, {}); };
await assert.rejects(api.createProject({ name: 'test' }));
assert.equal(calls.length, 1, 'writes must never be replayed');

globalThis.fetch = async () => reply(400, { error: 'Invalid request' });
await assert.rejects(api.getProjects(), /Invalid request/);
console.log('PASS: proxy recovery, network recovery, shared loading, no write replay, permanent errors');

calls = [];
let active = 0;
let peak = 0;
globalThis.fetch = async (url) => {
  calls.push(url);
  active += 1;
  peak = Math.max(peak, active);
  await new Promise((resolve) => setTimeout(resolve, 5));
  active -= 1;
  return reply(200, { scrape_status: 'SUCCESS' });
};
await Promise.all([api.scrapeCompetitor(1), api.scrapeCompetitor(1), api.scrapeCompetitor(2)]);
assert.equal(peak, 1, 'scrapes must be serialized');
assert.equal(calls.length, 2, 'duplicate scrape clicks must share a request');
assert.ok(calls.every((url) => url.startsWith('https://map-compete.onrender.com/api/')));
globalThis.fetch = async () => reply(500, { error: 'failed' });
await assert.rejects(api.scrapeCompetitor(3), /failed/);
globalThis.fetch = async () => reply(200, { scrape_status: 'SUCCESS' });
assert.equal((await api.scrapeCompetitor(4)).scrape_status, 'SUCCESS');
console.log('PASS: serialized direct scrapes, duplicate suppression, queue recovery');