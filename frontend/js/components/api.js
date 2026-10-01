// API Service for communicating with backend
//
// The API base URL is resolved at runtime so the SAME frontend works in every
// environment without code changes:
//   1. window.__API_BASE__  - explicit override (set it in index.html before
//      app.js loads, if you ever need to point somewhere else).
//   2. On localhost the backend is auto-detected from LOCAL_API_CANDIDATES, so
//      the app works no matter which port the API was started on. A candidate
//      is accepted only when /api/health proves it is the MapCompete MongoDB
//      backend (it reports a `database` field) - a legacy SQLite build or an
//      unrelated server on the same port is skipped instead of feeding the UI
//      the wrong data.
//   3. "/api" - relative path for production: Vercel forwards /api/* to the
//      backend using the rewrite in frontend/vercel.json, and the Docker
//      frontend (nginx) proxies /api/* to the backend container.
const DEPLOYED_API_BASE = 'https://map-compete.onrender.com/api';

// Local development candidates, highest priority first. Port 10000 is the port
// configured in .env / .env.example (`python backend/api.py`); 5000 is the
// docker-compose / legacy port. Both localhost and 127.0.0.1 are probed because
// some Windows setups resolve only one of them. The deployed Render API comes
// last: local development keeps working (with real data) even when the local
// MongoDB connection is down, e.g. the machine's IP is not in the Atlas
// "Network Access" allowlist.
const LOCAL_API_CANDIDATES = [
  { base: 'http://localhost:10000/api', timeoutMs: 4000 },
  { base: 'http://127.0.0.1:10000/api', timeoutMs: 4000 },
  { base: 'http://localhost:5000/api', timeoutMs: 4000 },
  { base: 'http://127.0.0.1:5000/api', timeoutMs: 4000 },
  { base: DEPLOYED_API_BASE, timeoutMs: 15000 }
];

// Requests must never hang for ever: a stalled call used to leave the whole
// interface waiting with no error at all. Every request now carries an abort
// timeout, with a much larger budget for the operations that legitimately take
// minutes (collection, generation) than for list reads.
const DEFAULT_TIMEOUT_MS = 300000;   // 5 minutes - one collection run
const LIST_TIMEOUT_MS = 20000;       // list and detail reads answer in milliseconds

function callFetch(url, options) {
  // Indirection so a wrapper (or a test) can replace globalThis.fetch.
  return globalThis.fetch(url, options);
}

