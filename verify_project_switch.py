#!/usr/bin/env python3
"""
Verify that choosing a project in the header switcher really switches the app.

The switcher (#project-select) is shared: the dashboard owns it and the four other
components react to it. Two defects made a switch look ignored on the deployed
build, and this script pins both of them down.

  1. A second writer rebuilt the switcher's options from its own project list.
     Because it read the value back *after* the options had been replaced - which
     always yields the first option of the fresh list - its "preserve the current
     selection" logic could never work, so a project request that answered after
     the user had chosen another company snapped the switcher back to the first
     project ("still shows style").
  2. Every component reloaded at once. One switch fired about twenty requests at
     an instance that serves a single request at a time, so the newly selected
     project took tens of seconds to appear and looked frozen on the old one.

What this script asserts, against a running frontend:

  * the switcher and the dashboard heading both keep the chosen project,
  * the heading changes the moment the switch is made, not when the data lands,
  * a switch reloads only the tab on screen: the hidden tabs' own endpoints stay
    silent until their tab is opened,
  * opening a hidden tab then loads that tab for the newly chosen project,
  * a switch made while another tab is open does not fetch dashboard data until
    the Dashboard tab is opened again,
  * no component rewrites the switcher after the user has chosen a project.

Usage:
    python serve_local.py                                 # terminal 1 (optional)
    python verify_project_switch.py                       # http://localhost:3000
    python verify_project_switch.py https://map-compete.vercel.app

Exit code 0 = every check passed, 1 = at least one failure.
"""

import json
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select

DEFAULT_URL = "http://localhost:3000"

# Endpoint fragments that identify which component issued a request. The
# dashboard and the analytics view share several reads, so only the fragments
# that belong to exactly one component are usable as markers.
DASHBOARD_ONLY = ("/scraping-stats", "/scraping-logs")
ANALYTICS_ONLY = ("/market-overview", "/reviews/analytics", "/trend-analysis", "/reviews?")
POSTS_ONLY = ("include_public=true",)
IDEAS_ONLY = ("limit=200",)
COMPETITORS_KEYWORDS = "/keywords"

TAB_ELEMENT_ID = {
    "dashboard": "dashboard-tab",
    "competitors": "competitors-tab",
    "posts": "posts-tab",
    "analytics": "analytics-tab",
    "ideas": "ideas-tab",
}

# Installed into the page before the first interaction: records every API request
# with a timestamp, every rewrite of the switcher's options with a stack trace,
# and every uncaught error.
INSTRUMENT = r"""
window.__reqs = window.__reqs || [];
window.__writes = window.__writes || [];
window.__errors = window.__errors || [];
if (!window.__hooked) {
  window.__hooked = true;
  window.addEventListener('error', e =>
    window.__errors.push('error: ' + (e.message || '') + ' @ ' + (e.filename || '') + ':' + (e.lineno || 0)));
  window.addEventListener('unhandledrejection', e =>
    window.__errors.push('rejection: ' + ((e.reason && (e.reason.message || e.reason)) || '')));
  const originalFetch = window.fetch;
  window.fetch = function () {
    const args = arguments;
    const url = (typeof args[0] === 'string') ? args[0] : (args[0] && args[0].url) || '';
    if (url.indexOf('/api/') !== -1 || url.indexOf('onrender.com/api') !== -1) {
      window.__reqs.push({ at: Math.round(performance.now()), url: url });
    }
    return originalFetch.apply(this, args);
  };
}
const select = document.getElementById('project-select');
if (select && !select.dataset.probed) {
  select.dataset.probed = '1';
  const descriptor = Object.getOwnPropertyDescriptor(Element.prototype, 'innerHTML');
  Object.defineProperty(select, 'innerHTML', {
    configurable: true,
    get() { return descriptor.get.call(this); },
    set(value) {
      window.__writes.push({
        at: Math.round(performance.now()),
        value: this.value,
        stack: (new Error('options rewritten')).stack
      });
      descriptor.set.call(this, value);
    }
  });
}
return true;
"""

