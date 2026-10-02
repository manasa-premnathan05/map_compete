import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const listeners = new Map();
const views = { 'posts-view': true, 'dashboard-view': false };
globalThis.document = {
  getElementById(id) {
    if (id === 'project-select') return { value: '11' };
    return id in views ? { classList: { contains: () => views[id] } } : null;
  },
  addEventListener(name, handler) {
    const handlers = listeners.get(name) || [];
    handlers.push(handler);
    listeners.set(name, handlers);
  }
};
globalThis.window = { addEventListener: document.addEventListener };
const source = await readFile(new URL('./frontend/js/components/project-scope.js', import.meta.url), 'utf8');
const { createProjectReloader } = await import(`data:text/javascript;base64,${Buffer.from(source).toString('base64')}`);
let posts = 0;
let dashboard = 0;
createProjectReloader({ tab: 'posts', reload: async () => { posts++; } });
createProjectReloader({ tab: 'dashboard', reload: async () => { dashboard++; } });
async function emit(name, detail) {
  for (const handler of listeners.get(name) || []) handler({ detail });
  await new Promise(resolve => setTimeout(resolve, 0));
}
await emit('competitor-updated', { projectId: 11 });
assert.equal(posts, 0, 'hidden posts defer reads');
assert.equal(dashboard, 1, 'dashboard refreshes after a scrape');
views['posts-view'] = false;
await emit('tab-changed', { tab: 'posts' });
assert.equal(posts, 1, 'posts refresh when opened');
await emit('scrape-completed', { projectId: 7 });
assert.equal(posts, 1, 'other projects do not trigger reads');
await emit('scrape-completed', { projectId: 11 });
assert.equal(posts, 2, 'project crawl refreshes posts');
console.log('Scrape refresh regressions passed');