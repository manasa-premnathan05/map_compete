// Ideas & AI Content Generation Component
// Spec: Section 12 — AI-Based Content Analysis & Post Generation
export function initIdeas(api) {
  const ideasView = document.getElementById('ideas-view');
  if (!ideasView) return;

  const projectSelectEl   = document.getElementById('project-select');
  const ideasCountEl      = document.getElementById('ideas-count');
  const generateIdeasBtn  = document.getElementById('generate-ideas-btn');
  const completeToggle    = document.getElementById('complete-update-toggle');
  const ideasLoadingEl    = document.getElementById('ideas-loading');
  const ideasResultsEl    = document.getElementById('ideas-results');
  const previousIdeasEl   = document.getElementById('previous-ideas');

  let currentProjectId = null;
  // Track generated idea texts to avoid duplicates
  let existingIdeaTexts = [];
  // Cache analysis data
  let cachedAnalysis = null;
  let cachedPosts = [];

  // Wait for the header switcher (filled by the dashboard) instead of falling
  // back to a hard-coded project id, which could point at a deleted company.
  async function resolveProjectId(waitMs = 5000) {
    const deadline = Date.now() + waitMs;
    for (;;) {
      const projectId = parseInt(projectSelectEl?.value, 10) || currentProjectId;
      if (projectId) return projectId;
      if (Date.now() >= deadline) return null;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  // ── Init ───────────────────────────────────────────────────────────────────
  async function init() {
    currentProjectId = await resolveProjectId();
    setupEventListeners();
    await loadAll();
  }

  async function loadAll() {
    try {
      currentProjectId = await resolveProjectId() || currentProjectId;
      if (!currentProjectId) return;
      // Fetch previous ideas + posts + analysis in parallel
      const [ideasRes, postsRes] = await Promise.allSettled([
        api.getGeneratedIdeas(currentProjectId),
        api.getPosts({ project_id: currentProjectId, limit: 200 })
      ]);
      const ideas = ideasRes.status === 'fulfilled' ? (ideasRes.value?.ideas || []) : [];
      cachedPosts  = postsRes.status === 'fulfilled'  ? (postsRes.value?.posts  || []) : [];

      // Build dedup list from previous ideas
      existingIdeaTexts = ideas.map(i => i.idea_text || i.update_text || '').filter(Boolean);

      renderPreviousIdeas(ideas);
      renderAnalysisSummary(cachedPosts);
    } catch (err) {
      console.error('Error loading ideas view:', err);
    }
  }

  // ── Analysis Summary Panel ─────────────────────────────────────────────────
  function renderAnalysisSummary(posts) {
    const el = document.getElementById('ideas-analysis-panel');
    if (!el) return;
    if (!posts || posts.length === 0) {
      el.innerHTML = `
        <div class="p-4 bg-sand-50 border border-[#E8E2D8] rounded-xl text-xs text-sand-500 text-center">
          No competitor posts scraped yet. Add competitors and run scraping to enable content analysis.
        </div>`;
      return;
    }

    // Derive quick metrics from scraped posts
    const competitorSet = new Set(posts.map(p => p.competitor_name || p.competitor).filter(Boolean));
    const topicCounts = {};
    const kwCounts = {};
    const ctaCounts = {};
    const contentTypeCounts = {};

    posts.forEach(p => {
      // Topics
      const t = p.detected_topic || p.topic;
      if (t) topicCounts[t] = (topicCounts[t] || 0) + 1;

      // Keywords
      let kws = p.detected_keywords || p.keywords;
      if (typeof kws === 'string') { try { kws = JSON.parse(kws); } catch { kws = []; } }
      (kws || []).forEach(k => { if (k && k.length > 2) kwCounts[k] = (kwCounts[k] || 0) + 1; });

      // CTAs
      const c = p.cta;
      if (c && c.length > 2) ctaCounts[c] = (ctaCounts[c] || 0) + 1;

      // Content type heuristic
      const txt = (p.text_content || p.content || '').toLowerCase();
      const ct = txt.includes('%') || txt.includes('off') || txt.includes('discount') ? 'Offer/Promo'
               : txt.includes('new') || txt.includes('launch') || txt.includes('arrivals') ? 'New Arrival'
               : txt.includes('tip') || txt.includes('guide') || txt.includes('how') ? 'Educational'
               : txt.includes('event') || txt.includes('festival') ? 'Event/Seasonal'
               : 'General Update';
      contentTypeCounts[ct] = (contentTypeCounts[ct] || 0) + 1;
    });

    const topTopics = Object.entries(topicCounts).sort((a,b) => b[1]-a[1]).slice(0,5);
    const topKws    = Object.entries(kwCounts).sort((a,b) => b[1]-a[1]).slice(0,10);
    const topCTAs   = Object.entries(ctaCounts).sort((a,b) => b[1]-a[1]).slice(0,4);
    const ctypes    = Object.entries(contentTypeCounts).sort((a,b) => b[1]-a[1]);
    const postsPerWeek = posts.length > 0 ? (posts.length / Math.max(1, competitorSet.size) / 4).toFixed(1) : 0;

    el.innerHTML = `
      <div class="space-y-4">
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div>
            <h3 class="text-base font-bold font-serif text-sand-900">Content Intelligence</h3>
            <p class="text-xs text-sand-500 mt-0.5">Derived from ${posts.length} scraped competitor posts across ${competitorSet.size} rivals</p>
          </div>
          <span class="text-[10px] font-semibold uppercase tracking-wider text-sand-400 bg-sand-100 px-2 py-1 rounded-full">${postsPerWeek} posts/wk avg</span>
        </div>

        <!-- 4-col stats grid -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl text-center">
            <p class="text-xl font-bold text-sand-900">${posts.length}</p>
            <p class="text-[10px] text-sand-500 mt-0.5 uppercase tracking-wide">Total Posts</p>
          </div>
          <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl text-center">
            <p class="text-xl font-bold text-sand-900">${competitorSet.size}</p>
            <p class="text-[10px] text-sand-500 mt-0.5 uppercase tracking-wide">Competitors</p>
          </div>
          <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl text-center">
            <p class="text-xl font-bold text-sand-900">${Object.keys(topicCounts).length}</p>
            <p class="text-[10px] text-sand-500 mt-0.5 uppercase tracking-wide">Topics Found</p>
          </div>
          <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl text-center">
            <p class="text-xl font-bold text-sand-900">${Object.keys(kwCounts).length}</p>
            <p class="text-[10px] text-sand-500 mt-0.5 uppercase tracking-wide">Keywords</p>
          </div>
        </div>

        <!-- 3-col breakdown -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <!-- Top Topics -->
          ${topTopics.length > 0 ? `
          <div>
            <p class="text-[10px] font-semibold text-sand-500 uppercase tracking-wider mb-2">Main Topics</p>
            <div class="space-y-1.5">
              ${topTopics.map(([t, f]) => `
                <div class="flex items-center justify-between px-2.5 py-1.5 bg-white border border-[#E8E2D8] rounded-lg">
                  <span class="text-xs text-sand-800 font-medium truncate">${t}</span>
                  <span class="shrink-0 text-[10px] font-bold text-sage-700 bg-[#EBF2EC] px-1.5 py-0.5 rounded-full ml-1">${f}</span>
                </div>`).join('')}
            </div>
          </div>` : ''}

          <!-- Content Types -->
          ${ctypes.length > 0 ? `
          <div>
            <p class="text-[10px] font-semibold text-sand-500 uppercase tracking-wider mb-2">Content Types</p>
            <div class="space-y-1.5">
              ${ctypes.map(([ct, f]) => `
                <div class="flex items-center justify-between px-2.5 py-1.5 bg-white border border-[#E8E2D8] rounded-lg">
                  <span class="text-xs text-sand-800 font-medium">${ct}</span>
                  <span class="shrink-0 text-[10px] font-bold text-[#A66E20] bg-[#FDF6EC] px-1.5 py-0.5 rounded-full ml-1">${f}x</span>
                </div>`).join('')}
            </div>
          </div>` : ''}

          <!-- CTAs & Keywords -->
          <div class="space-y-3">
            ${topCTAs.length > 0 ? `
            <div>
              <p class="text-[10px] font-semibold text-sand-500 uppercase tracking-wider mb-2">Common CTAs</p>
              <div class="flex flex-wrap gap-1.5">
                ${topCTAs.map(([c, f]) => `<span class="px-2 py-0.5 bg-[#FCEFEA] text-[#C8684C] border border-[#F3CEC3] text-[10px] font-medium rounded-full">${c}</span>`).join('')}
              </div>
            </div>` : ''}
            ${topKws.length > 0 ? `
            <div>
              <p class="text-[10px] font-semibold text-sand-500 uppercase tracking-wider mb-2">Top Keywords</p>
              <div class="flex flex-wrap gap-1.5">
                ${topKws.slice(0,8).map(([k, f]) => `<span class="px-2 py-0.5 bg-sand-100 text-sand-700 text-[10px] font-medium rounded-full border border-[#E8E2D8]">${k}</span>`).join('')}
              </div>
            </div>` : ''}
          </div>
        </div>
      </div>`;
  }

  // ── Generate Ideas ─────────────────────────────────────────────────────────
  async function generateIdeas() {
    const count = Math.max(1, Math.min(50, parseInt(ideasCountEl?.value) || 3));
    const isComplete = completeToggle?.checked;

    currentProjectId = await resolveProjectId() || currentProjectId;
    if (!currentProjectId) {
      showToast('Select a project first', 'warning');
      return;
    }

    ideasLoadingEl?.classList.remove('hidden');
    ideasResultsEl.innerHTML = '';
    generateIdeasBtn.disabled = true;
    generateIdeasBtn.innerHTML = `
      <svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
      </svg>
      Generating ${count} Ideas...`;

    try {
      let ideas = [];
      if (isComplete) {
        const res = await api.generateCompleteUpdate(currentProjectId);
        ideas = [res.update || res];
      } else {
        const res = await api.generateIdeas(currentProjectId, count);
        ideas = res.ideas || [];
      }

      // Filter out any that are too similar to existing (dedup)
      const fresh = ideas.filter(idea => {
        const text = (idea.update_text || idea.idea_text || '').toLowerCase().trim();
        if (!text) return false;
        return !existingIdeaTexts.some(existing => {
          const e = existing.toLowerCase().trim();
          // Simple similarity check: if >70% words match, skip
          const newWords  = new Set(text.split(/\s+/).filter(w => w.length > 3));
          const existingWords = new Set(e.split(/\s+/).filter(w => w.length > 3));
          const intersection = [...newWords].filter(w => existingWords.has(w)).length;
          const union = Math.max(newWords.size, existingWords.size, 1);
          return intersection / union > 0.65;
        });
      });

      if (fresh.length === 0 && ideas.length > 0) {
        // All ideas were duplicates — regenerate or show warning
        ideasResultsEl.innerHTML = `
          <div class="col-span-2 py-8 text-center text-xs text-sand-500">
            <svg width="20" height="20" class="mx-auto mb-2 text-amber-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            All generated ideas were similar to previously created ones. Try increasing the count or clearing previous ideas to get fresh content.
          </div>`;
        return;
      }

      renderNewIdeas(fresh.length > 0 ? fresh : ideas);

      // Track new idea texts
      (fresh.length > 0 ? fresh : ideas).forEach(i => {
        const t = i.update_text || i.idea_text || '';
        if (t && !existingIdeaTexts.includes(t)) existingIdeaTexts.push(t);
      });

      // Reload previous ideas to keep log in sync
      await loadPreviousIdeas();

    } catch (err) {
      console.error('Error generating ideas:', err);
      ideasResultsEl.innerHTML = `
        <div class="col-span-2 py-8 text-center">
          <p class="text-xs text-red-600 font-medium">Generation failed: ${err.message}</p>
          <p class="text-[10px] text-sand-500 mt-1">Check that your AI API key is set in .env and competitors have been scraped.</p>
        </div>`;
    } finally {
      ideasLoadingEl?.classList.add('hidden');
      generateIdeasBtn.disabled = false;
      generateIdeasBtn.innerHTML = `
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
        Generate Content Ideas`;
    }
  }

  // ── Render New Ideas (Generated) ───────────────────────────────────────────
  function renderNewIdeas(ideas) {
    if (!ideasResultsEl || !ideas?.length) return;

    ideasResultsEl.innerHTML = ideas.map((idea, idx) => {
      const text         = idea.update_text || idea.idea_text || '';
      const kws          = normalizeKeywords(idea.keywords || idea.detected_keywords);
      const cta          = idea.cta || '';
      const imageConc    = idea.image_concept || '';
      const suggestTime  = idea.suggested_posting_time || '';
      const mainTopic    = idea.detected_topic || kws[0] || '';
      const charCount    = text.length;

      return `
        <div class="flex flex-col gap-0 bg-white border border-[#E8E2D8] rounded-2xl shadow-xs hover:shadow-md hover:border-[#D4CFC6] transition-all duration-200 overflow-hidden" id="idea-card-${idx}">
          <!-- Card Header -->
          <div class="flex items-center justify-between px-5 pt-5 pb-3 border-b border-[#F0EAE0]">
            <div class="flex items-center gap-2">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-[#DE7E63] to-[#B0553B] flex items-center justify-center text-white text-[11px] font-bold shadow-inner">
                ${idx + 1}
              </div>
              <span class="text-[10px] font-bold uppercase tracking-widest text-[#C8684C]">Content Idea</span>
              ${mainTopic ? `<span class="text-[10px] text-sand-500 border border-[#E8E2D8] px-2 py-0.5 rounded-full">${mainTopic}</span>` : ''}
            </div>
            <span class="text-[10px] text-sand-400">${charCount} chars</span>
          </div>

          <!-- Post Text -->
          <div class="px-5 py-4">
            <p class="text-sm text-sand-900 leading-relaxed font-medium">${text}</p>
          </div>

          <!-- Metadata Rows -->
          <div class="px-5 pb-4 space-y-3">
            <!-- Keywords -->
            ${kws.length > 0 ? `
            <div class="flex flex-wrap items-center gap-1.5">
              <span class="text-[10px] font-semibold text-sand-500 uppercase tracking-wider mr-1">Keywords</span>
              ${kws.slice(0, 6).map(k => `<span class="px-2 py-0.5 bg-[#EBF2EC] text-[#5E7E62] text-[10px] font-medium rounded-full border border-[#C8DBCB]">#${k}</span>`).join('')}
            </div>` : ''}

            <!-- CTA + Posting Time row -->
            <div class="flex flex-wrap gap-3">
              ${cta ? `
              <div class="flex items-center gap-1.5 px-3 py-1.5 bg-[#FCEFEA] border border-[#F3CEC3] rounded-lg">
                <svg width="11" height="11" fill="none" stroke="#C8684C" stroke-width="2.2" viewBox="0 0 24 24"><polyline points="15 10 20 15 15 20"/><path d="M4 4v7a4 4 0 004 4h12"/></svg>
                <span class="text-[10px] font-semibold text-[#C8684C]">CTA: ${cta}</span>
              </div>` : ''}
              ${suggestTime ? `
              <div class="flex items-center gap-1.5 px-3 py-1.5 bg-sand-100 border border-[#E8E2D8] rounded-lg">
                <svg width="11" height="11" fill="none" stroke="#8C8479" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                <span class="text-[10px] font-medium text-sand-600">${suggestTime}</span>
              </div>` : ''}
            </div>

            <!-- Image Concept -->
            ${imageConc ? `
            <div class="flex items-start gap-2 px-3 py-2.5 bg-[#F5F1EA] border border-[#E8E2D8] rounded-xl">
              <svg width="14" height="14" class="shrink-0 mt-0.5 text-sand-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <div>
                <p class="text-[10px] font-semibold text-sand-500 uppercase tracking-wider mb-0.5">Image Concept</p>
                <p class="text-xs text-sand-700">${imageConc}</p>
              </div>
            </div>` : ''}
          </div>

          <!-- Action Footer -->
          <div class="flex items-center gap-2 px-5 py-3 bg-[#FAF8F5] border-t border-[#F0EAE0]">
            <button class="copy-idea-btn flex-1 px-3 py-1.5 bg-sage-600 hover:bg-sage-700 text-white text-xs font-semibold rounded-lg transition-colors flex items-center justify-center gap-1.5"
                    data-text="${encodeURIComponent(text)}">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              Copy Post
            </button>
            <button class="use-idea-btn px-3 py-1.5 bg-white border border-[#E8E2D8] hover:bg-sand-50 text-sand-700 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5"
                    data-idea-idx="${idx}" data-text="${encodeURIComponent(text)}">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
              Mark Used
            </button>
          </div>
        </div>`;
    }).join('');

    // Wire up copy + mark-used buttons
    ideasResultsEl.querySelectorAll('.copy-idea-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = decodeURIComponent(btn.dataset.text);
        if (navigator.clipboard) navigator.clipboard.writeText(text);
        const orig = btn.innerHTML;
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.innerHTML = orig; }, 1800);
        showToast('Post copied to clipboard', 'success');
      });
    });

    ideasResultsEl.querySelectorAll('.use-idea-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        try {
          await api.markIdeaUsed(btn.dataset.ideaIdx);
          btn.closest('[id^="idea-card"]')?.remove();
          showToast('Marked as used', 'success');
          await loadPreviousIdeas();
        } catch (e) {
          showToast('Error: ' + e.message, 'error');
        }
      });
    });
  }

  // ── Render Previous Ideas ──────────────────────────────────────────────────
  async function loadPreviousIdeas() {
    try {
      const res = await api.getGeneratedIdeas(currentProjectId);
      renderPreviousIdeas(res.ideas || []);
    } catch (e) {
      console.warn('loadPreviousIdeas error:', e);
    }
  }

  function renderPreviousIdeas(ideas) {
    if (!previousIdeasEl) return;

    if (!ideas?.length) {
      previousIdeasEl.innerHTML = `<p class="text-xs text-sand-500 text-center py-4">No previously generated ideas for this project.</p>`;
      return;
    }

    previousIdeasEl.innerHTML = ideas.map((idea, idx) => {
      const text = idea.idea_text || idea.update_text || '';
      const used = !!idea.used_flag;
      const date = formatDate(idea.generated_at);
      return `
        <div class="flex items-start gap-3 px-4 py-3 bg-white border border-[#E8E2D8] rounded-xl hover:bg-[#FAF8F5] transition-colors">
          <div class="shrink-0 w-1 h-full min-h-[32px] rounded ${used ? 'bg-sage-400' : 'bg-amber-400'} mt-1"></div>
          <div class="flex-1 min-w-0">
            <p class="text-xs text-sand-800 line-clamp-2 leading-relaxed">${text}</p>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-[10px] text-sand-400">${date}</span>
              <span class="text-[10px] font-semibold ${used ? 'text-sage-600' : 'text-amber-600'}">${used ? 'Used' : 'Unused'}</span>
            </div>
          </div>
          <button class="shrink-0 px-2 py-1 bg-sand-100 hover:bg-sand-200 text-sand-600 text-[10px] font-semibold rounded-lg transition-colors copy-prev-btn" data-text="${encodeURIComponent(text)}">
            Copy
          </button>
        </div>`;
    }).join('');

    previousIdeasEl.querySelectorAll('.copy-prev-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = decodeURIComponent(btn.dataset.text);
        if (navigator.clipboard) navigator.clipboard.writeText(text);
        showToast('Copied', 'success');
      });
    });
  }

  // ── Helpers ────────────────────────────────────────────────────────────────
  function normalizeKeywords(raw) {
    if (!raw) return [];
    if (Array.isArray(raw)) return raw.filter(k => typeof k === 'string' && k.length > 1).slice(0, 8);
    if (typeof raw === 'string') {
      try { return normalizeKeywords(JSON.parse(raw)); } catch { return []; }
    }
    return [];
  }

  function formatDate(d) {
    if (!d) return '';
    try { return new Date(d).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
    catch { return ''; }
  }

  function showToast(msg, type = 'info') {
    if (window.showToast) window.showToast(msg, type);
  }

  // ── Event Listeners ────────────────────────────────────────────────────────
  function setupEventListeners() {
    generateIdeasBtn?.addEventListener('click', generateIdeas);
    projectSelectEl?.addEventListener('change', async () => {
      currentProjectId = await resolveProjectId();
      loadAll();
    });
    ideasCountEl?.addEventListener('keypress', e => { if (e.key === 'Enter') generateIdeas(); });

    // Quick count preset buttons (3, 10, 50)
    document.querySelectorAll('.ideas-preset-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const c = parseInt(btn.dataset.count) || 3;
        if (ideasCountEl) ideasCountEl.value = c;
        document.querySelectorAll('.ideas-preset-btn').forEach(b => {
          const isActive = b === btn;
          b.classList.toggle('bg-white', isActive);
          b.classList.toggle('shadow-xs', isActive);
          b.classList.toggle('text-[#C8684C]', isActive);
        });
      });
    });
  }

  // Start
  init();
}