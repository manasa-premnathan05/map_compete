// Competitors Component with Smart Google Maps Discovery & Keywords Management
export function initCompetitors(api) {
  const competitorsView = document.getElementById('competitors-view');
  if (!competitorsView) return;

  // State
  let currentProjectId = 1;
  let isOnlineScope = false;
  let lastDiscoveredCompetitors = [];
  let currentProjectCompetitors = [];
  let editingCompetitorId = null;
  // Result chosen in the "Search Google Maps" list. This MUST be the result
  // object itself (not its index): index 0 is falsy and any index >= 1 has no
  // `.name`/`.google_maps_url`, which previously made Resolve fail for every
  // entry except the first one.
  let selectedSearchResult = null;
  let selectedSearchResultIndex = null;
  let lastSearchResults = [];

  // Resolve the active project from the shared header switcher at call time.
  // The dashboard rewrites that <select> when a project is created/switched,
  // so relying on a cached id made tracked competitors attach to the wrong
  // (stale) project and new projects showed zero competitors.
  function activeProjectId() {
    const fromSelect = parseInt(projectSelectEl?.value, 10);
    const fromMobile = parseInt(document.getElementById('mobile-project-select')?.value, 10);
    return fromSelect || fromMobile || currentProjectId || 1;
  }

  // DOM Elements
  const projectSelectEl = document.getElementById('project-select');
  const competitorSearchEl = document.getElementById('competitor-search');
  const addCompetitorBtn = document.getElementById('add-competitor-btn');
  const competitorsTableBody = document.getElementById('competitors-table-body');

  // Discovery Elements
  const discoveryForm = document.getElementById('competitor-discovery-form');
  const discoveryCompanyEl = document.getElementById('discovery-company-name');
  const discoveryLocationEl = document.getElementById('discovery-location');
  const discoveryFieldEl = document.getElementById('discovery-field');
  const discoverBtn = document.getElementById('discover-competitors-btn');
  const discoveryResultsWrapper = document.getElementById('discovery-results-wrapper');
  const discoveryCardsGrid = document.getElementById('discovery-cards-grid');
  const discoveryMetaSummary = document.getElementById('discovery-meta-summary');
  const trackAllBtn = document.getElementById('track-all-discovered-btn');

  // Scope Toggle Buttons
  const scopeLocalBtn = document.getElementById('scope-local-btn');
  const scopeOnlineBtn = document.getElementById('scope-online-btn');
  const discoveryLocationLabel = document.getElementById('discovery-location-label');

  // Keywords Elements
  const addKeywordForm = document.getElementById('add-keyword-form');
  const newKeywordInput = document.getElementById('new-keyword-input');
  const projectKeywordsContainer = document.getElementById('project-keywords-container');

  // Modal Elements
  const addCompetitorModal = document.getElementById('add-competitor-modal');
  const addCompetitorForm = document.getElementById('add-competitor-form');
  const modalCompetitorName = document.getElementById('modal-competitor-name');
  const modalCompetitorUrl = document.getElementById('modal-competitor-url');
  const searchPlaceBtn = document.getElementById('search-place-btn');
  const resolvePlaceBtn = document.getElementById('resolve-place-btn');
  const searchResultsDisplay = document.getElementById('search-results-display');
  const searchResultsList = document.getElementById('search-results-list');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const resolvedPlaceDisplay = document.getElementById('resolved-place-display');
  const resolvedPlaceDetails = document.getElementById('resolved-place-details');
  const resolvedPlaceKey = document.getElementById('resolved-place-key');
  const resolvedGooglePlaceId = document.getElementById('resolved-google-place-id');
  const resolvedCid = document.getElementById('resolved-cid');
  const resolvedHexId = document.getElementById('resolved-hex-id');
  const closeCompetitorModalBtn = document.getElementById('close-competitor-modal-btn');
  const cancelCompetitorModalBtn = document.getElementById('cancel-competitor-modal-btn');
  const saveCompetitorBtn = document.getElementById('save-competitor-btn');

  // Initialize
  async function init() {
    try {
      await loadProjectSelector();
      // Pre-fill discovery form with project context after selector is loaded
      if (currentProjectId) {
        await prefillDiscoveryFromProject(currentProjectId);
      }
      await loadCompetitors();
      await loadKeywords();
      setupEventListeners();
    } catch (error) {
      console.error('Error initializing competitors component:', error);
    }
  }

  // Load project selector
  async function loadProjectSelector() {
    try {
      const response = await api.getProjects();
      const projects = response.projects || [];

      if (projectSelectEl) {
        projectSelectEl.innerHTML = projects.map(p => `
          <option value="${p.id}">${p.name}</option>
        `).join('');

        if (projects.length > 0) {
          // Keep an already-selected project: the dashboard may have switched
          // the header select before this component finished loading.
          const existing = parseInt(projectSelectEl.value, 10);
          const preserved = projects.some(p => p.id === existing);
          if (!preserved) projectSelectEl.value = String(projects[0].id);
          currentProjectId = parseInt(projectSelectEl.value, 10) || projects[0].id;

          // Pre-populate discovery company name with current project name
          if (discoveryCompanyEl && !discoveryCompanyEl.value) {
            const active = projects.find(p => p.id === currentProjectId) || projects[0];
            discoveryCompanyEl.value = active.name;
          }
        }
      }
    } catch (error) {
      console.error('Error loading projects:', error);
    }
  }

  // Load competitors for current project
  async function loadCompetitors() {
    try {
      api.showLoading();
      currentProjectId = activeProjectId();
      const response = await api.getCompetitors(currentProjectId);
      currentProjectCompetitors = response.competitors || [];
      renderCompetitorsTable(currentProjectCompetitors);
    } catch (error) {
      console.error('Error loading competitors:', error);
      showErrorState(error.message);
    } finally {
      api.hideLoading();
    }
  }

  // Load project target keywords
  async function loadKeywords() {
    if (!projectKeywordsContainer) return;
    try {
      const response = await api.getKeywords(activeProjectId());
      const keywords = response.keywords || [];
      renderKeywords(keywords);
    } catch (error) {
      console.error('Error loading keywords:', error);
      projectKeywordsContainer.innerHTML = `<span class="text-xs text-sand-500">No keywords added yet.</span>`;
    }
  }

  // Render keywords pills with remove action
  function renderKeywords(keywords) {
    if (!projectKeywordsContainer) return;

    if (!keywords || keywords.length === 0) {
      projectKeywordsContainer.innerHTML = `<span class="text-xs text-sand-500">No target keywords added yet. Add terms above to track competitor search alignment.</span>`;
      return;
    }

    const badgeThemes = ['badge-sage', 'badge-terracotta', 'badge-amber', 'badge-clay'];

    projectKeywordsContainer.innerHTML = keywords.map((kw, i) => {
      const theme = badgeThemes[i % badgeThemes.length];
      return `
        <span class="${theme} inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium shadow-2xs">
          <span>#${kw.keyword}</span>
          <button type="button" class="delete-keyword-btn hover:text-red-700 transition-colors ml-0.5" data-id="${kw.id}" title="Remove keyword">
            &times;
          </button>
        </span>
      `;
    }).join('');

    // Attach delete listeners
    projectKeywordsContainer.querySelectorAll('.delete-keyword-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const kid = e.currentTarget.dataset.id;
        try {
          await api.deleteKeyword(kid);
          window.showToast?.('Keyword removed', 'info');
          await loadKeywords();
        } catch (err) {
          window.showToast?.(`Error deleting keyword: ${err.message}`, 'error');
        }
      });
    });
  }

  // Render competitors table
  function renderCompetitorsTable(competitors) {
    if (!competitorsTableBody) return;

    if (!competitors || competitors.length === 0) {
      competitorsTableBody.innerHTML = `
        <tr>
          <td colspan="4" class="px-6 py-8 text-center text-xs text-sand-500">
            No competitors currently tracked in this project. Use the Smart Discovery search above or click "+ Add Custom" to enter one.
          </td>
        </tr>
      `;
      return;
    }

    const paletteClasses = ['bg-sage-100 text-sage-700', 'bg-terracotta-100 text-terracotta-700', 'bg-amber-100 text-amber-700', 'bg-clay-100 text-clay-700'];

    competitorsTableBody.innerHTML = competitors.map((competitor, idx) => {
      let host = '';
      if (competitor.gmap_url) {
        try {
          host = new URL(competitor.gmap_url).hostname;
        } catch (e) {
          host = competitor.gmap_url;
        }
      }
      const avatarClass = paletteClasses[idx % paletteClasses.length];

      // Identity badge
      const identitySource = competitor.identity_source || 'unknown';
      const isStrong = ['place_id', 'hex_id', 'cid', 'kgmid'].includes(identitySource);
      const identityBadge = isStrong
        ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sage-100 text-sage-700" title="Resolved via ${identitySource}">
            <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
            Google Maps Verified
          </span>`
        : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700" title="Manual entry: ${identitySource}">
            <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg>
            Manual Entry
          </span>`;

      // Shared projects indicator
      const sharedCount = competitor.shared_with_projects || 0;
      const sharedBadge = sharedCount > 0
        ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-terracotta-100 text-terracotta-700" title="Also tracked in ${sharedCount} other project${sharedCount > 1 ? 's' : ''}">
            <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M9 6a3 3 0 116 0 3 3 0 01-6 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>
            +${sharedCount} project${sharedCount > 1 ? 's' : ''}
          </span>`
        : '';

      return `
        <tr class="hover:bg-sand-50/70 transition-colors">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center space-x-3">
              <div class="flex-shrink-0">
                <div class="w-8 h-8 rounded-lg ${avatarClass} flex items-center justify-center text-xs font-bold shadow-xs">
                  ${competitor.name.charAt(0).toUpperCase()}
                </div>
              </div>
              <div class="min-w-0">
                <p class="text-xs font-bold text-sand-900">${competitor.name}</p>
                ${competitor.gmap_url ? `
                  <a href="${competitor.gmap_url}" target="_blank" rel="noopener noreferrer" class="text-[11px] text-sage-600 hover:text-sage-700 hover:underline flex items-center gap-1 mt-0.5">
                    <span>Google Maps Link</span>
                    <svg width="10" height="10" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg>
                  </a>
                ` : `<p class="text-[11px] text-sand-500 truncate max-w-xs">${host || 'Manual Profile'}</p>`}
                <div class="flex flex-wrap items-center gap-1.5 mt-1">
                  ${competitor.rating ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200"><svg width="9" height="9" viewBox="0 0 24 24" fill="#D4A373" stroke="#B8824C" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> ${competitor.rating.toFixed(1)} ${competitor.review_count ? `(${competitor.review_count.toLocaleString()})` : ''}</span>` : ''}
                  ${identityBadge}
                  ${sharedBadge}
                </div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-xs text-sand-500">
            ${competitor.last_scraped ? formatDate(competitor.last_scraped) : 'Never'}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-xs font-medium space-x-2">
            <button class="text-sage-600 hover:text-sage-700 p-1.5 rounded-lg hover:bg-sage-50 transition-colors" title="Scrape" data-id="${competitor.id}">
              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
              </svg>
            </button>
            <button class="text-sand-600 hover:text-sand-900 p-1.5 rounded-lg hover:bg-sand-100 transition-colors" title="Edit" data-id="${competitor.id}">
              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>
              </svg>
            </button>
            <button class="text-sand-600 hover:text-sand-900 p-1.5 rounded-lg hover:bg-sand-100 transition-colors" title="View Posts" data-id="${competitor.id}">
              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
              </svg>
            </button>
            <button class="text-terracotta-500 hover:text-terracotta-700 p-1.5 rounded-lg hover:bg-terracotta-50 transition-colors" title="Delete" data-id="${competitor.id}">
              <svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M3 6h18m-2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
              </svg>
            </button>
          </td>
        </tr>
      `;
    }).join('');

    addActionListeners();
  }

  // Handle Smart Discovery Search
  async function handleDiscovery(e) {
    if (e) e.preventDefault();

    const companyName = discoveryCompanyEl.value.trim();
    if (!companyName) {
      window.showToast?.('Please enter a company name', 'warning');
      return;
    }

    const location = discoveryLocationEl.value.trim();
    const field = discoveryFieldEl.value.trim();

    try {
      discoverBtn.disabled = true;
      discoverBtn.innerHTML = `
        <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Identifying...</span>
      `;

      const result = await api.discoverCompetitors(activeProjectId(), {
        company_name: companyName,
        location: location || null,
        field: field || null,
        is_online: isOnlineScope
      });

      lastDiscoveredCompetitors = result.competitors || [];
      renderDiscoveryResults(result);

      window.showToast?.(`Discovered ${lastDiscoveredCompetitors.length} competitors!`, 'success');
    } catch (err) {
      console.error('Error during competitor discovery:', err);
      window.showToast?.(`Discovery error: ${err.message}`, 'error');
    } finally {
      discoverBtn.disabled = false;
      discoverBtn.innerHTML = `
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
        <span>Discover</span>
      `;
    }
  }

  // Render Discovered Competitors Cards
  function renderDiscoveryResults(data) {
    if (!discoveryResultsWrapper || !discoveryCardsGrid) return;

    discoveryResultsWrapper.classList.remove('hidden');

    const locationText = data.inferred_location || (isOnlineScope ? 'Pan-India / Online' : 'Local Area');
    const fieldText = data.inferred_field || 'Industry Competitors';
    discoveryMetaSummary.textContent = `Found ${data.competitors?.length || 0} Competitors in ${locationText} (${fieldText})`;

    if (!data.competitors || data.competitors.length === 0) {
      discoveryCardsGrid.innerHTML = `
        <div class="col-span-full py-8 text-center text-xs text-sand-500">
          No competitors found for this search. Try modifying the location or industry category.
        </div>
      `;
      return;
    }

    discoveryCardsGrid.innerHTML = data.competitors.map((comp, idx) => {
      const isTracked = comp.already_tracked;
      const strengths = Array.isArray(comp.strengths) ? comp.strengths : [];
      
      // Identity badge
      const identitySource = comp.identity_source || 'unknown';
      const isStrong = ['place_id', 'hex_id', 'cid', 'kgmid'].includes(identitySource);
      const identityBadge = isStrong
        ? `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sage-100 text-sage-700" title="Resolved via ${identitySource}">
            <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
            Verified
          </span>`
        : `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700" title="Identity: ${identitySource}">
            <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z"/></svg>
            Discovered
          </span>`;

      // Already tracked indicator with details
      const trackedDetails = comp.tracked_in_other_projects && comp.tracked_in_other_projects.length > 0
        ? `<div class="text-[10px] text-terracotta-600 mt-1 flex items-center gap-1">
             <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M9 6a3 3 0 116 0 3 3 0 01-6 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z"/></svg>
             Also in: ${comp.tracked_in_other_projects.map(p => p.name).join(', ')}
           </div>`
        : '';

      const isOwnBusiness = comp.is_own_business;
      const ownBusinessBadge = isOwnBusiness
        ? `<div class="text-[10px] text-sage-600 mt-1 flex items-center gap-1">
             <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l4.293 4.293a1 1 0 001.414-1.414l-7-7z"/></svg>
             This is YOUR business
           </div>`
        : '';

      return `
        <div class="bg-white border ${isTracked ? 'border-sage-200' : isOwnBusiness ? 'border-terracotta-200' : 'border-[#E8E2D8]'} rounded-xl p-4 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between ${isTracked ? 'opacity-60' : ''}">
          <div>
            <div class="flex items-start justify-between gap-2 mb-1.5">
              <h4 class="text-sm font-bold text-sand-900 leading-snug">${comp.name}</h4>
              <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full ${isTracked ? 'bg-sage-100 text-sage-700' : isOwnBusiness ? 'bg-terracotta-100 text-terracotta-700' : 'bg-sand-100 text-sand-700'} whitespace-nowrap">
                ${comp.distance || (isOnlineScope ? 'Online' : 'Local')}
              </span>
            </div>

            <div class="flex items-center gap-2 mb-1">
              <p class="text-xs font-medium text-terracotta-700">${comp.category || fieldText}</p>
              ${identityBadge}
            </div>
            <p class="text-[11px] text-sand-500 mb-2 truncate" title="${comp.address}">${comp.address || locationText}</p>

            <div class="flex items-center gap-2 mb-3 text-xs">
              <span class="text-amber-500 font-bold flex items-center gap-1">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="#D4A373" stroke="#B8824C" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                <span>${comp.rating || '4.6'}</span>
              </span>
              <span class="text-[11px] text-sand-500">(${comp.review_count || '120'} reviews)</span>
            </div>

            ${strengths.length > 0 ? `
              <div class="flex flex-wrap gap-1 mb-3">
                ${strengths.map(s => `<span class="text-[10px] bg-sand-50 text-sand-600 px-2 py-0.5 rounded border border-[#E8E2D8]">${s}</span>`).join('')}
              </div>
            ` : ''}

            ${ownBusinessBadge}
            ${trackedDetails}
            ${isTracked ? `
              <div class="text-[10px] text-sage-600 mt-1 flex items-center gap-1">
                <svg width="10" height="10" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                Already tracked in this project
              </div>
            ` : ''}
          </div>

          <div class="pt-3 border-t border-[#E8E2D8] flex items-center justify-between gap-2 mt-2">
            ${comp.google_maps_url ? `
              <a href="${comp.google_maps_url}" target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-sage-600 hover:text-sage-700 flex items-center gap-1">
                <span>View Maps</span>
                <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg>
              </a>
            ` : '<span></span>'}

            <button type="button" class="track-single-btn px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              isTracked || isOwnBusiness
                ? 'bg-sage-100 text-sage-700 cursor-default'
                : 'bg-terracotta-500 hover:bg-terracotta-600 text-white shadow-xs'
            }" data-index="${idx}" ${isTracked || isOwnBusiness ? 'disabled' : ''}>
              ${isTracked ? 'In Project' : isOwnBusiness ? 'Your Business' : '+ Track Competitor'}
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Attach listener to each "+ Track Competitor" button
    discoveryCardsGrid.querySelectorAll('.track-single-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const button = e.currentTarget;
        const index = parseInt(button.dataset.index);
        const comp = data.competitors[index];
        if (!comp || comp.already_tracked || comp.is_own_business) return;

        try {
          button.disabled = true;
          button.textContent = 'Adding...';

          await api.addCompetitor(activeProjectId(), {
            name: comp.name,
            gmap_url: comp.google_maps_url || null,
            address: comp.address || null,
            category: comp.category || null,
            place_key: comp.place_key || null,
            google_place_id: comp.google_place_id || null,
            cid: comp.cid || null,
            hex_id: comp.hex_id || null,
          });

          comp.already_tracked = true;
          button.className = 'track-single-btn px-3 py-1.5 rounded-lg text-xs font-semibold bg-sage-100 text-sage-700 cursor-default';
          button.textContent = 'Tracked';

          window.showToast?.(`"${comp.name}" added to project competitors!`, 'success');
          await loadCompetitors(); // Reload table below
          document.dispatchEvent(new CustomEvent('competitor-updated', {
            detail: { projectId: activeProjectId() }
          }));
        } catch (err) {
          button.disabled = false;
          button.textContent = '+ Track Competitor';
          window.showToast?.(`Failed to add competitor: ${err.message}`, 'error');
        }
      });
    });
  }

  // Track All Discovered Competitors
  async function trackAllDiscovered() {
    if (!lastDiscoveredCompetitors || lastDiscoveredCompetitors.length === 0) return;

    const untracked = lastDiscoveredCompetitors.filter(c => !c.already_tracked);
    if (untracked.length === 0) {
      window.showToast?.('All discovered competitors are already tracked in this project!', 'info');
      return;
    }

    try {
      trackAllBtn.disabled = true;
      trackAllBtn.textContent = `Adding ${untracked.length}...`;

      let addedCount = 0;
      for (const comp of untracked) {
        try {
          await api.addCompetitor(activeProjectId(), {
            name: comp.name,
            gmap_url: comp.google_maps_url || null,
            address: comp.address || null,
            category: comp.category || null,
            place_key: comp.place_key || null,
            google_place_id: comp.google_place_id || null,
            cid: comp.cid || null,
            hex_id: comp.hex_id || null,
          });
          comp.already_tracked = true;
          addedCount++;
        } catch (e) {
          console.error(`Failed to add ${comp.name}:`, e);
        }
      }

      window.showToast?.(`Added ${addedCount} competitors to project!`, 'success');
      await loadCompetitors();
      document.dispatchEvent(new CustomEvent('competitor-updated', {
        detail: { projectId: activeProjectId() }
      }));

      // Refresh card button states
      renderDiscoveryResults({
        inferred_location: discoveryLocationEl.value || (isOnlineScope ? 'Pan-India / Online' : 'Local Area'),
        inferred_field: discoveryFieldEl.value || 'Industry Competitors',
        competitors: lastDiscoveredCompetitors
      });
    } catch (err) {
      window.showToast?.(`Error adding competitors: ${err.message}`, 'error');
    } finally {
      trackAllBtn.disabled = false;
      trackAllBtn.innerHTML = `
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M12 5v14m-7-7h14"/></svg>
        Track All Discovered
      `;
    }
  }

  // Setup Event Listeners
  function setupEventListeners() {
    // Project Select Change
    if (projectSelectEl) {
      projectSelectEl.addEventListener('change', async (e) => {
        currentProjectId = parseInt(e.target.value);
        const mobileSelect = document.getElementById('mobile-project-select');
        if (mobileSelect) mobileSelect.value = e.target.value;
        await loadCompetitors();
        await loadKeywords();
        // Pre-fill discovery form with project context
        await prefillDiscoveryFromProject(currentProjectId);
      });
    }

    const mobileProjectSelectEl = document.getElementById('mobile-project-select');
    if (mobileProjectSelectEl) {
      mobileProjectSelectEl.addEventListener('change', async (e) => {
        currentProjectId = parseInt(e.target.value);
        if (projectSelectEl) projectSelectEl.value = e.target.value;
        await loadCompetitors();
        await loadKeywords();
        await prefillDiscoveryFromProject(currentProjectId);
      });
    }

    // Table Search Filter
    if (competitorSearchEl) {
      competitorSearchEl.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        if (!query) {
          renderCompetitorsTable(currentProjectCompetitors);
          return;
        }
        const filtered = currentProjectCompetitors.filter(c =>
          c.name.toLowerCase().includes(query) || (c.gmap_url && c.gmap_url.toLowerCase().includes(query))
        );
        renderCompetitorsTable(filtered);
      });
    }

    // Scope Toggle
    if (scopeLocalBtn && scopeOnlineBtn) {
      scopeLocalBtn.addEventListener('click', () => {
        isOnlineScope = false;
        scopeLocalBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-white text-sand-900 shadow-xs transition-all';
        scopeOnlineBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-medium text-sand-600 hover:text-sand-900 transition-all';
        if (discoveryLocationLabel) discoveryLocationLabel.textContent = 'Geographic Location';
        if (discoveryLocationEl) {
          discoveryLocationEl.placeholder = 'e.g. Kharghar, Navi Mumbai';
          if (discoveryLocationEl.value === 'Pan-India / Online') discoveryLocationEl.value = '';
        }
      });

      scopeOnlineBtn.addEventListener('click', () => {
        isOnlineScope = true;
        scopeOnlineBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-semibold bg-white text-sand-900 shadow-xs transition-all';
        scopeLocalBtn.className = 'px-3 py-1.5 rounded-lg text-xs font-medium text-sand-600 hover:text-sand-900 transition-all';
        if (discoveryLocationLabel) discoveryLocationLabel.textContent = 'Operating Scope';
        if (discoveryLocationEl) {
          discoveryLocationEl.placeholder = 'Pan-India / Nationwide / Online';
          if (!discoveryLocationEl.value) discoveryLocationEl.value = 'Pan-India / Online';
        }
      });
    }

    // Discovery Form Submit
    if (discoveryForm) {
      discoveryForm.addEventListener('submit', handleDiscovery);
    }

    // Track All Button
    if (trackAllBtn) {
      trackAllBtn.addEventListener('click', trackAllDiscovered);
    }

    // Add Target Keyword Form Submit
    if (addKeywordForm) {
      addKeywordForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const kw = newKeywordInput.value.trim();
        if (!kw) return;

        try {
          await api.addKeyword(activeProjectId(), { keyword: kw });
          newKeywordInput.value = '';
          window.showToast?.(`Keyword "#${kw}" added to project`, 'success');
          await loadKeywords();
        } catch (err) {
          window.showToast?.(`Error adding keyword: ${err.message}`, 'error');
        }
      });
    }

    // Modal Events for Manual Add
    const resetModalToAddMode = () => {
      editingCompetitorId = null;
      selectedSearchResult = null;
      selectedSearchResultIndex = null;
      lastSearchResults = [];
      const titleEl = addCompetitorModal?.querySelector('h3');
      if (titleEl) titleEl.textContent = 'Add New Competitor';
      // Clear all displays
      if (searchResultsDisplay) searchResultsDisplay.classList.add('hidden');
      if (searchResultsList) searchResultsList.innerHTML = '';
      if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.add('hidden');
      if (resolvedPlaceDetails) resolvedPlaceDetails.innerHTML = '';
      if (resolvedPlaceKey) resolvedPlaceKey.value = '';
      if (resolvedGooglePlaceId) resolvedGooglePlaceId.value = '';
      if (resolvedCid) resolvedCid.value = '';
      if (resolvedHexId) resolvedHexId.value = '';
      if (saveCompetitorBtn) saveCompetitorBtn.disabled = true;
    };

    if (addCompetitorBtn && addCompetitorModal) {
      addCompetitorBtn.addEventListener('click', () => {
        resetModalToAddMode();
        addCompetitorModal.classList.remove('hidden');
        if (modalCompetitorName) modalCompetitorName.focus();
      });
    }

    // The dashboard's Quick Add opens this same modal — make sure it is in
    // "add" mode even if the user previously opened the Edit dialog.
    const dashQuickAddBtn = document.getElementById('dash-quick-add-btn');
    dashQuickAddBtn?.addEventListener('click', resetModalToAddMode);

    // Search button - searches Google Maps near project location for business name
    if (searchPlaceBtn) {
      searchPlaceBtn.addEventListener('click', async () => {
        const name = modalCompetitorName?.value?.trim();
        if (!name) {
          window.showToast?.('Enter a business name first', 'warning');
          return;
        }

        // Hide resolved display when searching
        if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.add('hidden');
        if (resolvedPlaceKey) resolvedPlaceKey.value = '';
        if (resolvedGooglePlaceId) resolvedGooglePlaceId.value = '';
        if (resolvedCid) resolvedCid.value = '';
        if (resolvedHexId) resolvedHexId.value = '';

        searchPlaceBtn.disabled = true;
        searchPlaceBtn.textContent = 'Searching...';

        try {
          const projectId = activeProjectId();
          const project = await api.getProject(projectId);
          const location = project?.project?.location || project?.project?.our_profile || '';

          if (!location) {
            window.showToast?.('Project location not set. Please set a location in project settings.', 'warning');
            return;
          }

          const result = await api.searchPlaces(name, location, 5);

          if (result.results && result.results.length > 0) {
            // Store search results for later verification
            lastSearchResults = result.results;
            // Show search results
            selectedSearchResult = null;
            selectedSearchResultIndex = null;
            renderSearchResults(result.results);
            if (searchResultsDisplay) searchResultsDisplay.classList.remove('hidden');
            window.showToast?.(`Found ${result.results.length} matching businesses`, 'success');
          } else {
            lastSearchResults = [];
            window.showToast?.('No matching businesses found on Google Maps near this location', 'warning');
          }
        } catch (err) {
          console.error('Error searching places:', err);
          window.showToast?.(`Search error: ${err.message}`, 'error');
        } finally {
          searchPlaceBtn.disabled = false;
          searchPlaceBtn.textContent = 'Search';
        }
      });
    }

    // Clear search results
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        selectedSearchResult = null;
        selectedSearchResultIndex = null;
        lastSearchResults = [];
        if (searchResultsDisplay) searchResultsDisplay.classList.add('hidden');
        if (searchResultsList) searchResultsList.innerHTML = '';
      });
    }

    // Typing in the name / URL fields invalidates the previously selected
    // search result so Resolve and Save use exactly what the user typed.
    const clearSelectedSearchResult = () => {
      if (!selectedSearchResult && selectedSearchResultIndex === null) return;
      selectedSearchResult = null;
      selectedSearchResultIndex = null;
      renderSearchResults(lastSearchResults || []);
    };
    modalCompetitorName?.addEventListener('input', clearSelectedSearchResult);
    modalCompetitorUrl?.addEventListener('input', clearSelectedSearchResult);

    // Resolve Place button - calls backend to resolve typed name/URL to canonical identity
    if (resolvePlaceBtn) {
      resolvePlaceBtn.addEventListener('click', async () => {
        const name = modalCompetitorName?.value?.trim();
        const url = modalCompetitorUrl?.value?.trim();
        if (!name && !url) {
          window.showToast?.('Enter a business name or Google Maps URL first', 'warning');
          return;
        }

        // If we have a selected search result, use that
        const useResult = selectedSearchResult;

        resolvePlaceBtn.disabled = true;
        resolvePlaceBtn.textContent = 'Resolving...';

        try {
          const projectId = activeProjectId();
          const project = await api.getProject(projectId);
          const location = project?.project?.location || project?.project?.our_profile || '';

          // If we have a selected search result with a URL, use that for resolution
          const gmapUrl = useResult ? useResult.google_maps_url : (url || undefined);
          const resultName = useResult ? useResult.name : (name || '');

          const result = await api.resolvePlace(resultName, location, {
            live: true,
            gmap_url: gmapUrl,
          });

          if (result.found && result.identity) {
            const identity = result.identity;
            // Populate hidden fields
            if (resolvedPlaceKey) resolvedPlaceKey.value = identity.place_key || '';
            if (resolvedGooglePlaceId) resolvedGooglePlaceId.value = identity.google_place_id || '';
            if (resolvedCid) resolvedCid.value = identity.cid || '';
            if (resolvedHexId) resolvedHexId.value = identity.hex_id || '';

            // Show resolved details
            let detailsHtml = '';
            if (identity.name) detailsHtml += `<div><strong>Name:</strong> ${identity.name}</div>`;
            if (identity.address) detailsHtml += `<div><strong>Address:</strong> ${identity.address}</div>`;
            if (identity.category) detailsHtml += `<div><strong>Category:</strong> ${identity.category}</div>`;
            if (identity.rating) detailsHtml += `<div><strong>Rating:</strong> ${identity.rating} (${identity.review_count || 0} reviews)</div>`;
            if (identity.google_place_id) detailsHtml += `<div><strong>Place ID:</strong> <code class="bg-white px-1 rounded">${identity.google_place_id}</code></div>`;
            if (identity.hex_id) detailsHtml += `<div><strong>Hex Pair:</strong> <code class="bg-white px-1 rounded">${identity.hex_id}</code></div>`;
            if (identity.cid) detailsHtml += `<div><strong>CID:</strong> <code class="bg-white px-1 rounded">${identity.cid}</code></div>`;
            if (identity.identity_source) {
              const sourceLabel = identity.identity_source === 'name' ? 'Name only (weak)' : identity.identity_source;
              detailsHtml += `<div><strong>Source:</strong> ${sourceLabel} (confidence: ${identity.confidence})</div>`;
            }
            if (identity.is_strong) {
              detailsHtml += `<div class="text-sage-700 font-medium flex items-center gap-1.5"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Strong Google Maps identity confirmed</div>`;
            } else {
              detailsHtml += `<div class="text-amber-700 font-medium flex items-center gap-1.5"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Weak identity - name match only</div>`;
            }

            if (resolvedPlaceDetails) resolvedPlaceDetails.innerHTML = detailsHtml;
            if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.remove('hidden');
            if (saveCompetitorBtn) saveCompetitorBtn.disabled = false;

            // Hide search results
            if (searchResultsDisplay) searchResultsDisplay.classList.add('hidden');

            window.showToast?.('Place resolved to canonical Google Maps identity', 'success');
          } else {
            window.showToast?.(result.message || 'Could not resolve place on Google Maps', 'warning');
            if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.add('hidden');
            if (saveCompetitorBtn) saveCompetitorBtn.disabled = true;
          }
        } catch (err) {
          console.error('Error resolving place:', err);
          window.showToast?.(`Resolution error: ${err.message}`, 'error');
        } finally {
          resolvePlaceBtn.disabled = false;
          resolvePlaceBtn.textContent = 'Resolve';
        }
      });
    }

    // Render search results
    function renderSearchResults(results) {
      if (!searchResultsList) return;
      
      searchResultsList.innerHTML = results.map((result, index) => {
        const identitySource = result.identity_source || 'unknown';
        const isStrong = ['place_id', 'hex_id', 'cid', 'kgmid'].includes(identitySource);
        
        return `
          <div class="search-result-item p-3 bg-white border border-sage-200 rounded-lg cursor-pointer hover:bg-sage-50 transition-colors ${selectedSearchResultIndex === index ? 'border-sage-500 bg-sage-50' : ''}" data-index="${index}">
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-1">
                  <p class="text-xs font-bold text-sand-900 truncate">${result.name}</p>
                  ${isStrong ? `
                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-sage-100 text-sage-700">
                      <svg width="8" height="8" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                      Verified
                    </span>
                  ` : `
                    <span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-semibold bg-amber-100 text-amber-700">
                      Candidate
                    </span>
                  `}
                </div>
                <p class="text-[11px] text-sand-500 truncate">${result.address || 'Address not available'}</p>
                <div class="flex items-center gap-2 mt-1 text-[10px] text-sand-500">
                  ${result.category ? `<span>${result.category}</span>` : ''}
                  ${result.rating ? `<span class="text-amber-600 font-semibold flex items-center gap-0.5"><svg width="9" height="9" viewBox="0 0 24 24" fill="#D4A373" stroke="#B8824C" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg> ${result.rating}</span>` : ''}
                  ${result.review_count ? `<span>(${result.review_count} reviews)</span>` : ''}
                </div>
              </div>
              <button type="button" class="select-result-btn px-2 py-1 bg-terracotta-500 hover:bg-terracotta-600 text-white text-[10px] font-semibold rounded transition-colors">
                Select
              </button>
            </div>
          </div>
        `;
      }).join('');

      // Add click handlers
      searchResultsList.querySelectorAll('.search-result-item').forEach(item => {
        item.addEventListener('click', (e) => {
          // Don't trigger if clicking the select button
          if (e.target.closest('.select-result-btn')) return;
          
          const index = parseInt(item.dataset.index);
          selectSearchResult(index, results);
        });
        
        item.querySelector('.select-result-btn')?.addEventListener('click', (e) => {
          e.stopPropagation();
          const index = parseInt(item.dataset.index);
          selectSearchResult(index, results);
        });
      });
    }

    function selectSearchResult(index, results) {
      const result = results[index];
      // Store the result object itself so Resolve / Add use its real
      // name + Google Maps URL (storing the bare index broke both for any
      // entry other than the first one, and index 0 was falsy).
      selectedSearchResult = result || null;
      selectedSearchResultIndex = Number.isInteger(index) ? index : null;

      // Update UI
      searchResultsList.querySelectorAll('.search-result-item').forEach((item, i) => {
        if (i === index) {
          item.classList.add('border-sage-500', 'bg-sage-50');
          item.classList.remove('border-sage-200');
        } else {
          item.classList.remove('border-sage-500', 'bg-sage-50');
          item.classList.add('border-sage-200');
        }
      });
      
      // Pre-fill the name and URL with selected result
      if (result) {
        if (modalCompetitorName) modalCompetitorName.value = result.name || '';
        if (modalCompetitorUrl) modalCompetitorUrl.value = result.google_maps_url || '';
        window.showToast?.(`Selected: ${result.name}`, 'info');
      }
    }

    // Show verification modal before adding custom competitor
    function showVerificationModal(verification) {
      return new Promise((resolve) => {
        // Create verification modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 modal-backdrop flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
          <div class="bg-white border border-[#E8E2D8] rounded-2xl max-w-lg w-full p-6 shadow-xl animate-fade-in max-h-[80vh] overflow-y-auto">
            <div class="flex items-center justify-between pb-3 border-b border-[#E8E2D8] mb-4">
              <h3 class="text-lg font-bold font-serif text-sand-900">Google Maps Verification</h3>
              <button id="close-verification-modal" class="text-sand-400 hover:text-sand-700 text-lg leading-none">&times;</button>
            </div>
            <div class="space-y-4">
              <div class="p-3 bg-sage-50 border border-sage-200 rounded-xl">
                <div class="flex items-center gap-2 text-xs font-semibold text-sage-700 mb-2">
                  <svg width="12" height="12" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                  <span>Verified Business</span>
                </div>
                <div class="text-[11px] text-sand-600 space-y-1" id="verification-details"></div>
              </div>
              
              ${verification.already_tracked ? `
                <div class="p-3 bg-amber-50 border border-amber-200 rounded-xl">
                  <div class="flex items-center gap-2 text-xs font-semibold text-amber-700">
                    <svg width="12" height="12" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                    <span>Already tracked in this project: ${verification.existing_competitor?.name}</span>
                  </div>
                </div>
              ` : ''}
              
              ${!verification.verified ? `
                <div class="p-3 bg-red-50 border border-red-200 rounded-xl">
                  <div class="flex items-center gap-2 text-xs font-semibold text-red-700">
                    <svg width="12" height="12" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/></svg>
                    <span>Could not verify this business on Google Maps</span>
                  </div>
                  <p class="text-[11px] text-red-600 mt-1">This business does not have a verified Google Maps listing.</p>
                </div>
              ` : ''}
              
              <div class="p-3 bg-sand-50 border border-[#E8E2D8] rounded-xl">
                <div class="text-xs font-semibold text-sand-700 mb-1">Competitor Relevance</div>
                <div class="flex items-center gap-2 text-xs text-sand-600">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                    verification.relevance === 'Relevant' ? 'bg-sage-100 text-sage-700' :
                    verification.relevance === 'Possibly Relevant' ? 'bg-amber-100 text-amber-700' :
                    verification.relevance === 'Not Relevant' ? 'bg-red-100 text-red-700' :
                    'bg-sand-100 text-sand-700'
                  }">${verification.relevance || 'Unknown'}</span>
                </div>
                ${verification.relevance_details?.length ? `
                  <div class="text-[10px] text-sand-500 mt-1 space-y-0.5">
                    ${verification.relevance_details.map(d => `<div>${d}</div>`).join('')}
                  </div>
                ` : ''}
              </div>
              
              <div class="flex justify-end gap-2.5 pt-3">
                ${!verification.already_tracked && verification.verified ? `
                  <button id="confirm-add-competitor" class="px-4 py-2 bg-sage-500 hover:bg-sage-600 text-white text-xs font-semibold rounded-xl shadow-sm">
                    Add to Project
                  </button>
                ` : ''}
                <button id="cancel-verification" class="px-4 py-2 bg-sand-100 hover:bg-sand-200 text-sand-800 text-xs font-semibold rounded-xl">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        `;
        
        document.body.appendChild(modal);
        
        // Populate verification details from display object (full search result details)
        const detailsEl = modal.querySelector('#verification-details');
        if (detailsEl) {
          const display = verification.display || {};
          const id = verification.identity || {};
          let html = '';
          if (display.name) html += `<div><strong>Business:</strong> ${display.name}</div>`;
          if (display.address) html += `<div><strong>Address:</strong> ${display.address}</div>`;
          if (display.category) html += `<div><strong>Category:</strong> ${display.category}</div>`;
          if (display.status) html += `<div><strong>Status:</strong> ${display.status}</div>`;
          if (display.opening_hours) html += `<div><strong>Closes:</strong> ${display.opening_hours}</div>`;
          if (display.rating) html += `<div><strong>Rating:</strong> ${display.rating} (${display.review_count || 0} reviews)</div>`;
          if (display.distance_km !== null && display.distance_km !== undefined) html += `<div><strong>Distance from project:</strong> ${display.distance_km.toFixed(1)} km</div>`;
          if (display.google_maps_url) html += `<div><strong>Google Maps:</strong> <a href="${display.google_maps_url}" target="_blank" class="text-sage-600 hover:underline text-[11px]">${display.google_maps_url}</a></div>`;
          if (display.place_id) html += `<div><strong>Place ID:</strong> <code class="bg-white px-1 rounded">${display.place_id}</code></div>`;
          // Identity source info
          if (id.identity_source) {
            const sourceLabel = id.identity_source === 'name' ? 'Name only (weak)' : id.identity_source;
            html += `<div><strong>Source:</strong> ${sourceLabel} (confidence: ${id.confidence})</div>`;
          }
          if (id.is_strong) {
            html += `<div class="text-sage-700 font-medium flex items-center gap-1.5"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Strong Google Maps identity confirmed</div>`;
          } else {
            html += `<div class="text-amber-700 font-medium flex items-center gap-1.5"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Weak identity - name match only</div>`;
          }
          detailsEl.innerHTML = html;
        }
        
        const closeModal = () => {
          modal.remove();
          resolve(false);
        };
        
        modal.querySelector('#close-verification-modal')?.addEventListener('click', closeModal);
        modal.querySelector('#cancel-verification')?.addEventListener('click', closeModal);
        
        const confirmBtn = modal.querySelector('#confirm-add-competitor');
        if (confirmBtn) {
          confirmBtn.addEventListener('click', () => {
            modal.remove();
            resolve(true);
          });
        }
        
        // Close on backdrop click
        modal.addEventListener('click', (e) => {
          if (e.target === modal) closeModal();
        });
      });
    }

    const closeModal = () => {
      if (addCompetitorModal) addCompetitorModal.classList.add('hidden');
      if (addCompetitorForm) addCompetitorForm.reset();
      editingCompetitorId = null;
      selectedSearchResult = null;
      selectedSearchResultIndex = null;
      const titleEl = addCompetitorModal?.querySelector('h3');
      if (titleEl) titleEl.textContent = 'Add New Competitor';
      // Clear all displays
      if (searchResultsDisplay) searchResultsDisplay.classList.add('hidden');
      if (searchResultsList) searchResultsList.innerHTML = '';
      if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.add('hidden');
      if (resolvedPlaceDetails) resolvedPlaceDetails.innerHTML = '';
      if (resolvedPlaceKey) resolvedPlaceKey.value = '';
      if (resolvedGooglePlaceId) resolvedGooglePlaceId.value = '';
      if (resolvedCid) resolvedCid.value = '';
      if (resolvedHexId) resolvedHexId.value = '';
      if (saveCompetitorBtn) saveCompetitorBtn.disabled = true;
    };

    if (closeCompetitorModalBtn) closeCompetitorModalBtn.addEventListener('click', closeModal);
    if (cancelCompetitorModalBtn) cancelCompetitorModalBtn.addEventListener('click', closeModal);

    if (addCompetitorForm) {
      addCompetitorForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = modalCompetitorName.value.trim();
        const url = modalCompetitorUrl.value.trim() || null;
        if (!name) return;

        try {
          const projectId = activeProjectId();
          
          // First verify the competitor - include the selected search result
          // (object) so the backend receives the full Google Maps details.
          const searchResult = selectedSearchResult;
          const verification = await api.verifyCompetitor({
            name,
            gmap_url: url,
            project_id: projectId,
            search_result: searchResult
          });
          
          // Show verification result
          const confirmed = await showVerificationModal(verification);
          if (!confirmed) return;
          
          const competitorData = {
            name,
            gmap_url: url,
            // Include resolved identity fields if available
            place_key: resolvedPlaceKey?.value || verification.identity?.place_key || null,
            google_place_id: resolvedGooglePlaceId?.value || verification.identity?.google_place_id || null,
            cid: resolvedCid?.value || verification.identity?.cid || null,
            hex_id: resolvedHexId?.value || verification.identity?.hex_id || null,
          };
          
          if (editingCompetitorId) {
            await api.updateCompetitor(editingCompetitorId, competitorData);
            closeModal();
            window.showToast?.(`Competitor "${name}" updated!`, 'success');
          } else {
            await api.addCompetitor(projectId, competitorData);
            closeModal();
            window.showToast?.(`Competitor "${name}" added!`, 'success');
          }
          await loadCompetitors();
          // Notify the dashboard (which shares this modal) to refresh its counters
          document.dispatchEvent(new CustomEvent('competitor-added', {
            detail: { projectId, name }
          }));
        } catch (err) {
          window.showToast?.(`Error saving competitor: ${err.message}`, 'error');
        }
      });
    }
  }

  // Add Action Listeners for Table Rows
  function addActionListeners() {
    // Scrape button — re-scrape only this competitor
    document.querySelectorAll('#competitors-table-body button[title="Scrape"]').forEach(button => {
      button.addEventListener('click', async (e) => {
        const competitorId = e.target.closest('button').dataset.id;
        if (!competitorId) return;

        try {
          api.showLoading();
          const result = await api.scrapeCompetitor(competitorId);
          const summary = result.results || {};
          const warning = result.warning ? ` (${result.warning})` : '';
          if (result.scrape_status === 'NO_POSTS' || (summary.posts_found === 0 && !result.warning && !result.error)) {
            window.showToast?.(`No updates published by competitor in the last 6 months`, 'info');
          } else {
            window.showToast?.(
              `Scraping finished: ${summary.new_posts || 0} new updates, ${summary.duplicates_skipped || 0} duplicates skipped${warning}`,
              result.warning ? 'warning' : 'success'
            );
          }
          await loadCompetitors();
          document.dispatchEvent(new CustomEvent('competitor-updated', {
            detail: { projectId: activeProjectId() }
          }));
        } catch (error) {
          window.showToast?.(`Scraping error: ${error.message}`, 'error');
        } finally {
          api.hideLoading();
        }
      });
    });

    // Edit button — open the shared modal in edit mode
    document.querySelectorAll('#competitors-table-body button[title="Edit"]').forEach(button => {
      button.addEventListener('click', (e) => {
        const competitorId = parseInt(e.target.closest('button').dataset.id, 10);
        const competitor = currentProjectCompetitors.find(c => c.id === competitorId);
        if (!competitor || !addCompetitorModal) return;

        editingCompetitorId = competitor.id;
        const titleEl = addCompetitorModal.querySelector('h3');
        if (titleEl) titleEl.textContent = 'Edit Competitor';
        if (modalCompetitorName) modalCompetitorName.value = competitor.name || '';
        if (modalCompetitorUrl) modalCompetitorUrl.value = competitor.gmap_url || '';

        // Populate resolved identity fields if available
        if (competitor.place) {
          if (resolvedPlaceKey) resolvedPlaceKey.value = competitor.place.place_key || '';
          if (resolvedGooglePlaceId) resolvedGooglePlaceId.value = competitor.place.google_place_id || '';
          if (resolvedCid) resolvedCid.value = competitor.place.cid || '';
          if (resolvedHexId) resolvedHexId.value = competitor.place.hex_id || '';

          // Show resolved details
          const place = competitor.place;
          let detailsHtml = '';
          if (place.name) detailsHtml += `<div><strong>Name:</strong> ${place.name}</div>`;
          if (place.address) detailsHtml += `<div><strong>Address:</strong> ${place.address}</div>`;
          if (place.google_place_id) detailsHtml += `<div><strong>Place ID:</strong> <code class="bg-white px-1 rounded">${place.google_place_id}</code></div>`;
          if (place.hex_id) detailsHtml += `<div><strong>Hex Pair:</strong> <code class="bg-white px-1 rounded">${place.hex_id}</code></div>`;
          if (place.cid) detailsHtml += `<div><strong>CID:</strong> <code class="bg-white px-1 rounded">${place.cid}</code></div>`;
          if (place.identity_source) detailsHtml += `<div><strong>Source:</strong> ${place.identity_source} (confidence: ${place.confidence})</div>`;
          if (place.confidence >= 2) {
            detailsHtml += `<div class="text-sage-700 font-medium flex items-center gap-1.5"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Strong Google Maps identity confirmed</div>`;
          } else {
            detailsHtml += `<div class="text-amber-700 font-medium flex items-center gap-1.5"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Weak identity - manual entry only</div>`;
          }

          if (resolvedPlaceDetails) resolvedPlaceDetails.innerHTML = detailsHtml;
          if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.remove('hidden');
        } else {
          // Clear resolved place display
          if (resolvedPlaceDisplay) resolvedPlaceDisplay.classList.add('hidden');
          if (resolvedPlaceDetails) resolvedPlaceDetails.innerHTML = '';
          if (resolvedPlaceKey) resolvedPlaceKey.value = '';
          if (resolvedGooglePlaceId) resolvedGooglePlaceId.value = '';
          if (resolvedCid) resolvedCid.value = '';
          if (resolvedHexId) resolvedHexId.value = '';
        }

        addCompetitorModal.classList.remove('hidden');
        modalCompetitorName?.focus();
      });
    });

    // View posts button — jump to Posts pre-filtered to this competitor
    document.querySelectorAll('#competitors-table-body button[title="View Posts"]').forEach(button => {
      button.addEventListener('click', (e) => {
        const competitorId = e.target.closest('button').dataset.id;
        const postsTab = document.getElementById('posts-tab');
        if (postsTab) postsTab.click();
        const compFilter = document.getElementById('competitor-filter');
        if (compFilter && competitorId) {
          compFilter.value = competitorId;
          compFilter.dispatchEvent(new Event('change'));
        }
      });
    });

    // Delete competitor button
    document.querySelectorAll('#competitors-table-body button[title="Delete"]').forEach(button => {
      button.addEventListener('click', async (e) => {
        const competitorId = e.target.closest('button').dataset.id;
        if (!confirm('Are you sure you want to remove this competitor from the project?')) return;

        try {
          await api.deleteCompetitor(competitorId);
          window.showToast?.('Competitor deleted', 'success');
          await loadCompetitors();
          document.dispatchEvent(new CustomEvent('competitor-updated', {
            detail: { projectId: activeProjectId() }
          }));
        } catch (error) {
          window.showToast?.(`Delete error: ${error.message}`, 'error');
        }
      });
    });
  }

  function showErrorState(message) {
    if (!competitorsTableBody) return;
    competitorsTableBody.innerHTML = `
      <tr>
        <td colspan="4" class="px-6 py-4 text-center text-xs text-red-500">
          Error loading competitors: ${message}
        </td>
      </tr>
    `;
  }

  function formatDate(dateString) {
    try {
      const options = { year: 'numeric', month: 'short', day: 'numeric' };
      return new Date(dateString).toLocaleDateString(undefined, options);
    } catch {
      return dateString;
    }
  }

  // Pre-fill discovery form with project context
  async function prefillDiscoveryFromProject(projectId) {
    try {
      const project = await api.getProject(projectId);
      if (project?.project) {
        const p = project.project;
        if (discoveryCompanyEl) discoveryCompanyEl.value = p.name || '';
        if (discoveryLocationEl) discoveryLocationEl.value = p.location || p.our_profile || '';
        if (discoveryFieldEl) discoveryFieldEl.value = p.field || '';
      }
    } catch (err) {
      console.error('Error pre-filling discovery:', err);
    }
  }

  // Execute initialization
  init();
}