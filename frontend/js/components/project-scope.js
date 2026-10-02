// Shared project-scoping helpers for the header project switcher.
//
// The switcher (#project-select / #mobile-project-select) is filled by the
// dashboard and listened to by five components. Two rules keep that fan-out
// correct on the deployed build:
//
//   1. Only the dashboard may rewrite the switcher's options. A second writer
//      that rebuilt the list and then read the value back to "preserve" the
//      selection always read the freshly rendered first option, so whenever its
//      slower project request landed after the user had chosen another company
//      the switcher snapped back to the first project and the choice looked
//      ignored.
//   2. A component whose tab is not on screen does not reload straight away: it
//      records that it is stale and reloads when its tab is opened. A single
//      switch used to fire about twenty requests at an instance that serves one
//      request at a time, so the newly selected project took tens of seconds to
//      appear and looked frozen on the previous one.

const VIEW_ID_BY_TAB = {
  dashboard: 'dashboard-view',
  competitors: 'competitors-view',
  posts: 'posts-view',
  analytics: 'analytics-view',
  ideas: 'ideas-view'
};

// Read the project currently chosen in the header switcher. Read at the moment
// of use, so a project chosen after a component started waiting is honoured.
export function readActiveProjectId() {
  const desktop = parseInt(document.getElementById('project-select')?.value, 10);
  if (desktop) return desktop;
  const mobile = parseInt(document.getElementById('mobile-project-select')?.value, 10);
  return mobile || null;
}

// Label shown in the switcher for the active project ("style", "bcafe", ...).
export function selectedProjectLabel() {
  const select = document.getElementById('project-select');
  if (!select || select.selectedIndex < 0) return null;
  const option = select.options[select.selectedIndex];
  // A placeholder option ("Loading projects...", "API unreachable - retrying...")
  // is not a project, so it must never be shown as the active company's name.
  if (!option || !parseInt(option.value, 10)) return null;
  const label = option.textContent.trim();
  return label && !/^loading/i.test(label) ? label : null;
}

// Wrap a component's project-scoped loader so that a switch made from any tab
// reloads only the tab that is on screen, and a hidden tab catches up when it
// is opened. `reload` receives no arguments and must not reject.
export function createProjectReloader({ tab, reload }) {
  if (!VIEW_ID_BY_TAB[tab]) {
    throw new Error(`Unknown tab for project reloading: ${tab}`);
  }

  let stale = false;
  let running = false;

  function viewVisible() {
    const view = document.getElementById(VIEW_ID_BY_TAB[tab]);
    return !!view && !view.classList.contains('hidden');
  }

  async function run() {
    if (!viewVisible()) {
      // Off screen: remember the change and reload when the tab is opened.
      stale = true;
      return;
    }
    if (running) {
      // A load is in flight: finish it, then reload once more for the change.
      stale = true;
      return;
    }
    running = true;
    try {
      do {
        stale = false;
        await reload();
      } while (stale && viewVisible());
    } catch (error) {
      console.error(`Project reload failed for the ${tab} view:`, error);
    } finally {
      running = false;
    }
  }

  window.addEventListener('tab-changed', (event) => {
    if (event.detail?.tab !== tab) return;
    if (stale) run();
  });

  document.addEventListener('competitor-updated', (event) => {
    if (event.detail?.projectId && Number(event.detail.projectId) !== readActiveProjectId()) return;
    run();
  });

  document.addEventListener('scrape-completed', (event) => {
    if (event.detail?.projectId && Number(event.detail.projectId) !== readActiveProjectId()) return;
    run();
  });

  return { reload: run };
}
