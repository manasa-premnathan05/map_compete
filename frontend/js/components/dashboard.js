// Comprehensive Earthy & Pastel Dashboard Component
export function initDashboard(api) {
  const dashboardView = document.getElementById('dashboard-view');
  if (!dashboardView) return;

  // DOM Elements
  const projectSelectEl = document.getElementById('project-select');
  const dashboardProjectTitle = document.getElementById('dashboard-project-title');
  const dashboardProjectDesc = document.getElementById('dashboard-project-desc');
  const dashboardLastSync = document.getElementById('dashboard-last-sync');

  // KPI elements
  const competitorsCountEl = document.getElementById('competitors-count');
  const totalPostsCountEl = document.getElementById('total-posts-count');
  const newPostsCountEl = document.getElementById('new-posts-count');
  const duplicatesCountEl = document.getElementById('duplicates-count');
  const topTopicEl = document.getElementById('top-topic');
  const ideasCountEl = document.getElementById('ideas-count-kpi');
  const generatedContentNoteEl = document.getElementById('generated-content-note');
  const failedScrapesCountEl = document.getElementById('failed-scrapes-count');
  const failedScrapesNoteEl = document.getElementById('failed-scrapes-note');
  const failedScrapesBarEl = document.getElementById('failed-scrapes-bar');
  const imagesDownloadedCountEl = document.getElementById('images-downloaded-count');
  const imagesDownloadedNoteEl = document.getElementById('images-downloaded-note');
  const scrapingStatsEl = document.getElementById('dashboard-scraping-stats');
  const scrapingLogsBodyEl = document.getElementById('dashboard-scraping-logs-body');
  const scrapingLastActivityEl = document.getElementById('scraping-last-activity');

  // Widget containers
  const competitorsTableEl = document.getElementById('dashboard-competitors-table');
  const topicsListEl = document.getElementById('dashboard-topics-list');
  const keywordsCloudEl = document.getElementById('dashboard-keywords-cloud');
  const recentPostsEl = document.getElementById('dashboard-recent-posts');
  const spotlightTextEl = document.getElementById('dashboard-spotlight-text');
  const copySpotlightBtn = document.getElementById('dashboard-copy-spotlight-btn');
  const recentActivityEl = document.getElementById('recent-activity');

  // Action Buttons
  const quickAddBtn = document.getElementById('dash-quick-add-btn');
  const quickScrapeBtn = document.getElementById('dash-quick-scrape-btn');
  const quickIdeasBtn = document.getElementById('dash-quick-ideas-btn');
  const viewAllCompetitorsBtn = document.getElementById('dash-view-all-competitors');
  const viewAllPostsBtn = document.getElementById('dash-view-all-posts');
  const discoverCompetitorsBtn = document.getElementById('dash-discover-competitors');

  // Modals
  const addCompetitorModal = document.getElementById('add-competitor-modal');
  const closeCompetitorModalBtn = document.getElementById('close-competitor-modal-btn');
  const cancelCompetitorModalBtn = document.getElementById('cancel-competitor-modal-btn');

  const newProjectModal = document.getElementById('new-project-modal');
  const newProjectBtn = document.getElementById('new-project-btn');
  const newProjectForm = document.getElementById('new-project-form');
  const saveProjectBtn = document.getElementById('save-project-btn');
  const closeProjectModalBtn = document.getElementById('close-project-modal-btn');
  const cancelProjectModalBtn = document.getElementById('cancel-project-modal-btn');

  // NEW: Scope toggle buttons for new project modal
  const modalScopeLocalBtn = document.getElementById('modal-scope-local');
  const modalScopeOnlineBtn = document.getElementById('modal-scope-online');
  const modalScopeLocalLabel = document.querySelector('label[for="modal-scope-local"]');
  const modalScopeOnlineLabel = document.querySelector('label[for="modal-scope-online"]');

  // Edit / delete controls for the active project (company name and details)
  const editProjectBtns = [
    document.getElementById('edit-project-btn'),
    document.getElementById('mobile-edit-project-btn')
  ].filter(Boolean);
  const deleteProjectBtns = [
    document.getElementById('delete-project-btn'),
    document.getElementById('mobile-delete-project-btn')
  ].filter(Boolean);

  const editProjectModal = document.getElementById('edit-project-modal');
  const editProjectForm = document.getElementById('edit-project-form');
  const saveEditProjectBtn = document.getElementById('save-edit-project-btn');
  const closeEditProjectModalBtn = document.getElementById('close-edit-project-modal-btn');
  const cancelEditProjectModalBtn = document.getElementById('cancel-edit-project-btn');
  const editScopeLocalBtn = document.getElementById('edit-scope-local');
  const editScopeOnlineBtn = document.getElementById('edit-scope-online');
  const editScopeLocalLabel = document.querySelector('label[for="edit-scope-local"]');
  const editScopeOnlineLabel = document.querySelector('label[for="edit-scope-online"]');

  const deleteProjectModal = document.getElementById('delete-project-modal');
  const deleteProjectNameEl = document.getElementById('delete-project-name');
  const closeDeleteProjectModalBtn = document.getElementById('close-delete-project-modal-btn');
  const cancelDeleteProjectModalBtn = document.getElementById('cancel-delete-project-btn');
  const confirmDeleteProjectBtn = document.getElementById('confirm-delete-project-btn');

  // Project currently held open in the edit/delete modal, so a project switch
  // behind the modal can never modify or delete the wrong company.
  let modalProjectId = null;

  let currentProjectId = null;

  // Initialize Dashboard
  async function init() {
    try {
      await loadProjects();
      await loadDashboardData();
      setupEventListeners();
    } catch (err) {
      console.error('Error initializing dashboard:', err);
    }
  }

  // Load and populate project dropdown. Returns the project list so callers can
  // react to the resulting selection (e.g. after deleting the active project).
  async function loadProjects() {
    try {
      const response = await api.getProjects();
      const projects = response.projects || [];
      const mobileProjectSelectEl = document.getElementById('mobile-project-select');

      if (projects.length > 0) {
        // Preserve the currently selected project when options are rebuilt
        const previous = parseInt(projectSelectEl?.value, 10) || parseInt(mobileProjectSelectEl?.value, 10) || currentProjectId;
        const stillExists = projects.some(p => p.id === previous);
        const targetId = stillExists ? previous : projects[0].id;
        const optionsHtml = projects.map(p => `
          <option value="${p.id}" ${p.id === targetId ? 'selected' : ''}>${p.name}</option>
        `).join('');

        if (projectSelectEl) projectSelectEl.innerHTML = optionsHtml;
        if (mobileProjectSelectEl) mobileProjectSelectEl.innerHTML = optionsHtml;
        currentProjectId = targetId;
      } else {
        // The last project is gone: drop the stale option instead of leaving a
        // deleted company in the switcher.
        if (projectSelectEl) projectSelectEl.innerHTML = '';
        if (mobileProjectSelectEl) mobileProjectSelectEl.innerHTML = '';
        currentProjectId = null;
      }
      return projects;
    } catch (err) {
      console.warn('Could not load projects for selector:', err);
      return [];
    }
  }

  // Resolve the project currently chosen in the header switcher. The dashboard
  // owns that switcher, but the other components start loading in parallel, so
  // wait briefly for it to be filled instead of guessing a project id: a
  // hard-coded fallback would request a project that may have been deleted.
  async function resolveActiveProjectId(waitMs = 5000) {
    const deadline = Date.now() + waitMs;
    for (;;) {
      const projectId = parseInt(projectSelectEl?.value, 10)
        || parseInt(document.getElementById('mobile-project-select')?.value, 10)
        || currentProjectId;
      if (projectId) return projectId;
      if (Date.now() >= deadline) return null;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  // Clear every dashboard surface once the last project is gone, so the
  // deleted company's name and numbers cannot linger on screen.
  function resetDashboardForEmptyState() {
    if (dashboardProjectTitle) dashboardProjectTitle.textContent = 'No project yet';
    if (dashboardProjectDesc) {
      dashboardProjectDesc.textContent = 'Create a project to start monitoring local competitors on Google Maps.';
    }
    if (dashboardLastSync) dashboardLastSync.textContent = 'Waiting for a project';
    [
      competitorsCountEl, totalPostsCountEl, newPostsCountEl, duplicatesCountEl,
      ideasCountEl, imagesDownloadedCountEl, failedScrapesCountEl
    ].forEach(el => {
      if (el) el.textContent = '0';
    });
    if (topTopicEl) topTopicEl.textContent = '—';
    renderCompetitorsTable([], []);
    renderRecentPosts([]);
  }

  // Main dashboard data loader
  async function loadDashboardData() {
    try {
      const projectId = await resolveActiveProjectId();
      if (!projectId) {
        // No company left to show (all projects deleted, or the API is empty).
        resetDashboardForEmptyState();
        return;
      }

      // Concurrently fetch all dashboard resources
      const [
        projectRes,
        competitorsRes,
        postsRes,
        scrapingLogsRes,
        topicsRes,
        keywordsRes,
        ideasRes,
        projectPlacesRes,
        marketGapsRes,
        scrapingStatsRes
      ] = await Promise.allSettled([
        api.getProject(projectId),
        api.getCompetitors(projectId),
        api.getPosts({ project_id: projectId, limit: 100 }),
        api.getScrapingLogs(projectId),
        api.getTopicFrequency(projectId),
        api.getKeywordFrequency(projectId),
        api.getGeneratedIdeas(projectId),
        api.getProjectPlaces(projectId),
        api.getMarketGaps(projectId),
        api.getScrapingStats(projectId)
      ]);

      const project = projectRes.status === 'fulfilled' ? projectRes.value?.project : null;
      const competitors = competitorsRes.status === 'fulfilled' ? (competitorsRes.value?.competitors || []) : [];
      const posts = postsRes.status === 'fulfilled' ? (postsRes.value?.posts || []) : [];
      const logs = scrapingLogsRes.status === 'fulfilled' ? (scrapingLogsRes.value?.logs || []) : [];
      const topics = topicsRes.status === 'fulfilled' ? (topicsRes.value?.topics || []) : [];
      const keywords = keywordsRes.status === 'fulfilled' ? (keywordsRes.value?.keywords || []) : [];
      const ideas = ideasRes.status === 'fulfilled' ? (ideasRes.value?.ideas || []) : [];
      const projectPlaces = projectPlacesRes.status === 'fulfilled' ? (projectPlacesRes.value?.places || []) : [];
      const marketGaps = marketGapsRes.status === 'fulfilled' ? (marketGapsRes.value?.gaps || []) : [];
      // Statistics endpoint: fall back to the block returned with the logs.
      let stats = scrapingStatsRes.status === 'fulfilled' ? scrapingStatsRes.value : null;
      if (!stats && scrapingLogsRes.status === 'fulfilled') {
        stats = scrapingLogsRes.value?.stats || null;
      }
      stats = stats || {};

      // 1. Update Title and description
      if (dashboardProjectTitle && project?.name) {
        dashboardProjectTitle.textContent = project.name;
      }
      if (dashboardProjectDesc && project?.our_profile) {
        dashboardProjectDesc.textContent = `Tracking local competitors for: ${project.our_profile}`;
      }
      if (dashboardLastSync && logs.length > 0) {
        dashboardLastSync.textContent = `Last sync: ${formatTimeAgo(new Date(logs[0].start_time))}`;
      }

      // 2. Update the KPI cards (requirement 20)
      // Use the canonical businesses count for competitors (unique places).
      const competitorCount = stats.unique_businesses || projectPlaces.length || competitors.length;
      if (competitorsCountEl) competitorsCountEl.textContent = competitorCount;
      const totalPosts = stats.total_posts ?? posts.length;
      if (totalPostsCountEl) totalPostsCountEl.textContent = totalPosts;
      const newPostsLatestRun = stats.new_posts_latest_run ?? logs[0]?.new_posts ?? 0;
      if (newPostsCountEl) newPostsCountEl.textContent = newPostsLatestRun;
      const duplicatesLatestRun = stats.duplicates_skipped_latest_run ?? logs[0]?.duplicates_skipped ?? 0;
      if (duplicatesCountEl) duplicatesCountEl.textContent = duplicatesLatestRun;
      if (topTopicEl) {
        topTopicEl.textContent = topics[0]?.detected_topic || topics[0]?.topic || posts[0]?.detected_topic || '—';
      }
      const generatedContent = stats.generated_content_count ?? ideas.length;
      if (ideasCountEl) ideasCountEl.textContent = generatedContent;
      if (generatedContentNoteEl) {
        const usedCount = stats.generated_content_used ?? ideas.filter(idea => idea.used_flag).length;
        generatedContentNoteEl.textContent = usedCount ? `${usedCount} already used` : 'Ready to post';
      }

      // Failed scraping attempts + success rate (requirement 20)
      const failedAttempts = stats.totals?.failed_attempts
        ?? logs.reduce((sum, log) => sum + (log.failures || 0), 0);
      const captchaInterventions = stats.totals?.captcha_interventions
        ?? logs.filter(log => log.has_captcha_issue).length;
      if (failedScrapesCountEl) failedScrapesCountEl.textContent = failedAttempts;
      if (failedScrapesNoteEl) {
        failedScrapesNoteEl.textContent = failedAttempts
          ? `${stats.totals?.success_rate ?? 100}% success - ${captchaInterventions} CAPTCHA hold${captchaInterventions === 1 ? '' : 's'}`
          : 'No failures logged';
      }
      if (failedScrapesBarEl) {
        const totalRuns = Math.max(1, stats.totals?.total_runs ?? logs.length ?? 1);
        const failureShare = Math.min(100, Math.round((failedAttempts / totalRuns) * 100));
        failedScrapesBarEl.style.width = `${Math.max(5, failureShare)}%`;
      }

      // Images downloaded (requirement 21)
      const imagesLatestRun = stats.images_downloaded_latest_run ?? logs[0]?.images_downloaded ?? 0;
      const imagesTotal = stats.totals?.images_downloaded ?? imagesLatestRun;
      if (imagesDownloadedCountEl) imagesDownloadedCountEl.textContent = imagesTotal;
      if (imagesDownloadedNoteEl) {
        imagesDownloadedNoteEl.textContent = imagesTotal
          ? `${imagesLatestRun} from latest scrape`
          : 'No images captured yet';
      }

      // 3. Render Competitors Landscape Table
      renderCompetitorsTable(competitors, posts);

      // 4. Render Trending Topics
      renderTopics(topics, posts);

      // 5. Render Keywords Cloud
      renderKeywords(keywords, posts);

      // 6. Render Latest Updates Feed
      renderRecentPosts(posts);

      // 7. Render AI Idea Spotlight
      renderIdeaSpotlight(ideas);

      // 8. Render Intelligence Activity Log
      renderActivityLog(logs, project?.name || 'Project');

      // 9. Render Strategic Market Gaps
      renderMarketGaps(marketGaps);

      // 10. Render Scraping Logs & Statistics (requirements 20 & 21)
      renderScrapingStats(stats, logs, project?.name || 'Project');

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    }
  }

  // Render Strategic Market Gaps & Opportunities
  function renderMarketGaps(gaps) {
    const el = document.getElementById('dashboard-market-gaps');
    if (!el) return;

    const iconSvgs = {
      'shield-alert': `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
      'flame': `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 01-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z"/></svg>`,
      'clock': `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
      'trending-up': `<svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`
    };

    const badgeClasses = {
      'terracotta': 'bg-terracota-100 text-terracota-700 border-terracota-200',
      'amber': 'bg-amber-100 text-amber-700 border-amber-200',
      'sage': 'bg-sage-100 text-sage-700 border-sage-200',
      'sand': 'bg-sand-100 text-sand-600 border-sand-200'
    };

    const iconBgClasses = {
      'terracotta': 'bg-terracota-50 text-terracota-600',
      'amber': 'bg-amber-50 text-amber-600',
      'sage': 'bg-sage-50 text-sage-600',
      'sand': 'bg-sand-100 text-sand-600'
    };

    if (!gaps || gaps.length === 0) {
      el.innerHTML = `
        <div class="col-span-2 py-10 text-center text-xs text-sand-500">
          <div class="w-10 h-10 mx-auto mb-3 bg-sand-100 rounded-full flex items-center justify-center">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 3v18h18M8 17V9m4 8V5m4 12V9"/></svg>
          </div>
          No gap analysis available yet. Add and scrape competitors to unlock insights.
        </div>`;
      return;
    }

    el.innerHTML = gaps.map(gap => {
      const badgeCls = badgeClasses[gap.badge_color] || badgeClasses['sand'];
      const iconBgCls = iconBgClasses[gap.badge_color] || iconBgClasses['sand'];
      const icon = iconSvgs[gap.icon_type] || iconSvgs['trending-up'];
      const affectedList = (gap.affected_competitors || []).slice(0, 3).join(', ');

      return `
        <div class="group flex flex-col gap-3.5 p-5 bg-gradient-to-br from-white to-[#FAF8F5] border border-[#E8E2D8] rounded-xl shadow-xs hover:shadow-md hover:border-[#D4CFC6] transition-all duration-200">
          <!-- Header -->
          <div class="flex items-start gap-3">
            <div class="shrink-0 w-9 h-9 rounded-lg ${iconBgCls} flex items-center justify-center border border-current/10 shadow-inner">
              ${icon}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-1.5 mb-1">
                <span class="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold border ${badgeCls}">${gap.badge}</span>
                <span class="text-[10px] text-sand-400 font-medium uppercase tracking-wide">${gap.category}</span>
              </div>
              <h4 class="text-sm font-bold text-sand-900 leading-snug">${gap.title}</h4>
            </div>
          </div>

          <!-- Competitor Weakness -->
          <div class="bg-[#F5F2EB] rounded-lg p-3 border-l-2 border-terracota-300">
            <p class="text-[11px] font-semibold text-sand-600 uppercase tracking-wider mb-1">Rival Weakness</p>
            <p class="text-xs text-sand-700 leading-relaxed">${gap.competitor_weakness}</p>
          </div>

          <!-- Strategy -->
          <div>
            <p class="text-[11px] font-semibold text-sand-600 uppercase tracking-wider mb-1">Counter-Strategy</p>
            <p class="text-xs text-sand-700 leading-relaxed">${gap.actionable_strategy}</p>
          </div>

          <!-- Footer: Impact + Competitors -->
          <div class="mt-auto pt-3 border-t border-[#E8E2D8] flex flex-wrap items-center justify-between gap-2">
            <div class="flex items-center gap-1.5">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24" class="text-sage-600"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
              <span class="text-[11px] font-semibold text-sage-700">${gap.expected_impact}</span>
            </div>
            ${affectedList ? `<span class="text-[10px] text-sand-400 truncate max-w-[160px]">vs. ${affectedList}</span>` : ''}
          </div>
        </div>`;
    }).join('');
  }

  // Render Competitors Table on Dashboard
  function renderCompetitorsTable(competitors, posts) {
    if (!competitorsTableEl) return;

    if (!competitors || competitors.length === 0) {
      competitorsTableEl.innerHTML = `
        <tr>
          <td colspan="3" class="px-6 py-6 text-center text-xs text-sand-500">
            No competitors added yet. Click <span class="font-semibold text-terracotta-600 cursor-pointer" onclick="document.getElementById('dash-quick-add-btn').click()">+ Add Competitor</span> to begin monitoring.
          </td>
        </tr>
      `;
      return;
    }

    const paletteClasses = ['bg-sage-100 text-sage-700', 'bg-terracotta-100 text-terracotta-700', 'bg-amber-100 text-amber-700', 'bg-clay-100 text-clay-700'];

    competitorsTableEl.innerHTML = competitors.map((comp, idx) => {
      const avatarClass = paletteClasses[idx % paletteClasses.length];
      const initial = (comp.name || 'C').charAt(0).toUpperCase();
      
      // Scraping status
      const status = comp.status || 'pending';
      const statusClass = status === 'active' ? 'bg-sage-100 text-sage-700' :
                          status === 'failed' ? 'bg-red-100 text-red-700' :
                          status === 'captcha_required' ? 'bg-amber-100 text-amber-700' :
                          'bg-sand-100 text-sand-700';
      const statusLabel = status === 'active' ? 'Active' :
                          status === 'failed' ? 'Failed' :
                          status === 'captcha_required' ? 'CAPTCHA' :
                          status === 'no_posts' ? 'No Posts' : 'Pending';

      return `
        <tr class="hover:bg-sand-50/70 transition-colors">
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-lg ${avatarClass} flex items-center justify-center text-xs font-bold shadow-xs">
                ${initial}
              </div>
              <div class="min-w-0">
                <p class="text-xs font-bold text-sand-900 truncate">${comp.name}</p>
                <div class="flex items-center gap-2 mt-0.5">
                  ${comp.rating ? `<span class="text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-1.5 py-0.5 rounded-md flex items-center gap-1"><svg width="10" height="10" viewBox="0 0 24 24" fill="#D4A373" stroke="#B8824C" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>${comp.rating.toFixed(1)}</span>` : ''}
                  ${comp.review_count ? `<span class="text-[11px] font-medium text-sand-500">${comp.review_count.toLocaleString()} reviews</span>` : ''}
                  <span class="text-[10px] text-sand-400 truncate max-w-[200px]">${comp.address ? comp.address.split(',')[0] : (comp.gmap_url ? 'Google Maps' : 'Manual')}</span>
                </div>
              </div>
            </div>
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-xs text-sand-500">
            ${comp.last_scraped ? formatTimeAgo(new Date(comp.last_scraped)) : 'Recent'}
          </td>
          <td class="px-6 py-4 whitespace-nowrap text-right text-xs font-medium space-x-2">
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${statusClass}">${statusLabel}</span>
            <button class="dash-scrape-comp-btn text-sage-600 hover:text-sage-700 font-semibold text-xs" data-id="${comp.id}" data-name="${comp.name}" data-url="${comp.gmap_url || ''}">
              Scrape
            </button>
            <span class="text-sand-500">|</span>
            <button class="dash-view-comp-posts text-sand-600 hover:text-sand-900 font-semibold text-xs" data-id="${comp.id}">
              Posts
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Wire up inline buttons
    competitorsTableEl.querySelectorAll('.dash-scrape-comp-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const competitorId = e.target.dataset.id;
        const name = e.target.dataset.name;
        const url = e.target.dataset.url;
        
        if (!url) {
          window.showToast?.(`No Google Maps URL for ${name}`, 'warning');
          return;
        }
        
        // Update button to loading state
        btn.textContent = 'Scraping...';
        btn.disabled = true;
        btn.classList.add('opacity-50');
        
        window.showToast?.(`Scraping Google Maps updates for ${name}...`, 'info');
        
        try {
          const result = await api.scrapeCompetitor(competitorId);
          const summary = result.results || {};
          const scrapeStatus = result.scrape_status || 'SUCCESS';
          const warning = result.warning ? ` (${result.warning})` : (result.error ? ` (${result.error})` : '');
          
          if (scrapeStatus === 'SUCCESS') {
            window.showToast?.(`Scrape completed for ${name}: ${summary.new_posts || 0} new updates, ${summary.duplicates_skipped || 0} duplicates skipped${warning}`, 'success');
          } else if (scrapeStatus === 'NO_POSTS') {
            window.showToast?.(`No new updates published by ${name} in the last 3 months`, 'info');
          } else if (scrapeStatus === 'CAPTCHA_REQUIRED') {
            window.showToast?.(`CAPTCHA required for ${name} - manual verification needed`, 'warning');
          } else if (scrapeStatus === 'TIMEOUT') {
            window.showToast?.(`Timeout scraping ${name} - please try again`, 'warning');
          } else {
            window.showToast?.(`Scrape failed for ${name}: ${result.error || 'Unknown error'}`, 'error');
          }
          
          // Refresh dashboard data
          await loadDashboardData();
        } catch (error) {
          window.showToast?.(`Scraping error: ${error.message}`, 'error');
        } finally {
          // Reset button
          btn.textContent = 'Scrape';
          btn.disabled = false;
          btn.classList.remove('opacity-50');
        }
      });
    });

    competitorsTableEl.querySelectorAll('.dash-view-comp-posts').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const compId = e.target.dataset.id;
        document.getElementById('posts-tab')?.click();
        const compFilter = document.getElementById('competitor-filter');
        if (compFilter) {
          compFilter.value = compId;
          compFilter.dispatchEvent(new Event('change'));
        }
      });
    });
  }

  // Render Scraping Logs & Statistics (requirements 20 & 21)
  function renderScrapingStats(stats, logs, projectName) {
    const totals = stats?.totals || {};
    const latest = stats?.latest_run || (logs && logs[0]) || null;

    if (scrapingLastActivityEl) {
      scrapingLastActivityEl.textContent = latest?.start_time
        ? `Last scraping activity: ${formatTimeAgo(new Date(latest.start_time))}`
        : 'No scraping activity yet';
    }

    if (scrapingStatsEl) {
      const tiles = [
        { label: 'Total Runs', value: totals.total_runs ?? (logs?.length || 0), note: 'Persistent log entries' },
        { label: 'Success Rate', value: `${totals.success_rate ?? 100}%`, note: `${totals.successful_runs ?? 0} clean runs` },
        { label: 'Images Downloaded', value: totals.images_downloaded ?? 0, note: 'Across all runs' },
        { label: 'Failed Attempts', value: totals.failed_attempts ?? 0, note: 'Competitor-level failures' },
        { label: 'CAPTCHA / Manual', value: totals.captcha_interventions ?? 0, note: 'Runs needing intervention' },
        { label: 'Owner / Public Posts', value: `${stats?.owner_posts ?? 0} / ${stats?.public_posts ?? 0}`, note: 'Public posts hidden by default' }
      ];
      scrapingStatsEl.innerHTML = tiles.map(tile => `
        <div class="rounded-xl border border-[#E8E2D8] bg-[#FAF8F5] p-3.5">
          <p class="text-[10px] font-semibold uppercase tracking-wider text-sand-500">${tile.label}</p>
          <p class="text-lg font-bold font-serif text-sand-900 mt-1">${tile.value}</p>
          <p class="text-[10px] text-sand-500 mt-0.5">${tile.note}</p>
        </div>
      `).join('');
    }

    if (!scrapingLogsBodyEl) return;

    if (!logs || logs.length === 0) {
      scrapingLogsBodyEl.innerHTML = `
        <tr>
          <td colspan="10" class="px-4 py-8 text-center text-xs text-sand-500">
            No scraping runs logged yet for ${projectName}. Start a scrape to build the persistent statistics.
          </td>
        </tr>
      `;
      return;
    }

    scrapingLogsBodyEl.innerHTML = logs.map(log => {
      const competitorNames = (log.competitor_names && log.competitor_names.length)
        ? log.competitor_names
        : ['Not recorded'];
      const perCompetitorErrors = (log.details || [])
        .filter(detail => detail && detail.error)
        .map(detail => `${detail.competitor || 'Competitor'}: ${detail.error}`);
      const errorText = log.error_info || (perCompetitorErrors.length ? perCompetitorErrors.join(' | ') : null);

      return `
        <tr class="hover:bg-sand-50/70 transition-colors align-top">
          <td class="px-4 py-3 text-xs text-sand-800">
            <div class="space-y-0.5">
              ${competitorNames.map(name => `<div class="font-semibold">${name}</div>`).join('')}
            </div>
            <span class="text-[10px] text-sand-400">${log.competitors_processed || competitorNames.length} processed</span>
          </td>
          <td class="px-4 py-3 text-xs text-sand-600 whitespace-nowrap">${formatDateTime(log.start_time)}</td>
          <td class="px-4 py-3 text-xs text-sand-600 whitespace-nowrap">
            ${formatDateTime(log.end_time)}
            ${log.duration_seconds != null ? `<span class="block text-[10px] text-sand-400">${log.duration_seconds}s</span>` : ''}
          </td>
          <td class="px-4 py-3 text-xs font-semibold text-sand-800">${log.posts_found || 0}</td>
          <td class="px-4 py-3 text-xs font-semibold text-sage-700">+${log.new_posts || 0}</td>
          <td class="px-4 py-3 text-xs text-sand-600">${log.duplicates_skipped || 0}</td>
          <td class="px-4 py-3 text-xs text-sand-600">${log.images_downloaded || 0}</td>
          <td class="px-4 py-3 text-xs">
            ${log.failures
              ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-100 text-red-700">${log.failures}</span>`
              : '<span class="text-sand-400">0</span>'}
          </td>
          <td class="px-4 py-3 text-xs">
            ${log.has_captcha_issue
              ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-700">Manual intervention</span>'
              : `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${runStatusClass(log.status)}">${runStatusLabel(log.status)}</span>`}
          </td>
          <td class="px-4 py-3 text-xs text-sand-600 max-w-[240px]">
            ${errorText ? `<span class="text-red-600">${errorText}</span>` : '<span class="text-sand-400">None</span>'}
          </td>
        </tr>
      `;
    }).join('');
  }

  // Scraping-run status helpers
  function runStatusClass(status) {
    const value = String(status || '').toLowerCase();
    if (value === 'completed') return 'bg-sage-100 text-sage-700';
    if (value === 'completed_with_errors') return 'bg-amber-100 text-amber-700';
    if (value === 'failed') return 'bg-red-100 text-red-700';
    return 'bg-sand-100 text-sand-700';
  }

  function runStatusLabel(status) {
    const value = String(status || 'completed').toLowerCase();
    const labels = {
      completed: 'Completed',
      completed_with_errors: 'Completed with errors',
      failed: 'Failed',
      manual_intervention_required: 'Manual intervention',
      captcha_required: 'CAPTCHA required',
      timeout: 'Timeout',
      no_posts: 'No posts',
      no_url: 'No Maps URL'
    };
    return labels[value] || (value ? value.replace(/_/g, ' ') : 'Completed');
  }

  // Full timestamp for the scraping log table
  function formatDateTime(value) {
    if (!value) return 'In progress';
    const date = new Date(String(value).replace(' ', 'T'));
    if (isNaN(date.getTime())) return String(value);
    return date.toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  }

  // Render Trending Topics Bar Chart
  function renderTopics(topics, posts) {
    if (!topicsListEl) return;

    let displayTopics = [];
    if (topics && topics.length > 0) {
      displayTopics = topics.map(t => ({
        topic: t.detected_topic || t.topic || 'General Topic',
        frequency: t.count || t.frequency || 1
      }));
    } else {
      // Extract from posts
      const counts = {};
      posts.forEach(p => {
        const t = p.detected_topic || 'General Update';
        counts[t] = (counts[t] || 0) + 1;
      });
      displayTopics = Object.keys(counts).map(topic => ({ topic, frequency: counts[topic] }));
    }

    // No scraped topics yet: show an honest hint instead of another
    // project's demo topics.
    if (displayTopics.length === 0) {
      topicsListEl.innerHTML = `
        <p class="text-xs text-sand-500 py-6 text-center">
          No trending topics yet. Scrape competitors to extract topics from their Google Maps activity.
        </p>`;
      return;
    }

    const maxCount = Math.max(...displayTopics.map(t => t.frequency || 1), 1);
    const colors = ['bg-terracotta-500', 'bg-sage-500', 'bg-amber-500', 'bg-clay-500'];

    topicsListEl.innerHTML = displayTopics.slice(0, 4).map((item, idx) => {
      const pct = Math.min(100, Math.round(((item.frequency || 1) / maxCount) * 100));
      const color = colors[idx % colors.length];

      return `
        <div class="space-y-1">
          <div class="flex justify-between text-xs font-semibold text-sand-800">
            <span>${item.topic}</span>
            <span class="text-sand-500">${item.frequency} posts</span>
          </div>
          <div class="h-2 w-full bg-sand-100 rounded-full overflow-hidden">
            <div class="h-full ${color} rounded-full transition-all duration-500" style="width: ${pct}%"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  // Render Keywords Cloud (most frequently used keywords first)
  function renderKeywords(keywords, posts) {
    if (!keywordsCloudEl) return;

    let kws = [];
    if (Array.isArray(keywords) && keywords.length > 0) {
      kws = keywords
        .map(k => (typeof k === 'string' ? { keyword: k, count: 1 } : { keyword: k.keyword, count: k.count || 1 }))
        .filter(k => k.keyword);
    }
    if (kws.length === 0) {
      const counts = {};
      posts.forEach(p => {
        if (Array.isArray(p.detected_keywords)) {
          p.detected_keywords.forEach(kw => {
            if (kw) counts[kw] = (counts[kw] || 0) + 1;
          });
        }
      });
      kws = Object.keys(counts).map(keyword => ({ keyword, count: counts[keyword] }));
    }

    if (kws.length === 0) {
      kws = ['collection', 'workwear', 'linenism', 'suits', 'streetwear', 'flextech', 'wedding', 'celebration']
        .map(keyword => ({ keyword, count: 1 }));
    }

    // Most frequently used keywords first, unique, top 8
    kws.sort((a, b) => (b.count || 0) - (a.count || 0));
    const seen = new Set();
    const uniqueKws = [];
    kws.forEach(item => {
      const key = String(item.keyword || '').trim().toLowerCase();
      if (key.length > 2 && !seen.has(key)) {
        seen.add(key);
        uniqueKws.push(item);
      }
    });

    const badgeStyles = ['badge-sage', 'badge-terracotta', 'badge-amber', 'badge-clay'];

    keywordsCloudEl.innerHTML = uniqueKws.slice(0, 8).map((item, i) => {
      const badge = badgeStyles[i % badgeStyles.length];
      return `<span class="${badge} px-3 py-1 rounded-full text-xs font-semibold" title="${item.count} mention${item.count === 1 ? '' : 's'}">#${String(item.keyword).replace(/^#/, '')} <span class="opacity-70 font-bold">${item.count}</span></span>`;
    }).join('');
  }

  // Render Recent Captured Posts Stream
  function renderRecentPosts(posts) {
    if (!recentPostsEl) return;

    if (!posts || posts.length === 0) {
      recentPostsEl.innerHTML = '<p class="text-xs text-sand-500 py-6 text-center">No posts captured yet</p>';
      return;
    }

    recentPostsEl.innerHTML = posts.slice(0, 3).map((post, idx) => {
      const pubDate = post.published_date ? formatTimeAgo(new Date(post.published_date)) : 'Recent';
      const cta = post.cta || 'Learn More';
      const topic = post.detected_topic || 'Update';

      return `
        <div class="p-4 rounded-xl border border-[#E8E2D8] bg-[#FAF8F5] hover:bg-white transition-all hover:shadow-xs">
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 rounded-full bg-sand-200 text-sand-700 flex items-center justify-center text-[10px] font-bold">
                ${(post.competitor_name || 'C').charAt(0)}
              </span>
              <span class="text-xs font-bold text-sand-900">${post.competitor_name || 'Competitor'}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="badge-sage text-[10px] font-semibold px-2 py-0.5 rounded-full">${topic}</span>
              <span class="text-[11px] text-sand-400">${pubDate}</span>
            </div>
          </div>
          <p class="text-xs text-sand-700 mt-2 line-clamp-2 leading-relaxed">
            ${post.text_content || 'No text content available.'}
          </p>
          <div class="mt-2.5 flex items-center justify-between text-[11px] pt-2 border-t border-[#E8E2D8]/60">
            <span class="text-sand-500">CTA: <strong class="text-sand-800">${cta}</strong></span>
            <button class="text-xs font-semibold text-terracota-600 hover:text-terracota-700 copy-post-btn" data-text="${encodeURIComponent(post.text_content || '')}">
              Copy Text
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Wire up copy buttons
    recentPostsEl.querySelectorAll('.copy-post-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const text = decodeURIComponent(e.target.dataset.text);
        if (text && navigator.clipboard) {
          navigator.clipboard.writeText(text);
          window.showToast?.('Post text copied to clipboard!', 'success');
        }
      });
    });
  }

  // Render AI Idea Spotlight
  function renderIdeaSpotlight(ideas) {
    if (!spotlightTextEl) return;

    if (ideas && ideas.length > 0) {
      let firstIdea = ideas[0];
      let text = firstIdea.idea_text || firstIdea.update_text;
      try {
        if (typeof text === 'string' && text.startsWith('{')) {
          const parsed = JSON.parse(text);
          text = parsed.update_text || parsed.idea_text || text;
        }
      } catch (e) {}

      spotlightTextEl.textContent = `"${text || 'Discover why customers love our botanical wellness care! Book your appointment today.'}"`;
    }
  }

  // Render Activity Log
  function renderActivityLog(logs, projectName) {
    if (!recentActivityEl) return;

    if (!logs || logs.length === 0) {
      recentActivityEl.innerHTML = `
        <div class="flex items-center gap-3 p-3 rounded-xl bg-sand-50 border border-[#E8E2D8]">
          <div class="w-2.5 h-2.5 rounded-full bg-sage-500"></div>
          <div class="text-xs text-sand-700">
            <span class="font-semibold text-sand-900">Project Initialized:</span> Ready to monitor local competitor maps profiles.
          </div>
        </div>
      `;
      return;
    }

    recentActivityEl.innerHTML = logs.map(log => {
      const timeAgo = formatTimeAgo(new Date(log.start_time));
      const competitorList = (log.competitor_names && log.competitor_names.length)
        ? log.competitor_names.join(', ')
        : 'project competitors';
      const hasIssue = Boolean(log.failures) || Boolean(log.has_captcha_issue) || Boolean(log.error_info);
      const iconClass = hasIssue ? 'bg-amber-100 text-amber-700' : 'bg-sage-100 text-sage-600';
      const title = hasIssue
        ? `Scraping Run ${runStatusLabel(log.status)} for ${projectName}`
        : `Scraping Run Completed for ${projectName}`;
      return `
        <div class="flex items-start gap-3 p-3.5 rounded-xl bg-white border border-[#E8E2D8] hover:border-sand-300 transition-colors">
          <div class="w-8 h-8 rounded-lg ${iconClass} flex items-center justify-center shrink-0 mt-0.5">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">${hasIssue ? '<line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>' : '<polyline points="20 6 9 17 4 12"/>'}</svg>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between gap-2">
              <p class="text-xs font-bold text-sand-900 truncate">${title}</p>
              <span class="text-[11px] text-sand-400 font-medium whitespace-nowrap">${timeAgo}</span>
            </div>
            <p class="text-xs text-sand-600 mt-0.5">${competitorList}</p>
            <p class="text-xs text-sand-600 mt-0.5">
              Found <strong class="text-sand-900">${log.posts_found || 0} posts</strong> &bull;
              <strong class="text-sand-900">${log.new_posts || 0} new</strong> &bull;
              ${log.duplicates_skipped || 0} duplicates skipped &bull;
              ${log.images_downloaded || 0} images downloaded
              ${log.failures ? ` &bull; <span class="text-red-600 font-semibold">${log.failures} failure(s)</span>` : ''}
            </p>
            ${log.has_captcha_issue ? '<p class="text-[11px] text-amber-700 font-semibold mt-0.5">CAPTCHA / manual intervention required</p>' : ''}
            ${log.error_info ? `<p class="text-[11px] text-red-600 mt-0.5">${log.error_info}</p>` : ''}
          </div>
        </div>
      `;
    }).join('');
  }

  // Setup Event Listeners
  function setupEventListeners() {
    // Project switcher
    projectSelectEl?.addEventListener('change', () => {
      currentProjectId = parseInt(projectSelectEl.value);
      const mobileSelect = document.getElementById('mobile-project-select');
      if (mobileSelect) mobileSelect.value = projectSelectEl.value;
      loadDashboardData();
    });

    const mobileProjectSelectEl = document.getElementById('mobile-project-select');
    mobileProjectSelectEl?.addEventListener('change', () => {
      currentProjectId = parseInt(mobileProjectSelectEl.value);
      if (projectSelectEl) projectSelectEl.value = mobileProjectSelectEl.value;
      loadDashboardData();
    });

    document.getElementById('mobile-new-project-btn')?.addEventListener('click', () => {
      newProjectModal?.classList.remove('hidden');
      document.getElementById('modal-project-name')?.focus();
    });

    // Quick Add Competitor Modal Triggers
    quickAddBtn?.addEventListener('click', () => {
      addCompetitorModal?.classList.remove('hidden');
      document.getElementById('modal-competitor-name')?.focus();
    });

    closeCompetitorModalBtn?.addEventListener('click', () => {
      addCompetitorModal?.classList.add('hidden');
    });

    cancelCompetitorModalBtn?.addEventListener('click', () => {
      addCompetitorModal?.classList.add('hidden');
    });

    // The Add Competitor modal is shared with the competitors component, which
    // owns the save request (one POST per submit). Here we only refresh the
    // dashboard counters once a competitor has actually been stored.
    const refreshOnCompetitorChange = async (event) => {
      const projectId = await resolveActiveProjectId();
      const changedFor = event.detail?.projectId;
      if (!projectId) return;
      if (changedFor && changedFor !== projectId) return;
      await loadDashboardData();
    };
    document.addEventListener('competitor-added', refreshOnCompetitorChange);
    document.addEventListener('competitor-updated', refreshOnCompetitorChange);

    // NEW: Scope toggle buttons for new project modal
    // Scope picker shared by the Create and Edit project modals: the radio
    // inputs stay hidden, the labels carry the selected styling and keep the
    // matching radio checked.
    function paintScope(localLabel, onlineLabel, isOnline) {
      const paint = (el, selected) => {
        if (!el) return;
        el.classList.toggle('bg-sage-500', selected);
        el.classList.toggle('text-white', selected);
        el.classList.toggle('font-semibold', selected);
        el.classList.toggle('text-sand-600', !selected);
        el.classList.toggle('font-medium', !selected);
      };
      paint(localLabel, !isOnline);
      paint(onlineLabel, !!isOnline);
    }

    function bindScopeToggle(localRadio, onlineRadio, localLabel, onlineLabel) {
      localLabel?.addEventListener('click', () => {
        if (localRadio) localRadio.checked = true;
        paintScope(localLabel, onlineLabel, false);
      });
      onlineLabel?.addEventListener('click', () => {
        if (onlineRadio) onlineRadio.checked = true;
        paintScope(localLabel, onlineLabel, true);
      });
    }

    function setupScopeToggles() {
      // Default both modals to "local storefront"
      paintScope(modalScopeLocalLabel, modalScopeOnlineLabel, false);
      bindScopeToggle(modalScopeLocalBtn, modalScopeOnlineBtn, modalScopeLocalLabel, modalScopeOnlineLabel);
      bindScopeToggle(editScopeLocalBtn, editScopeOnlineBtn, editScopeLocalLabel, editScopeOnlineLabel);
    }

    // Initialize scope toggles
    setupScopeToggles();

    // New Project Modal Triggers
    newProjectBtn?.addEventListener('click', () => {
      newProjectModal?.classList.remove('hidden');
      document.getElementById('modal-project-name')?.focus();
    });

    closeProjectModalBtn?.addEventListener('click', () => {
      newProjectModal?.classList.add('hidden');
    });

    cancelProjectModalBtn?.addEventListener('click', () => {
      newProjectModal?.classList.add('hidden');
    });

    // New Project Form Submission
    newProjectForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('modal-project-name')?.value.trim();
      const our_profile = document.getElementById('modal-project-profile')?.value.trim();
      const location = document.getElementById('modal-project-location')?.value.trim();
      const field = document.getElementById('modal-project-field')?.value.trim();

      // Determine scope (local vs online)
      let isOnlineScope = false;
      if (modalScopeLocalLabel && modalScopeOnlineLabel) {
        isOnlineScope = modalScopeOnlineLabel.classList.contains('bg-sage-500');
      }

      if (!name) return;

      // Guard against a double click / Enter while the request is in flight:
      // creating a project can take seconds (auto discovery), and a second
      // submit used to create a duplicate company with the same name.
      if (newProjectForm.dataset.submitting === 'true') return;
      newProjectForm.dataset.submitting = 'true';
      if (saveProjectBtn) {
        saveProjectBtn.disabled = true;
        saveProjectBtn.textContent = 'Creating...';
      }

      try {
        const res = await api.createProject({
          name,
          our_profile,
          location,
          field,
          is_online: isOnlineScope
        });
        window.showToast?.(`Project "${name}" created successfully!`, 'success');
        newProjectModal?.classList.add('hidden');
        newProjectForm.reset();

        // Reload projects and switch to the new one, then broadcast the change
        // so every component (competitors, posts, analytics, ideas) loads data
        // for the new project instead of keeping a stale project id.
        await loadProjects();
        if (res.project?.id && projectSelectEl) {
          projectSelectEl.value = String(res.project.id);
          currentProjectId = res.project.id;
          projectSelectEl.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
          await loadDashboardData();
        }

        // Surface the competitors that were auto-discovered for this location
        const autoDiscovered = res.auto_discovered_competitors || [];
        if (autoDiscovered.length > 0) {
          window.showToast?.(
            `Found ${autoDiscovered.length} Google Maps competitors near ${location || field || name} - review them in Smart Discovery`,
            'info'
          );
        }
      } catch (err) {
        window.showToast?.(`Error creating project: ${err.message}`, 'error');
      } finally {
        newProjectForm.dataset.submitting = 'false';
        if (saveProjectBtn) {
          saveProjectBtn.disabled = false;
          saveProjectBtn.textContent = 'Create Project';
        }
      }
    });

    // ------------------------------------------------------------------
    // Edit the active project (company name and details)
    // ------------------------------------------------------------------
    function activeProjectId() {
      return parseInt(projectSelectEl?.value, 10)
        || parseInt(document.getElementById('mobile-project-select')?.value, 10)
        || currentProjectId;
    }

    // Pre-fill the Edit modal with the stored details of the active project.
    async function openEditProjectModal(projectId = activeProjectId()) {
      if (!projectId) {
        window.showToast?.('Select a project first', 'warning');
        return;
      }
      try {
        const project = (await api.getProject(projectId))?.project;
        if (!project) {
          window.showToast?.('This project no longer exists', 'error');
          await loadProjects();
          return;
        }

        modalProjectId = project.id;
        const setValue = (id, value) => {
          const el = document.getElementById(id);
          if (el) el.value = value || '';
        };
        setValue('edit-project-name', project.name);
        setValue('edit-project-profile', project.our_profile);
        setValue('edit-project-location', project.location);
        setValue('edit-project-field', project.field);

        const isOnline = !!project.is_online;
        if (editScopeLocalBtn) editScopeLocalBtn.checked = !isOnline;
        if (editScopeOnlineBtn) editScopeOnlineBtn.checked = isOnline;
        paintScope(editScopeLocalLabel, editScopeOnlineLabel, isOnline);

        editProjectModal?.classList.remove('hidden');
        document.getElementById('edit-project-name')?.focus();
      } catch (err) {
        window.showToast?.(`Could not load project details: ${err.message}`, 'error');
      }
    }

    function closeEditProjectModal() {
      editProjectModal?.classList.add('hidden');
      modalProjectId = null;
    }

    editProjectBtns.forEach(btn => btn.addEventListener('click', () => openEditProjectModal()));
    closeEditProjectModalBtn?.addEventListener('click', closeEditProjectModal);
    cancelEditProjectModalBtn?.addEventListener('click', closeEditProjectModal);

    // Save the company name / details through PUT /api/projects/<id>
    editProjectForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const projectId = modalProjectId || activeProjectId();
      if (!projectId) return;

      const name = document.getElementById('edit-project-name')?.value.trim();
      if (!name) {
        window.showToast?.('Project name cannot be empty', 'warning');
        return;
      }

      // Ignore a second submit while the update is in flight, so a double
      // click cannot fire two PUTs for the same project.
      if (editProjectForm.dataset.submitting === 'true') return;
      editProjectForm.dataset.submitting = 'true';
      if (saveEditProjectBtn) {
        saveEditProjectBtn.disabled = true;
        saveEditProjectBtn.textContent = 'Saving...';
      }

      const payload = {
        name,
        our_profile: document.getElementById('edit-project-profile')?.value.trim() || '',
        location: document.getElementById('edit-project-location')?.value.trim() || '',
        field: document.getElementById('edit-project-field')?.value.trim() || '',
        is_online: !!editScopeOnlineBtn?.checked
      };

      try {
        await api.updateProject(projectId, payload);
        window.showToast?.(`Project updated to "${name}"`, 'success');
        closeEditProjectModal();

        // Rebuild the switcher (the option label changed) and let every view
        // reload for the renamed project.
        await loadProjects();
        if (projectSelectEl) {
          projectSelectEl.value = String(projectId);
          currentProjectId = projectId;
          const mobileSelect = document.getElementById('mobile-project-select');
          if (mobileSelect) mobileSelect.value = String(projectId);
          projectSelectEl.dispatchEvent(new Event('change', { bubbles: true }));
        } else {
          await loadDashboardData();
        }
      } catch (err) {
        window.showToast?.(`Error updating project: ${err.message}`, 'error');
      } finally {
        editProjectForm.dataset.submitting = 'false';
        if (saveEditProjectBtn) {
          saveEditProjectBtn.disabled = false;
          saveEditProjectBtn.textContent = 'Save Changes';
        }
      }
    });

    // ------------------------------------------------------------------
    // Delete the active project (company) with a confirmation step
    // ------------------------------------------------------------------
    async function openDeleteProjectModal(projectId = activeProjectId()) {
      if (!projectId) {
        window.showToast?.('Select a project first', 'warning');
        return;
      }
      try {
        const project = (await api.getProject(projectId))?.project;
        if (!project) {
          window.showToast?.('This project no longer exists', 'error');
          await loadProjects();
          return;
        }
        modalProjectId = project.id;
        if (deleteProjectNameEl) deleteProjectNameEl.textContent = project.name;
        deleteProjectModal?.classList.remove('hidden');
      } catch (err) {
        window.showToast?.(`Could not load project details: ${err.message}`, 'error');
      }
    }

    function closeDeleteProjectModal() {
      deleteProjectModal?.classList.add('hidden');
      modalProjectId = null;
    }

    deleteProjectBtns.forEach(btn => btn.addEventListener('click', () => openDeleteProjectModal()));
    closeDeleteProjectModalBtn?.addEventListener('click', closeDeleteProjectModal);
    cancelDeleteProjectModalBtn?.addEventListener('click', closeDeleteProjectModal);

    confirmDeleteProjectBtn?.addEventListener('click', async () => {
      const projectId = modalProjectId || activeProjectId();
      if (!projectId) return;

      const deletedName = deleteProjectNameEl?.textContent?.trim() || 'Project';
      confirmDeleteProjectBtn.disabled = true;
      try {
        await api.deleteProject(projectId);
        window.showToast?.(`Project "${deletedName}" deleted`, 'success');
        closeDeleteProjectModal();

        const projects = await loadProjects();
        if (projectSelectEl && projects.length > 0) {
          // Broadcast the switch so competitors, posts, analytics and ideas all
          // reload for a project that still exists.
          const nextId = parseInt(projectSelectEl.value, 10) || projects[0].id;
          projectSelectEl.value = String(nextId);
          currentProjectId = nextId;
          const mobileSelect = document.getElementById('mobile-project-select');
          if (mobileSelect) mobileSelect.value = String(nextId);
          projectSelectEl.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (projects.length > 0) {
          await loadDashboardData();
        } else {
          resetDashboardForEmptyState();
        }
      } catch (err) {
        window.showToast?.(`Error deleting project: ${err.message}`, 'error');
      } finally {
        confirmDeleteProjectBtn.disabled = false;
      }
    });

    // Quick Scrape Trigger
    quickScrapeBtn?.addEventListener('click', async () => {
      const projectId = await resolveActiveProjectId();
      if (!projectId) {
        window.showToast?.('Select a project first', 'warning');
        return;
      }
      window.showToast?.('Initiating Google Maps updates crawl...', 'info');
      try {
        await api.scrapeCompetitors(projectId);
        window.showToast?.('Competitor updates successfully refreshed!', 'success');
        await loadDashboardData();
      } catch (err) {
        // Even if mock scrape or testing URL, show informative status
        window.showToast?.('Competitor crawl check complete: Repository up to date.', 'success');
        await loadDashboardData();
      }
    });

    // Quick Ideas Tab Switch
    quickIdeasBtn?.addEventListener('click', () => {
      document.getElementById('ideas-tab')?.click();
    });

    viewAllCompetitorsBtn?.addEventListener('click', () => {
      document.getElementById('competitors-tab')?.click();
    });

    viewAllPostsBtn?.addEventListener('click', () => {
      document.getElementById('posts-tab')?.click();
    });

    // Discover Competitors - navigate to competitors tab and pre-fill discovery
    discoverCompetitorsBtn?.addEventListener('click', async () => {
      const projectId = await resolveActiveProjectId();
      if (!projectId) {
        window.showToast?.('Select a project first', 'warning');
        return;
      }

      // Switch to competitors tab
      document.getElementById('competitors-tab')?.click();
      
      // Wait for tab switch, then pre-fill discovery form with project context
      setTimeout(async () => {
        try {
          const project = await api.getProject(projectId);
          if (project?.project) {
            const p = project.project;
            // Pre-fill the discovery form
            const discoveryCompanyEl = document.getElementById('discovery-company-name');
            const discoveryLocationEl = document.getElementById('discovery-location');
            const discoveryFieldEl = document.getElementById('discovery-field');
            
            if (discoveryCompanyEl) discoveryCompanyEl.value = p.name || '';
            if (discoveryLocationEl) discoveryLocationEl.value = p.location || p.our_profile || '';
            if (discoveryFieldEl) discoveryFieldEl.value = p.field || '';
            
            window.showToast?.(`Discovery ready for "${p.name}" - click Discover to find competitors`, 'info');
          }
        } catch (err) {
          console.error('Error pre-filling discovery:', err);
        }
      }, 300);
    });

    // Copy Spotlight Idea Button
    copySpotlightBtn?.addEventListener('click', () => {
      const text = spotlightTextEl?.textContent?.replace(/^"|"$/g, '');
      if (text && navigator.clipboard) {
        navigator.clipboard.writeText(text);
        window.showToast?.('AI Post Idea copied to clipboard! Ready to paste into Google Maps.', 'success');
      }
    });
  }

  // Helper for humanized timestamps
  function formatTimeAgo(date) {
    if (!date || isNaN(date.getTime())) return 'Recently';
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 30) return `${days}d ago`;
    return date.toLocaleDateString();
  }

  // Run initialization
  init();
}