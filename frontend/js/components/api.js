// API Service for communicating with backend
//
// The API base URL is resolved at runtime so the SAME frontend works in every
// environment without code changes:
//   1. window.__API_BASE__  - explicit override (set it in index.html before
//      app.js loads, if you ever need to point somewhere else).
//   2. http://localhost:10000/api when the page itself is served from
//      localhost - local development (matches .env.example PORT=10000).
//   3. "/api" - relative path for production: Vercel forwards /api/* to the
//      backend using the rewrite in frontend/vercel.json, and the Docker
//      frontend (nginx) proxies /api/* to the backend container.
function resolveApiBaseURL() {
  if (typeof window !== 'undefined' && window.__API_BASE__) {
    return window.__API_BASE__;
  }
  const host = (typeof window !== 'undefined' && window.location && window.location.hostname) || '';
  if (!host || host === 'localhost' || host === '127.0.0.1') {
    return 'http://localhost:10000/api';
  }
  return '/api';
}

export function initAPI() {
  const BASE_URL = resolveApiBaseURL(); // Backend API URL

  return {
    // Project methods
    getProjects: async () => {
      const response = await fetch(`${BASE_URL}/projects`);
      if (!response.ok) throw new Error('Failed to fetch projects');
      return response.json();
    },

    createProject: async (projectData) => {
      const response = await fetch(`${BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      });
      if (!response.ok) throw new Error('Failed to create project');
      return response.json();
    },

    getProject: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}`);
      if (!response.ok) throw new Error('Failed to fetch project');
      return response.json();
    },

    updateProject: async (projectId, projectData) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(projectData)
      });
      if (!response.ok) throw new Error('Failed to update project');
      return response.json();
    },

    deleteProject: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete project');
      return response.json();
    },

    // Competitor methods
    getCompetitors: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/competitors`);
      if (!response.ok) throw new Error('Failed to fetch competitors');
      return response.json();
    },

    addCompetitor: async (projectId, competitorData) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/competitors`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(competitorData)
      });
      if (!response.ok) throw new Error('Failed to add competitor');
      return response.json();
    },

    updateCompetitor: async (competitorId, competitorData) => {
      const response = await fetch(`${BASE_URL}/competitors/${competitorId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(competitorData)
      });
      if (!response.ok) throw new Error('Failed to update competitor');
      return response.json();
    },

    deleteCompetitor: async (competitorId) => {
      const response = await fetch(`${BASE_URL}/competitors/${competitorId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete competitor');
      return response.json();
    },

    discoverCompetitors: async (projectId, discoveryData) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/discover-competitors`, {
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
      const response = await fetch(`${BASE_URL}/projects/${projectId}/keywords`);
      if (!response.ok) throw new Error('Failed to fetch keywords');
      return response.json();
    },

    addKeyword: async (projectId, keywordData) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/keywords`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(keywordData)
      });
      if (!response.ok) throw new Error('Failed to add keyword');
      return response.json();
    },

    deleteKeyword: async (keywordId) => {
      const response = await fetch(`${BASE_URL}/keywords/${keywordId}`, {
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
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch posts');
      return response.json();
    },

    getPost: async (postId) => {
      const response = await fetch(`${BASE_URL}/posts/${postId}`);
      if (!response.ok) throw new Error('Failed to fetch post');
      const data = await response.json();
      return data.post || data;
    },

    // Scraping methods
    scrapeCompetitors: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/scrape`, {
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
      const listResponse = await fetch(`${BASE_URL}/projects/${projectId}/competitors`);
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
          const response = await fetch(`${BASE_URL}/competitors/${competitor.id}/scrape`, {
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
      const response = await fetch(`${BASE_URL}/competitors/${competitorId}/scrape`, {
        method: 'POST'
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || 'Failed to scrape competitor');
      }
      return response.json();
    },

    getScrapingLogs: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/scraping-logs`);
      if (!response.ok) throw new Error('Failed to fetch scraping logs');
      return response.json();
    },

    getScrapingStats: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/scraping-stats`);
      if (!response.ok) throw new Error('Failed to fetch scraping statistics');
      return response.json();
    },

    // AI Analysis methods
    analyzeProject: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/analyze`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to analyze project');
      return response.json();
    },

    // Content Generation methods
    generateIdeas: async (projectId, count = 5) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/ideas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ count })
      });
      if (!response.ok) throw new Error('Failed to generate ideas');
      return response.json();
    },

    generateCompleteUpdate: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/complete-update`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to generate complete update');
      return response.json();
    },

    // Generated Ideas methods
    getGeneratedIdeas: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/generated-ideas`);
      if (!response.ok) throw new Error('Failed to fetch generated ideas');
      return response.json();
    },

    markIdeaUsed: async (ideaId) => {
      const response = await fetch(`${BASE_URL}/generated-ideas/${ideaId}/use`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to mark idea as used');
      return response.json();
    },

    // Analytics & Market Intelligence methods (PDF Spec Compliance)
    getTopicFrequency: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/analytics/topics`);
      if (!response.ok) throw new Error('Failed to fetch topic frequency');
      return response.json();
    },

    getKeywordFrequency: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/analytics/keywords`);
      if (!response.ok) throw new Error('Failed to fetch keyword frequency');
      return response.json();
    },

    getMarketOverview: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/market-overview`);
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
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch project reviews');
      return response.json();
    },

    getReviewAnalytics: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/reviews/analytics`);
      if (!response.ok) throw new Error('Failed to fetch review analytics');
      return response.json();
    },

    // Place identity methods
    autocompletePlaces: async (query, location) => {
      const params = new URLSearchParams({ q: query });
      if (location) params.append('location', location);
      const response = await fetch(`${BASE_URL}/places/autocomplete?${params}`);
      if (!response.ok) throw new Error('Failed to autocomplete places');
      return response.json();
    },

    listPlaces: async (query = '', limit = 50) => {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      params.append('limit', String(limit));
      const response = await fetch(`${BASE_URL}/places?${params}`);
      if (!response.ok) throw new Error('Failed to list places');
      return response.json();
    },

    searchPlaces: async (name, location, maxResults = 5) => {
      const response = await fetch(`${BASE_URL}/places/search`, {
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
      const response = await fetch(`${BASE_URL}/places/${placeId}`);
      if (!response.ok) throw new Error('Failed to get place detail');
      return response.json();
    },

    getProjectPlaces: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/places`);
      if (!response.ok) throw new Error('Failed to get project places');
      return response.json();
    },

    getMarketGaps: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/market-gaps`);
      if (!response.ok) throw new Error('Failed to get market gaps');
      return response.json();
    },

    getTopicTrends: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/trend-analysis`);
      if (!response.ok) throw new Error('Failed to get trend analysis');
      return response.json();
    },

    // Competitor verification
    verifyCompetitor: async (data) => {
      const response = await fetch(`${BASE_URL}/competitors/verify`, {
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
      const response = await fetch(`${BASE_URL}/places/autocomplete?${params}`);
      if (!response.ok) throw new Error('Failed to autocomplete places');
      return response.json();
    },

    listPlaces: async (query = '', limit = 50) => {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      params.append('limit', String(limit));
      const response = await fetch(`${BASE_URL}/places?${params}`);
      if (!response.ok) throw new Error('Failed to list places');
      return response.json();
    },

    resolvePlace: async (name, location, options = {}) => {
      const response = await fetch(`${BASE_URL}/places/resolve`, {
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
      const response = await fetch(`${BASE_URL}/places/${placeId}`);
      if (!response.ok) throw new Error('Failed to get place detail');
      return response.json();
    },

    getProjectPlaces: async (projectId) => {
      const response = await fetch(`${BASE_URL}/projects/${projectId}/places`);
      if (!response.ok) throw new Error('Failed to get project places');
      return response.json();
    },

    // Google Maps scraping diagnostics (Selenium / Chrome / reachability)
    getPlacesDiagnostics: async () => {
      const response = await fetch(`${BASE_URL}/places/diagnostics`);
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