SAMPLE = r"""
const text = id => (document.getElementById(id) || {}).textContent || '';
const select = document.getElementById('project-select');
const option = select && select.selectedIndex >= 0 ? select.options[select.selectedIndex] : null;
return {
  at: Math.round(performance.now()),
  projectId: select ? select.value : null,
  projectName: option ? option.textContent.trim() : null,
  title: text('dashboard-project-title').trim(),
  competitors: text('competitors-count').trim(),
  posts: text('total-posts-count').trim(),
  sync: text('dashboard-last-sync').trim()
};
"""


class Reporter:
    """Tiny PASS/FAIL reporter: collects results and prints them as they run."""

    def __init__(self):
        self.failures = []

    def check(self, name, ok, detail=""):
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
        if not ok:
            self.failures.append(name)

    def summary(self):
        print()
        print("-" * 72)
        if self.failures:
            print(f"{len(self.failures)} check(s) FAILED:")
            for name in self.failures:
                print(f"  - {name}")
            return 1
        print("All project-switch checks passed.")
        return 0


def build_driver():
    options = Options()
    for flag in ("--headless=new", "--no-sandbox", "--disable-dev-shm-usage",
                 "--disable-gpu", "--window-size=1400,1000", "--log-level=3"):
        options.add_argument(flag)
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def wait_for(driver, script, timeout=60, interval=0.25, message="condition"):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            last = driver.execute_script(script)
        except Exception:  # noqa: BLE001 - the page may still be navigating
            last = None
        if last:
            return last
        time.sleep(interval)
    raise AssertionError(f"timed out waiting for {message} (last: {last!r})")


def requests(driver):
    return driver.execute_script("return window.__reqs || [];")


def urls_since(driver, since_ms):
    return [r["url"] for r in requests(driver) if r["at"] >= since_ms]


def mark(driver):
    """Current page timestamp, so later request sets can be filtered by it."""
    return driver.execute_script("return Math.round(performance.now());")


def click_tab(driver, tab):
    element = driver.find_element(By.ID, TAB_ELEMENT_ID[tab])
    driver.execute_script("arguments[0].scrollIntoView({block: 'nearest'});", element)
    element.click()
    time.sleep(0.4)


def switch_to(driver, value):
    """Select a project the way a user does: change the <select> and fire change."""
    Select(driver.find_element(By.ID, "project-select")).select_by_value(value)


def numeric(value):
    return bool(value) and value.replace(",", "").replace(".", "").isdigit()

def poll_settled(driver, expected_name, timeout=75):
    """Wait for the heading to be the expected project and its figures to be shown.

    The "Loading..." text a switch puts on the sync line must also be gone, so a
    load that never answers cannot pass for a finished one.
    """
    deadline = time.time() + timeout
    sample = driver.execute_script(SAMPLE)
    while time.time() < deadline:
        sample = driver.execute_script(SAMPLE)
        if (sample["title"] == expected_name
                and numeric(sample["competitors"])
                and numeric(sample["posts"])
                and not sample["sync"].startswith("Loading")):
            return sample
        time.sleep(0.5)
    return None


def appeared(driver, since_ms, needle, timeout=45):
    """Wait for a request containing `needle` that was issued after `since_ms`."""
    deadline = time.time() + timeout
    script = (
        "const since = arguments[0], needle = arguments[1];"
        "return (window.__reqs || []).some(r => r.at >= since && r.url.indexOf(needle) !== -1);"
    )
    while time.time() < deadline:
        try:
            if driver.execute_script(script, since_ms, needle):
                return True
        except Exception:  # noqa: BLE001 - the page may still be navigating
            pass
        time.sleep(0.4)
    return False