async function fetchWithTimeout(url, options = {}, timeoutMs = null) {
  if (options.signal || typeof AbortController === 'undefined') {
    return callFetch(url, options);
  }
  // Reads fail fast so a caller can retry; writes, collection and generation get
  // the long budget because they legitimately take minutes.
  const isRead = !options.method || String(options.method).toUpperCase() === 'GET';
  const budget = timeoutMs ?? (isRead ? LIST_TIMEOUT_MS : DEFAULT_TIMEOUT_MS);
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(new Error(`Request timed out after ${Math.round(budget / 1000)}s`)),
    budget
  );
  try {
    return await callFetch(url, { ...options, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

function isLocalHostname(host) {
  return !host
    || host === 'localhost'
    || host === '127.0.0.1'
    || host === '::1'
    || host.endsWith('.localhost');
}

// Ask one candidate who it is. Returns what /api/health revealed instead of
// throwing, so callers can rank all candidates in one pass.
async function probeCandidate({ base, timeoutMs }) {
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;
  try {
    const response = await fetchWithTimeout(`${base}/health`, {
      signal: controller ? controller.signal : undefined,
      cache: 'no-store'
    });
    const payload = await response.json().catch(() => null);
    return {
      base,
      reachable: true,
      // The MongoDB-era backend always reports `database`; anything else
      // answering on these ports is not the API this UI must talk to.
      isMapCompete: !!(payload && typeof payload.database === 'string'),
      healthy: response.ok && !!payload && payload.status === 'healthy',
      status: response.status
    };
  } catch (error) {
    return { base, reachable: false, isMapCompete: false, healthy: false, error };
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function pickLocalApiBase() {
  const results = await Promise.all(LOCAL_API_CANDIDATES.map(probeCandidate));

  // 1. First fully healthy MapCompete backend, in priority order (a local
  //    backend therefore always beats the deployed fallback).
  const healthy = results.find((r) => r.reachable && r.isMapCompete && r.healthy);
  if (healthy) {
    console.info(`[MapCompete] API: ${healthy.base} (database connected)`);
    return healthy.base;
  }

  // 2. The right backend is running but its database is unreachable. Point at
  //    it anyway so the UI shows the real 503 reason instead of pretending.
  const degraded = results.find((r) => r.reachable && r.isMapCompete);
  if (degraded) {
    console.error(
      `[MapCompete] API: ${degraded.base} answers but its MongoDB is unreachable. ` +
      'Add this machine\'s public IP to MongoDB Atlas -> Network Access ' +
      '(or set window.__API_BASE__ to a working API).'
    );
    return degraded.base;
  }

  // 3. Nothing that looks like the API answered: fail loudly on the documented
  //    local port instead of guessing.
  const unreachable = results.filter((r) => r.reachable && !r.isMapCompete).map((r) => r.base);
  if (unreachable.length) {
    console.warn(`[MapCompete] Ignored non-MapCompete servers on: ${unreachable.join(', ')}`);
  }
  console.error(
    `[MapCompete] No MapCompete backend answered. Start one with ` +
    `"python backend/api.py" (expected ${LOCAL_API_CANDIDATES[0].base}).`
  );
  return LOCAL_API_CANDIDATES[0].base;
}

async function resolveApiBaseURL() {
  if (typeof window !== 'undefined' && window.__API_BASE__) {
    return window.__API_BASE__;
  }
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';
  if (!isLocalHostname(host)) {
    // Production: relative path so the Vercel rewrite / nginx proxy forwards
    // /api/* to the backend (no CORS, no hard-coded host).
    return '/api';
  }
  return pickLocalApiBase();
}

export async function initAPI() {
  const BASE_URL = await resolveApiBaseURL(); // Backend API URL

  return {
    // Project methods
    getProjects: async () => {
      // List reads must fail fast so the caller can retry quickly: a platform
      // proxy (502/504) or a stalled request is surfaced within seconds.
      const response = await fetchWithTimeout(`${BASE_URL}/projects`, {}, LIST_TIMEOUT_MS);
      if (!response.ok) {
        const error = new Error(`Failed to fetch projects (HTTP ${response.status})`);
        error.status = response.status;
        throw error;
      }
      return response.json();
    },

    createProject: async (projectData) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      });
      if (!response.ok) throw new Error('Failed to create project');
      return response.json();
    },

    getProject: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}`);
      if (!response.ok) throw new Error('Failed to fetch project');
      return response.json();
    },

    updateProject: async (projectId, projectData) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      });
      if (!response.ok) throw new Error('Failed to update project');
      return response.json();
    },

    deleteProject: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete project');
      return response.json();
    },

    // Competitor methods
    getCompetitors: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/competitors`);
      if (!response.ok) throw new Error('Failed to fetch competitors');
      return response.json();
    },

    addCompetitor: async (projectId, competitorData) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/competitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(competitorData)
      });
      if (!response.ok) throw new Error('Failed to add competitor');
      return response.json();
    },

    updateCompetitor: async (competitorId, competitorData) => {
      const response = await fetchWithTimeout(`${BASE_URL}/competitors/${competitorId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(competitorData)
      });
      if (!response.ok) throw new Error('Failed to update competitor');
      return response.json();
    },

    deleteCompetitor: async (competitorId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/competitors/${competitorId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete competitor');
      return response.json();
    },

    discoverCompetitors: async (projectId, discoveryData) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/discover-competitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(discoveryData || {})
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || 'Failed to discover competitors');
      }
      return response.json();
    },

    // Keyword methods
    getKeywords: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/keywords`);
      if (!response.ok) throw new Error('Failed to fetch keywords');
      return response.json();
    },

    addKeyword: async (projectId, keywordData) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(keywordData)
      });
      if (!response.ok) throw new Error('Failed to add keyword');
      return response.json();
    },

    deleteKeyword: async (keywordId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/keywords/${keywordId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete keyword');
      return response.json();
    },

    // Post methods
    getPosts: async (params = {}) => {
      const cleanParams = {};
      for (const [k, v] of Object.entries(params || {})) {
        if (v !== undefined && v !== null && v !== '' && v !== 'all') {
          cleanParams[k] = v;
        }
      }
      const queryParams = new URLSearchParams(cleanParams).toString();
      const url = queryParams ? `${BASE_URL}/posts?${queryParams}` : `${BASE_URL}/posts`;
      const response = await fetchWithTimeout(url);
      if (!response.ok) throw new Error('Failed to fetch posts');
      return response.json();
    },

    getPost: async (postId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/posts/${postId}`);
      if (!response.ok) throw new Error('Failed to fetch post');
      const data = await response.json();
      return data.post || data;
    },

    // Scraping methods
    scrapeCompetitors: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/scrape`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to start scraping');
      return response.json();
    },

    // Scrape every competitor of a project ONE BY ONE via the existing
    // per-competitor endpoint. The all-at-once project endpoint can run for
    // ~10 minutes, which exceeds Vercel's ~120s proxy limit for rewrites to
    // external origins; each single scrape finishes well within it. Results
    // are saved competitor by competitor, so partial progress is never lost.
    // onProgress(done, total, name) is optional (used for UI toasts).
    scrapeProjectSequentially: async (projectId, onProgress) => {
      const listResponse = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/competitors`);
      if (!listResponse.ok) throw new Error('Failed to fetch competitors');
      const payload = await listResponse.json();
      const competitors = Array.isArray(payload) ? payload : (payload.competitors || []);
      const targets = competitors.filter((c) => c && c.gmap_url);
      const skipped = competitors.length - targets.length;
      let succeeded = 0;
      let failed = 0;
      for (let i = 0; i < targets.length; i += 1) {
        const competitor = targets[i];
        if (typeof onProgress === 'function') {
          onProgress(i + 1, targets.length, competitor.name);
        }
        try {
          const response = await fetchWithTimeout(`${BASE_URL}/competitors/${competitor.id}/scrape`, {
            method: 'POST'
          });
          if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${response.status}`);
          }
          succeeded += 1;
        } catch (err) {
          failed += 1;
          console.warn(`Scrape failed for ${competitor.name}:`, err);
        }
      }
      return { total: targets.length, succeeded, failed, skipped };
    },

    scrapeCompetitor: async (competitorId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/competitors/${competitorId}/scrape`, {
        method: 'POST'
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || 'Failed to scrape competitor');
      }
      return response.json();
    },

    getScrapingLogs: async (projectId, { includeStats = true } = {}) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/scraping-logs?include_stats=${includeStats ? 1 : 0}`);
      if (!response.ok) throw new Error('Failed to fetch scraping logs');
      return response.json();
    },

    getScrapingStats: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/scraping-stats`);
      if (!response.ok) throw new Error('Failed to fetch scraping statistics');
      return response.json();
    },

    // AI Analysis methods
    analyzeProject: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/analyze`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to analyze project');
      return response.json();
    },

    // Content Generation methods
    generateIdeas: async (projectId, count = 5) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/ideas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count })
      });
      if (!response.ok) throw new Error('Failed to generate ideas');
      return response.json();
    },

    generateCompleteUpdate: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/complete-update`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to generate complete update');
      return response.json();
    },

    // Generated Ideas methods
    getGeneratedIdeas: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/generated-ideas`);
      if (!response.ok) throw new Error('Failed to fetch generated ideas');
      return response.json();
    },

    markIdeaUsed: async (ideaId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/generated-ideas/${ideaId}/use`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to mark idea as used');
      return response.json();
    },

    // Analytics & Market Intelligence methods (PDF Spec Compliance)
    getTopicFrequency: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/analytics/topics`);
      if (!response.ok) throw new Error('Failed to fetch topic frequency');
      return response.json();
    },

    getKeywordFrequency: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/analytics/keywords`);
      if (!response.ok) throw new Error('Failed to fetch keyword frequency');
      return response.json();
    },

    getMarketOverview: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/market-overview`);
      if (!response.ok) throw new Error('Failed to fetch market overview');
      return response.json();
    },

    getProjectReviews: async (projectId, params = {}) => {
      const cleanParams = {};
      for (const [k, v] of Object.entries(params || {})) {
        if (v !== undefined && v !== null && v !== '' && v !== 'all') {
          cleanParams[k] = v;
        }
      }
      const queryParams = new URLSearchParams(cleanParams).toString();
      const url = queryParams ? `${BASE_URL}/projects/${projectId}/reviews?${queryParams}` : `${BASE_URL}/projects/${projectId}/reviews`;
      const response = await fetchWithTimeout(url);
      if (!response.ok) throw new Error('Failed to fetch project reviews');
      return response.json();
    },

    getReviewAnalytics: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/reviews/analytics`);
      if (!response.ok) throw new Error('Failed to fetch review analytics');
      return response.json();
    },

    // Place identity methods
    autocompletePlaces: async (query, location) => {
      const params = new URLSearchParams({ q: query });
      if (location) params.append('location', location);
      const response = await fetchWithTimeout(`${BASE_URL}/places/autocomplete?${params}`);
      if (!response.ok) throw new Error('Failed to autocomplete places');
      return response.json();
    },

    listPlaces: async (query = '', limit = 50) => {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      params.append('limit', String(limit));
      const response = await fetchWithTimeout(`${BASE_URL}/places?${params}`);
      if (!response.ok) throw new Error('Failed to list places');
      return response.json();
    },

    searchPlaces: async (name, location, maxResults = 5) => {
      const response = await fetchWithTimeout(`${BASE_URL}/places/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, location, max_results: maxResults })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        // Keep the backend's real reason (CAPTCHA / BLOCKED / SELECTOR_FAILURE /
        // TIMEOUT / BROWSER_ERROR) instead of a generic message.
        const error = new Error(payload.error || payload.message
          || 'The Google Maps search failed on the server.');
        error.status = response.status;
        error.errorType = payload.error_type || 'UNKNOWN';
        error.state = payload.state || null;
        error.diagnostics = payload.diagnostics || null;
        throw error;
      }
      return payload;
    },

    getPlaceDetail: async (placeId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/places/${placeId}`);
      if (!response.ok) throw new Error('Failed to get place detail');
      return response.json();
    },

    getProjectPlaces: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/places`);
      if (!response.ok) throw new Error('Failed to get project places');
      return response.json();
    },

    getMarketGaps: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/market-gaps`);
      if (!response.ok) throw new Error('Failed to get market gaps');
      return response.json();
    },

    getTopicTrends: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/trend-analysis`);
      if (!response.ok) throw new Error('Failed to get trend analysis');
      return response.json();
    },

    // Competitor verification
    verifyCompetitor: async (data) => {
      const response = await fetchWithTimeout(`${BASE_URL}/competitors/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const error = new Error(payload.error || payload.message
          || 'The competitor verification failed on the server.');
        error.status = response.status;
        error.errorType = payload.error_type || 'UNKNOWN';
        error.payload = payload;
        throw error;
      }
      return payload;
    },

    // Place identity methods
    autocompletePlaces: async (query, location) => {
      const params = new URLSearchParams({ q: query });
      if (location) params.append('location', location);
      const response = await fetchWithTimeout(`${BASE_URL}/places/autocomplete?${params}`);
      if (!response.ok) throw new Error('Failed to autocomplete places');
      return response.json();
    },

    listPlaces: async (query = '', limit = 50) => {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      params.append('limit', String(limit));
      const response = await fetchWithTimeout(`${BASE_URL}/places?${params}`);
      if (!response.ok) throw new Error('Failed to list places');
      return response.json();
    },

    resolvePlace: async (name, location, options = {}) => {
      const response = await fetchWithTimeout(`${BASE_URL}/places/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, location, ...options })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        // Preserve the backend's real reason (CAPTCHA / BLOCKED / NO_RESULTS...)
        const error = new Error(payload.error || payload.message
          || 'The Google Maps lookup failed on the server.');
        error.status = response.status;
        error.errorType = payload.error_type || 'UNKNOWN';
        error.state = payload.state || null;
        error.payload = payload;
        throw error;
      }
      return payload;
    },

    getPlaceDetail: async (placeId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/places/${placeId}`);
      if (!response.ok) throw new Error('Failed to get place detail');
      return response.json();
    },

    getProjectPlaces: async (projectId) => {
      const response = await fetchWithTimeout(`${BASE_URL}/projects/${projectId}/places`);
      if (!response.ok) throw new Error('Failed to get project places');
      return response.json();
    },

    // Google Maps scraping diagnostics (Selenium / Chrome / reachability)
    getPlacesDiagnostics: async () => {
      const response = await fetchWithTimeout(`${BASE_URL}/places/diagnostics`);
      if (!response.ok) throw new Error('Failed to read scraping diagnostics');
      return response.json();
    },

    // Utility method for handling loading states
    showLoading: () => {
      document.getElementById('loading-overlay')?.classList.remove('hidden');
    },

    hideLoading: () => {
      document.getElementById('loading-overlay')?.classList.add('hidden');
    },

    showCAPTCHAModal: () => {
      document.getElementById('captcha-modal')?.classList.remove('hidden');
    },

    hideCAPTCHAModal: () => {
      document.getElementById('captcha-modal')?.classList.add('hidden');
    }
  };
}