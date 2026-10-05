// Posts Component
import { createProjectReloader } from './project-scope.js';
import {
  getStoredProjectData,
  saveStoredProjectData,
  getStoredActiveProjectId
} from './project-store.js';

export function initPosts(api) {
  const postsView = document.getElementById('posts-view');
  if (!postsView) return;

  // Elements
  const projectSelectEl = document.getElementById('project-select');
  const competitorFilterEl = document.getElementById('competitor-filter');
  const topicFilterEl = document.getElementById('topic-filter');
  const keywordFilterEl = document.getElementById('keyword-filter');
  const postsGridEl = document.getElementById('posts-grid');

  // Owner priority / public post controls
  const showPublicPostsBtn = document.getElementById('show-public-posts-btn');
  const showPublicPostsLabel = document.getElementById('show-public-posts-label');
  const ownerPostsCountEl = document.getElementById('owner-posts-count');
  const publicPostsCountEl = document.getElementById('public-posts-count');
  const publicPostsStateEl = document.getElementById('public-posts-state');
  const ownProfilePostsCountEl = document.getElementById('own-profile-posts-count');

  let currentProjectId = getStoredActiveProjectId() || 11;
  // Owner updates are always shown first; public (user generated) posts are
  // hidden until the user explicitly presses "Show public posts".
  let showPublicPosts = false;
  let lastLoadedPosts = [];

  // The dashboard fills the header switcher asynchronously, so wait for it
  // instead of falling back to a hard-coded project id (which would request a
  // company that may have been deleted).
  async function resolveProjectId(waitMs = 5000) {
    const mobileSelect = document.getElementById('mobile-project-select');
    const deadline = Date.now() + waitMs;
    for (;;) {
      const projectId = parseInt(projectSelectEl?.value, 10)
        || parseInt(mobileSelect?.value, 10)
        || currentProjectId;
      if (projectId) return projectId;
      if (Date.now() >= deadline) return null;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  // Owner posts keep priority, public posts are opt-in.
  function isPublicPost(post) {
    return Boolean(post && (post.is_public || post.post_source === 'public'));
  }

  function visiblePosts(posts) {
    const list = Array.isArray(posts) ? posts : [];
    const ownerPosts = list.filter(post => !isPublicPost(post));
    const publicPosts = list.filter(isPublicPost);
    // Defensive: owner updates always render before public content.
    return showPublicPosts ? [...ownerPosts, ...publicPosts] : ownerPosts;
  }

  function updateOwnerPublicCounters(posts) {
    const list = Array.isArray(posts) ? posts : [];
    const publicCount = list.filter(isPublicPost).length;
    const ownerCount = list.length - publicCount;
    const ownProfileCount = list.filter(post => post && post.is_own_profile).length;

    if (ownerPostsCountEl) ownerPostsCountEl.textContent = ownerCount;
    if (publicPostsCountEl) publicPostsCountEl.textContent = publicCount;
    if (publicPostsStateEl) publicPostsStateEl.textContent = showPublicPosts ? 'shown' : 'hidden';
    if (ownProfilePostsCountEl) {
      ownProfilePostsCountEl.textContent = `Your profile: ${ownProfileCount}`;
      ownProfilePostsCountEl.classList.toggle('hidden', ownProfileCount === 0);
    }
    if (showPublicPostsLabel) {
      showPublicPostsLabel.textContent = showPublicPosts
        ? 'Hide public posts'
        : `Show public posts${publicCount ? ` (${publicCount})` : ''}`;
    }
  }

  function sourceBadge(post) {
    if (isPublicPost(post)) {
      return '<span class="badge-clay px-2 py-0.5 rounded-full text-[11px] font-semibold">Public post</span>';
    }
    if (post && post.is_own_profile) {
      return '<span class="badge-terracota px-2 py-0.5 rounded-full text-[11px] font-semibold">Your profile update</span>';
    }
    return '<span class="badge-sage px-2 py-0.5 rounded-full text-[11px] font-semibold">Owner update</span>';
  }

  // Initialize
  async function init() {
    try {
      setupEventListeners();
      await postsProjectReload.reload();
    } catch (error) {
      console.error('Error initializing posts component:', error);
    }
  }

  // Project-scoped loading, deferred while this tab is off screen so that a
  // switch made from another tab reloads only what the user is looking at.
  const postsProjectReload = createProjectReloader({
    tab: 'posts',
    reload: async () => {
      await loadCompetitorFilter();
      await loadPosts();
    }
  });

  // Helper to apply and render posts list
  function displayPosts(posts) {
    lastLoadedPosts = posts;
    updateOwnerPublicCounters(posts);

    // Populate topic filter dynamically if needed
    if (topicFilterEl && topicFilterEl.options.length <= 1) {
      const topics = [...new Set(posts.map(p => p.detected_topic).filter(Boolean))];
      topicFilterEl.innerHTML = `
        <option value="all">All Topics</option>
        ${topics.map(t => `<option value="${t}">${t}</option>`).join('')}
      `;
    }

    const selectedTopic = topicFilterEl?.value || 'all';
    const keyword = keywordFilterEl?.value?.trim() || '';

    // Apply client-side filtering for search & topic
    let filteredPosts = visiblePosts(posts);
    if (selectedTopic !== 'all') {
      filteredPosts = filteredPosts.filter(p => p.detected_topic === selectedTopic);
    }
    if (keyword) {
      const lowerKw = keyword.toLowerCase();
      filteredPosts = filteredPosts.filter(post =>
        (post.text_content && post.text_content.toLowerCase().includes(lowerKw)) ||
        (post.detected_topic && post.detected_topic.toLowerCase().includes(lowerKw)) ||
        (post.competitor_name && post.competitor_name.toLowerCase().includes(lowerKw)) ||
        (post.detected_keywords && post.detected_keywords.some(k => k.toLowerCase().includes(lowerKw)))
      );
    }

    renderPostsGrid(filteredPosts);
  }

  // Load competitor filter based on selected project
  async function loadCompetitorFilter() {
    try {
      const projectId = await resolveProjectId() || getStoredActiveProjectId() || 11;
      if (!projectId) {
        if (competitorFilterEl) {
          competitorFilterEl.innerHTML = '<option value="all">All Competitors</option>';
        }
        return;
      }
      // Populate from cached data immediately if available
      const cached = getStoredProjectData(projectId);
      if (cached?.competitors?.length && competitorFilterEl) {
        competitorFilterEl.innerHTML = `
          <option value="all">All Competitors</option>
          ${cached.competitors.map(competitor => `<option value="${competitor.id}">${competitor.name}</option>`).join('')}
        `;
      }
      const competitorsResponse = await api.getCompetitors(projectId);
      const competitors = competitorsResponse.competitors || [];
      if (competitorFilterEl) {
        competitorFilterEl.innerHTML = `
          <option value="all">All Competitors</option>
          ${competitors.map(competitor => `<option value="${competitor.id}">${competitor.name}</option>`).join('')}
        `;
      }
    } catch (error) {
      console.warn('Error loading competitor filter live:', error);
    }
  }

  // Load posts based on filters
  async function loadPosts() {
    try {
      const projectId = await resolveProjectId() || getStoredActiveProjectId() || 11;
      if (!projectId) {
        renderPostsGrid([]);
        return;
      }
      currentProjectId = projectId;

      // 1. Immediately display cached posts if available
      const cached = getStoredProjectData(projectId);
      if (cached?.posts?.length) {
        displayPosts(cached.posts);
      }

      api.showLoading();
      const competitorId = competitorFilterEl?.value === 'all' ? undefined : parseInt(competitorFilterEl?.value);
      const response = await api.getPosts({
        project_id: projectId,
        competitor_id: competitorId,
        limit: 100,
        include_public: true
      });
      const posts = response.posts || [];
      displayPosts(posts);
      saveStoredProjectData(projectId, { posts });
    } catch (error) {
      console.warn('[Posts] Error loading posts live, using cached data:', error);
      if (!lastLoadedPosts?.length) {
        showErrorState(error.message);
      }
    } finally {
      api.hideLoading();
    }
  }

  // Render posts grid
  function renderPostsGrid(posts) {
    console.log('[Posts] Rendering', posts.length, 'posts');
    if (!postsGridEl) return;

    if (!posts || posts.length === 0) {
      console.log('[Posts] No posts to render, showing empty state');
      const hiddenPublic = !showPublicPosts && lastLoadedPosts.some(isPublicPost);
      postsGridEl.innerHTML = `
        <div class="col-span-3 text-center py-12">
          <div class="w-14 h-14 mx-auto bg-sand-100 text-sand-500 rounded-2xl flex items-center justify-center mb-3">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          </div>
          <h3 class="text-base font-bold text-sand-900">No owner updates found</h3>
          <p class="text-sand-500 text-xs mt-1">
            ${hiddenPublic
              ? 'Public posts are hidden. Press <span class="font-semibold">Show public posts</span> to include them.'
              : 'Try adjusting your filters or scraping for new data'}
          </p>
        </div>
      `;
      return;
    }

    postsGridEl.innerHTML = posts.map(post => `
      <div class="earth-card overflow-hidden">
        <div class="p-5">
          <div class="relative h-44 w-full overflow-hidden rounded-xl mb-3.5 bg-sand-100 border border-[#E8E2D8]">
            ${post.image_urls && post.image_urls.length > 0 ? `
              <img src="${post.image_urls[0]}" alt="Post image" class="object-cover w-full h-full">
            ` : `
              <div class="absolute inset-0 bg-sand-100 flex flex-col items-center justify-center text-sand-400 gap-1.5">
                <svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                  <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/>
                  <circle cx="9" cy="9" r="2"/>
                  <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
                </svg>
                <span class="text-[11px] font-medium text-sand-500">Google Maps Post</span>
              </div>
            `}
          </div>
          <div class="space-y-3">
            <div class="flex items-center justify-between text-xs">
              <span class="font-bold text-sand-900">${post.competitor_name || 'Competitor'}</span>
              <span class="text-sand-400">${formatDate(post.published_date || post.scrape_date)}</span>
            </div>
            <div class="flex flex-wrap items-center gap-1.5">${sourceBadge(post)}</div>
            <p class="text-xs text-sand-700 line-clamp-3 leading-relaxed">${post.text_content || 'No content available'}</p>
            <div class="flex flex-wrap items-center gap-1.5 text-[11px]">
              ${post.detected_topic ? `<span class="badge-sage px-2 py-0.5 rounded-full font-semibold">${post.detected_topic}</span>` : ''}
              ${post.cta ? `<span class="badge-terracotta px-2 py-0.5 rounded-full font-semibold">CTA: ${post.cta}</span>` : ''}
              ${post.detected_keywords && post.detected_keywords.length > 0 ? `
                ${post.detected_keywords.slice(0, 2).map(keyword => `
                  <span class="badge-amber px-2 py-0.5 rounded-full font-semibold">#${keyword}</span>
                `).join('')}
              ` : ''}
            </div>
            <button class="btn-sand w-full text-center py-2 text-xs font-semibold rounded-xl mt-2 block"
                    data-post-id="${post.id}">
              View Details
            </button>
          </div>
        </div>
      </div>
    `).join('');

    // Add event listeners to view details buttons
    document.querySelectorAll('[data-post-id]').forEach(button => {
      button.addEventListener('click', async (e) => {
        const postId = e.target.dataset.postId;
        try {
          api.showLoading();
          const post = await api.getPost(postId);
          showPostDetailsModal(post);
        } catch (error) {
          showToast(`Error loading post details: ${error.message}`, 'error');
        } finally {
          api.hideLoading();
        }
      });
    });
  }

  // Show post details modal
  function showPostDetailsModal(rawPost) {
    const post = rawPost?.post || rawPost || {};
    const competitorName = post.competitor_name || post.competitor || 'Competitor';
    const publishedDate = post.published_date || post.date || post.scrape_date;
    const textContent = post.text_content || post.post_text || post.content || 'No content available';
    let imageUrls = [];
    if (Array.isArray(post.image_urls)) {
      imageUrls = post.image_urls;
    } else if (typeof post.image_urls === 'string') {
      try { imageUrls = JSON.parse(post.image_urls); } catch (e) { imageUrls = [post.image_urls]; }
    }
    let detectedKeywords = [];
    if (Array.isArray(post.detected_keywords)) {
      detectedKeywords = post.detected_keywords;
    } else if (typeof post.detected_keywords === 'string') {
      try { detectedKeywords = JSON.parse(post.detected_keywords); } catch (e) { detectedKeywords = []; }
    }
    const detectedTopic = post.detected_topic || post.topic || '';
    const cta = post.cta || '';
    const scrapeDate = post.scrape_date || post.scraped_at || post.published_date;
    const postUrl = post.post_url || post.url || post.competitor_gmap_url;
    const initial = (competitorName || 'C').charAt(0).toUpperCase();

    // Create modal
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
      <div class="bg-white border border-[#E8E2D8] p-6 sm:p-7 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto relative shadow-2xl animate-fade-in">
        <button class="absolute top-4 right-4 p-2 rounded-xl hover:bg-sand-100 transition-colors text-sand-500 hover:text-sand-900"
                id="close-post-modal">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-linecap="round"/>
          </svg>
        </button>
        <div class="space-y-5">
          <div class="flex items-start space-x-3.5">
            <div class="flex-shrink-0 h-12 w-12 bg-sage-100 text-sage-700 border border-sage-200 rounded-xl flex items-center justify-center text-base font-bold shadow-xs">
              ${initial}
            </div>
            <div>
              <h2 class="text-xl font-bold font-serif text-sand-900">${competitorName}</h2>
              <p class="text-xs text-sand-500 mt-0.5">Published: ${formatDate(publishedDate)}</p>
              <div class="mt-1.5 flex flex-wrap items-center gap-1.5">${sourceBadge(post)}</div>
            </div>
          </div>

          ${imageUrls && imageUrls.length > 0 ? `
            <div class="space-y-3">
              <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
                ${imageUrls.map((url, index) => `
                  <div class="relative h-48 overflow-hidden rounded-xl bg-sand-100 border border-[#E8E2D8]">
                    <img src="${url}" alt="Post image ${index + 1}" class="object-cover w-full h-full" onerror="this.parentElement.style.display='none'">
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <div class="p-4 rounded-xl bg-[#FAF8F5] border border-[#E8E2D8]">
            <p class="text-xs sm:text-sm text-sand-800 whitespace-pre-line leading-relaxed">${textContent}</p>
          </div>

          ${cta ? `
            <div class="border-t border-[#E8E2D8] pt-3.5 flex items-center justify-between">
              <span class="text-xs font-semibold text-sand-700">Call to Action:</span>
              <span class="badge-terracotta text-xs font-semibold px-2.5 py-1 rounded-full">${cta}</span>
            </div>
          ` : ''}

          ${detectedTopic ? `
            <div class="border-t border-[#E8E2D8] pt-3.5 flex items-center justify-between">
              <span class="text-xs font-semibold text-sand-700">Detected Topic:</span>
              <span class="badge-sage text-xs font-semibold px-2.5 py-1 rounded-full">${detectedTopic}</span>
            </div>
          ` : ''}

          ${detectedKeywords && detectedKeywords.length > 0 ? `
            <div class="border-t border-[#E8E2D8] pt-3.5">
              <p class="text-xs font-semibold text-sand-700 mb-2">Detected Keywords:</p>
              <div class="flex flex-wrap gap-1.5">
                ${detectedKeywords.map(keyword => `
                  <span class="badge-amber text-[11px] font-semibold px-2.5 py-0.5 rounded-full">#${keyword}</span>
                `).join('')}
              </div>
            </div>
          ` : ''}

          <div class="border-t border-[#E8E2D8] pt-3.5 text-xs text-sand-500 space-y-1">
            <div class="flex justify-between">
              <span>Captured on:</span>
              <span class="font-medium text-sand-700">${formatDate(scrapeDate)}</span>
            </div>
            ${postUrl ? `
              <div class="flex justify-between pt-1">
                <span>Google Maps Source:</span>
                <a href="${postUrl}" target="_blank" rel="noopener noreferrer" class="text-terracotta-600 hover:text-terracotta-700 font-semibold underline">
                  Open Post on Google Maps &rarr;
                </a>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    // Close modal
    const closeBtn = modal.querySelector('#close-post-modal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        modal.remove();
      });
    }

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.remove();
      }
    });

    // Close on ESC key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        modal.remove();
      }
    });
  }

  // Setup event listeners
  function setupEventListeners() {
    projectSelectEl?.addEventListener('change', () => {
      postsProjectReload.reload();
    });

    competitorFilterEl?.addEventListener('change', loadPosts);
    topicFilterEl?.addEventListener('change', loadPosts);

    // Public posts are hidden by default and only revealed on demand.
    showPublicPostsBtn?.addEventListener('click', () => {
      showPublicPosts = !showPublicPosts;
      showPublicPostsBtn.setAttribute('aria-pressed', String(showPublicPosts));
      showPublicPostsBtn.classList.toggle('bg-sage-500', showPublicPosts);
      showPublicPostsBtn.classList.toggle('text-white', showPublicPosts);
      showPublicPostsBtn.classList.toggle('hover:bg-sage-600', showPublicPosts);
      showPublicPostsBtn.classList.toggle('hover:bg-sand-50', !showPublicPosts);
      updateOwnerPublicCounters(lastLoadedPosts);
      renderPostsGrid(visiblePosts(lastLoadedPosts));
      const publicCount = lastLoadedPosts.filter(isPublicPost).length;
      window.showToast?.(
        showPublicPosts
          ? (publicCount ? `Showing ${publicCount} public post${publicCount === 1 ? '' : 's'}.` : 'Public posts shown - none captured yet.')
          : 'Public posts hidden again.',
        'info'
      );
    });

    if (keywordFilterEl) {
      keywordFilterEl.addEventListener('input', () => {
        clearTimeout(keywordFilterEl.debounceTimer);
        keywordFilterEl.debounceTimer = setTimeout(() => {
          loadPosts();
        }, 250);
      });
    }
  }

  // Show error state
  function showErrorState(message) {
    if (!postsGridEl) return;
    postsGridEl.innerHTML = `
      <div class="col-span-3 text-center py-12">
        <div class="w-12 h-12 mx-auto bg-terracotta-500 text-white rounded-xl flex items-center justify-center shadow-xs">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <h3 class="text-base font-bold text-sand-900 mt-4">Error loading posts</h3>
        <p class="text-sand-500 text-xs mt-1">${message}</p>
      </div>
    `;
  }

  // Format date
  function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    const options = { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' };
    return new Date(dateString).toLocaleDateString(undefined, options);
  }

  // Toast function
  function showToast(message, type = 'info') {
    alert(`${type.toUpperCase()}: ${message}`);
  }

  // Initialize
  init();
}