def appeared_all(driver, since_ms, fragments, timeout=45):
    """Wait for a request that contains every fragment, issued after `since_ms`."""
    deadline = time.time() + timeout
    script = (
        "const since = arguments[0], fragments = arguments[1];"
        "return (window.__reqs || []).some(r => r.at >= since"
        " && fragments.every(f => r.url.indexOf(f) !== -1));"
    )
    while time.time() < deadline:
        try:
            if driver.execute_script(script, since_ms, fragments):
                return True
        except Exception:  # noqa: BLE001 - the page may still be navigating
            pass
        time.sleep(0.4)
    return False


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    reporter = Reporter()
    driver = build_driver()
    try:
        print(f"Loading {url} ...")
        driver.get(url)
        wait_for(
            driver,
            "const s = document.getElementById('project-select');"
            "return s && s.options.length > 0 && !!s.value;",
            timeout=90,
            message="the project switcher to populate",
        )
        # Hook the page before the user interacts with it, then again once the
        # first load has finished, so no component can register late.
        driver.execute_script(INSTRUMENT)
        time.sleep(4)
        driver.execute_script(INSTRUMENT)

        options = [(o.get_attribute("value"), o.text.strip())
                   for o in driver.find_elements(By.CSS_SELECTOR, "#project-select option")]
        reporter.check(
            "switcher lists every project",
            len(options) >= 2,
            ", ".join(f"{value}={name}" for value, name in options),
        )
        if len(options) < 2:
            return reporter.summary()

        first_id, first_name = options[0]
        other_id, other_name = options[1]
        print(f"Switching '{first_name}' (id={first_id}) -> '{other_name}' (id={other_id})")

        # Let the first load finish: the complaint this script guards against is a
        # switch made once the page already shows a project.
        reporter.check(
            "the first project's figures load before any switch",
            poll_settled(driver, first_name, timeout=90) is not None,
            json.dumps(driver.execute_script(SAMPLE)),
        )

        # ----------------------------------------------------------------- switch
        # Timestamp first: the requests a switch issues are dispatched from a
        # microtask that drains before the next script the driver runs, so a
        # timestamp taken afterwards would sit just past them.
        switch_at = mark(driver)
        switch_to(driver, other_id)
        time.sleep(0.8)
        immediate = driver.execute_script(SAMPLE)
        reporter.check(
            "the switcher keeps the project the user chose",
            immediate["projectId"] == other_id,
            f"switcher value={immediate['projectId']!r}, heading={immediate['title']!r}",
        )
        reporter.check(
            "the dashboard heading follows the switch immediately",
            immediate["title"] == other_name,
            f"heading={immediate['title']!r}, expected {other_name!r}",
        )


        time.sleep(2.5)
        burst = urls_since(driver, switch_at)
        reporter.check(
            "the switch reloads the visible dashboard",
            any(fragment in u for u in burst for fragment in DASHBOARD_ONLY),
            f"{len(burst)} request(s) issued by the switch",
        )
        reporter.check(
            "the switch does not fire every component again",
            len(burst) <= 14,
            f"{len(burst)} request(s): " + ", ".join(u.split('/api/')[-1][:38] for u in burst[:8]),
        )
        leaks = {
            "analytics": [u for u in burst if f"/projects/{other_id}" in u
                          and any(f in u for f in ANALYTICS_ONLY)],
            "posts": [u for u in burst if f"project_id={other_id}" in u and "include_public=true" in u],
            "ideas": [u for u in burst if f"project_id={other_id}" in u and "limit=200" in u],
            "competitors": [u for u in burst if f"/projects/{other_id}/keywords" in u],
        }
        for view, leaked in leaks.items():
            reporter.check(
                f"the hidden {view} view stays idle while the dashboard is on screen",
                not leaked,
                "; ".join(leaked[:2]),
            )

        settled = poll_settled(driver, other_name)
        reporter.check(
            "the chosen project's figures replace the previous ones",
            settled is not None,
            json.dumps(settled or driver.execute_script(SAMPLE)),
        )

        late_writes = [w for w in driver.execute_script("return window.__writes || [];")
                       if w["at"] >= switch_at]
        reporter.check(
            "nothing rewrites the project list after the user chose a project",
            not late_writes,
            "; ".join(
                next((line.strip() for line in w["stack"].splitlines() if " at " in line), "")
                for w in late_writes[:2]
            ),
        )

        # --------------------------------------------------- hidden tab catch-up
        tab_at = mark(driver)
        click_tab(driver, "competitors")
        reporter.check(
            "opening the competitors tab loads the newly chosen project",
            appeared(driver, tab_at, f"/projects/{other_id}/keywords"),
            f"waited for /projects/{other_id}/keywords",
        )

        analytics_at = mark(driver)
        click_tab(driver, "analytics")
        reporter.check(
            "opening the analytics tab loads the newly chosen project",
            appeared(driver, analytics_at, f"/projects/{other_id}/market-overview"),
            f"waited for /projects/{other_id}/market-overview",
        )

        ideas_at = mark(driver)
        click_tab(driver, "ideas")
        reporter.check(
            "opening the ideas tab loads the newly chosen project",
            appeared(driver, ideas_at, "limit=200"),
            "waited for a posts request carrying limit=200",
        )


        # ------------------------------------------- switch from another tab
        click_tab(driver, "posts")
        time.sleep(2)
        hidden_at = mark(driver)
        switch_to(driver, first_id)
        time.sleep(0.5)
        hidden_state = driver.execute_script(SAMPLE)
        reporter.check(
            "the heading follows a switch made from another tab",
            hidden_state["title"] == first_name,
            f"heading={hidden_state['title']!r}, expected {first_name!r}",
        )

        time.sleep(2.5)
        hidden_burst = urls_since(driver, hidden_at)
        # The open tab reloads for the new project. It may be a moment later than
        # the switch: a reload that arrives while one is already in flight is
        # queued behind it rather than run twice at once.
        reporter.check(
            "the posts tab on screen reloads for the new project",
            appeared_all(driver, hidden_at, [f"project_id={first_id}", "include_public=true"]),
            f"{len(hidden_burst)} request(s) in the first 2.5s: "
            + ", ".join(u.split('/api/')[-1][:38] for u in hidden_burst[:8]),
        )
        reporter.check(
            "the hidden dashboard defers its reload",
            not [u for u in hidden_burst if f"/projects/{first_id}" in u
                 and any(f in u for f in DASHBOARD_ONLY)],
            "; ".join(u.split('/api/')[-1][:50] for u in hidden_burst if any(f in u for f in DASHBOARD_ONLY)),
        )
        reporter.check(
            "the hidden analytics and ideas views defer their reloads",
            not [u for u in hidden_burst if f"project_id={first_id}" in u and "limit=200" in u]
            and not [u for u in hidden_burst if f"/projects/{first_id}" in u
                     and any(f in u for f in ANALYTICS_ONLY)],
            "; ".join(u.split('/api/')[-1][:50] for u in hidden_burst if "limit=200" in u),
        )

        dashboard_at = mark(driver)
        click_tab(driver, "dashboard")
        reporter.check(
            "opening the dashboard loads the deferred project",
            appeared(driver, dashboard_at, f"/projects/{first_id}/scraping-stats"),
            f"waited for /projects/{first_id}/scraping-stats",
        )
        deferred = poll_settled(driver, first_name)
        reporter.check(
            "the dashboard shows the deferred project's figures",
            deferred is not None,
            json.dumps(deferred or driver.execute_script(SAMPLE)),
        )
        reporter.check(
            "the switcher still shows the project chosen last",
            (deferred or driver.execute_script(SAMPLE))["projectId"] == first_id,
            f"switcher value={driver.execute_script(SAMPLE)['projectId']!r}",
        )

        # Between the switch and the moment the dashboard tab was opened, no hidden
        # view fetched anything: the deferral lasted rather than merely arriving
        # late, which is what keeps a switch to one tab's worth of requests.
        hidden_window = [r for r in requests(driver) if hidden_at <= r["at"] < dashboard_at]
        late_hidden = [
            r["url"] for r in hidden_window
            if any(f in r["url"] for f in DASHBOARD_ONLY)
            or any(f in r["url"] for f in ANALYTICS_ONLY)
            or f"/projects/{first_id}/keywords" in r["url"]
            or (f"project_id={first_id}" in r["url"] and "limit=200" in r["url"])
        ]
        reporter.check(
            "no hidden view fetched anything while its tab was closed",
            not late_hidden,
            f"{len(hidden_window)} request(s) in the window"
            + ("; offending: " + "; ".join(u.split('/api/')[-1][:45] for u in late_hidden[:3]) if late_hidden else ""),
        )

        errors = driver.execute_script("return window.__errors || [];")
        reporter.check("no uncaught page errors", not errors, "; ".join(errors[:2]))

        severe = [e for e in driver.get_log("browser")
                  if e["level"] == "SEVERE" and "favicon" not in e["message"]]
        reporter.check("no console errors", not severe,
                       "; ".join(e["message"][:120] for e in severe[:2]))
    finally:
        driver.quit()

    return reporter.summary()


if __name__ == "__main__":
    sys.exit(main())

