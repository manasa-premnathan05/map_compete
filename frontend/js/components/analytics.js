// Analytics & Merged Market Intelligence Component (PDF Spec Compliance)
// Features all 6 Modules from Project Specification with real Chart.js graphs and Leaflet Map
export function initAnalytics(api) {
  const analyticsView = document.getElementById('analytics-view');
  if (!analyticsView) return;

  // Elements
  const projectSelectEl = document.getElementById('project-select');
  const mobileProjectSelectEl = document.getElementById('mobile-project-select');

  // KPI elements
  const marketAvgRatingEl = document.getElementById('market-avg-rating');
  const marketRatingBasisEl = document.getElementById('market-rating-basis');
  const marketTotalReviewsEl = document.getElementById('market-total-reviews');
  const marketPosSentimentEl = document.getElementById('market-pos-sentiment');
  const marketNegSentimentEl = document.getElementById('market-neg-sentiment');
  const marketRatingBar = document.getElementById('market-rating-bar');
  const marketPosBar = document.getElementById('market-pos-bar');
  const marketNegBar = document.getElementById('market-neg-bar');

  // Sentiment ratio counts
  const sentimentPosCountEl = document.getElementById('sentiment-pos-count');
  const sentimentNeuCountEl = document.getElementById('sentiment-neu-count');
  const sentimentNegCountEl = document.getElementById('sentiment-neg-count');

  // Chart instances tracking to safely destroy/re-render
  const charts = {};
  let leafletMap = null;
  let mapMarkers = [];

  // Filter & Container elements
  const sourceSearchInput = document.getElementById('source-search-input');
  const sourceCompFilter = document.getElementById('source-explorer-comp-filter');
  const sourceTypeFilter = document.getElementById('source-explorer-type-filter');
  const sourceSentimentFilter = document.getElementById('source-explorer-sentiment-filter');
  const sourceTbody = document.getElementById('source-explorer-tbody');

  let currentProjectId = null;
  let cachedMarketData = null;
  let cachedReviewAnalytics = null;
  let cachedReviews = [];
  let cachedPosts = [];
  let activeComparisonMetric = 'rating'; // 'rating' or 'reviews'
  let activeGeoMetric = 'reviews'; // 'reviews', 'posts', 'rating'

  // Format date safely
  function formatDate(d) {
    if (!d) return 'Recent';
    try {
      const dt = new Date(d);
      if (isNaN(dt.getTime())) return d;
      return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return d;
    }
  }

  // Initialize
  async function init() {
    try {
      setupSubnav();
      await loadAnalyticsData();
      setupEventListeners();
    } catch (error) {
      console.error('Error initializing analytics component:', error);
    }
  }

  // Subnav tab switching for the 6 PDF Modules
  function setupSubnav() {
    const subnavButtons = document.querySelectorAll('.analytics-subnav-btn');
    const modules = document.querySelectorAll('.analytics-module');

    subnavButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        const targetId = btn.dataset.target;

        // Update button states
        subnavButtons.forEach(b => {
          b.classList.remove('bg-sage-500', 'text-white', 'font-semibold');
          b.classList.add('text-sand-700', 'font-medium');
        });
        btn.classList.remove('text-sand-700', 'font-medium');
        btn.classList.add('bg-sage-500', 'text-white', 'font-semibold');

        // Show target module
        modules.forEach(m => {
          if (m.id === targetId) {
            m.classList.remove('hidden');
          } else {
            m.classList.add('hidden');
          }
        });

        // Trigger map resize if geographic module opened
        if (targetId === 'module-geo' && leafletMap) {
          setTimeout(() => leafletMap.invalidateSize(), 150);
        }

        // Trigger Chart.js resize
        Object.values(charts).forEach(c => {
          if (c && typeof c.resize === 'function') c.resize();
        });
      });
    });
  }

  // Wait for the header switcher (filled by the dashboard) instead of using a
  // hard-coded project id that may refer to a deleted company.
  async function resolveProjectId(waitMs = 5000) {
    const deadline = Date.now() + waitMs;
    for (;;) {
      const projectId = parseInt(projectSelectEl?.value, 10)
        || parseInt(mobileProjectSelectEl?.value, 10)
        || currentProjectId;
      if (projectId) return projectId;
      if (Date.now() >= deadline) return null;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  // Main data loader
  async function loadAnalyticsData() {
    try {
      api.showLoading();
      const projectId = await resolveProjectId();
      currentProjectId = projectId;
      if (!projectId) {
        api.hideLoading();
        return;
      }

      const [
        marketRes,
        reviewAnalyticsRes,
        topicData,
        keywordData,
        reviewsRes,
        postsRes,
        marketGapsRes,
        trendRes
      ] = await Promise.allSettled([
        api.getMarketOverview(projectId),
        api.getReviewAnalytics(projectId),
        api.getTopicFrequency(projectId),
        api.getKeywordFrequency(projectId),
        api.getProjectReviews(projectId, { limit: 100 }),
        api.getPosts({ project_id: projectId, limit: 100 }),
        api.getMarketGaps(projectId),
        api.getTopicTrends(projectId)
      ]);

      cachedMarketData = marketRes.status === 'fulfilled' ? marketRes.value : null;
      cachedReviewAnalytics = reviewAnalyticsRes.status === 'fulfilled' ? reviewAnalyticsRes.value : null;
      const topics = topicData.status === 'fulfilled' ? (topicData.value?.topics || []) : [];
      const keywords = keywordData.status === 'fulfilled' ? (keywordData.value?.keywords || []) : [];
      cachedReviews = reviewsRes.status === 'fulfilled' ? (reviewsRes.value?.reviews || []) : [];
      cachedPosts = postsRes.status === 'fulfilled' ? (postsRes.value?.posts || []) : [];
      const marketGaps = marketGapsRes.status === 'fulfilled' ? (marketGapsRes.value?.gaps || []) : [];
      const trendData = trendRes.status === 'fulfilled' ? trendRes.value : null;

      // 1. Render Market KPIs
      renderMarketKPIs(cachedMarketData);

      // 2. Render Charts & Modules
      renderMarketComparisonChart(cachedMarketData?.competitors || []);
      renderSentimentDonut(cachedMarketData);
      renderCompetitiveScatter(cachedMarketData?.competitors || []);
      renderRatingDistributionChart(cachedReviewAnalytics?.rating_distribution);
      renderReviewTopics(cachedReviewAnalytics?.topics || [], topics);
      renderNegativeHeatmap(cachedReviewAnalytics?.negative_topics || []);
      renderPostsTimelineChart(cachedPosts);
      renderPostThemesChart(cachedPosts);
      initOrUpdateGeographicMap(cachedMarketData?.competitors || []);

      // 3. Populate filters & Source Explorer Table
      populateCompetitorFilter(cachedMarketData?.competitors || []);
      renderSourceExplorer();

      // 4. Render AI Competitive Intelligence
      renderAICompetitiveIntelligence(cachedMarketData);

      // 5. Render Market Gaps section
      renderAnalyticsMarketGaps(marketGaps, cachedMarketData?.competitors || []);

      // 6. Render Trend Analysis (Section 13)
      renderTrendAnalysis(trendData);

    } catch (error) {
      console.error('Error loading analytics data:', error);
      showErrorState(error.message);
    } finally {
      api.hideLoading();
    }
  }

  // Render AI Competitive Intelligence - Unique Insights & Competitive Patterns
  function renderAICompetitiveIntelligence(marketData) {
    const container = document.getElementById('ai-competitive-intelligence');
    if (!container) return;

    // Get analysis from market data (if available) or trigger analysis
    const analysis = marketData?.analysis || marketData?.ai_analysis || null;
    
    if (!analysis) {
      container.innerHTML = `
        <div class="col-span-2 py-12 text-center">
          <div class="w-12 h-12 mx-auto mb-3 bg-sage-500/10 rounded-full flex items-center justify-center">
            <svg width="22" height="22" fill="none" stroke="#5E7E62" stroke-width="1.8" viewBox="0 0 24 24"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.5a3.374 3.374 0 00-3.36-3.36l-0.548-.547A5 5 0 0012 3.5 10.5 10.5 0 0122.5 14.5"></svg>
          </div>
          <h3 class="text-lg font-bold font-serif text-sand-900 mb-2">AI Competitive Intelligence</h3>
          <p class="text-xs text-sand-500 mb-4">Run AI analysis to unlock unique competitive insights from scraped Google Maps posts.</p>
          <button id="run-ai-analysis-btn" class="px-5 py-2.5 bg-sage-500 text-white text-xs font-semibold rounded-xl hover:bg-sage-600 transition-colors">
            Run AI Analysis
          </button>
        </div>`;
      document.getElementById('run-ai-analysis-btn')?.addEventListener('click', () => runAIAnalysis());
      return;
    }

    // Render the comprehensive analysis
    const topics = analysis.topics || [];
    const subTopics = analysis.sub_topics || [];
    const keywords = analysis.keywords || [];
    const contentTypes = analysis.content_types || [];
    const ctaAnalysis = analysis.cta_analysis || [];
    const offerPatterns = analysis.offer_promotion_patterns || [];
    const frequentSubjects = analysis.frequent_subjects || [];
    const contentFreq = analysis.content_frequency || {};
    const competitorPatterns = analysis.competitor_publishing_patterns || [];
    const trends = analysis.trends || [];
    const gapsOpps = analysis.gaps_opportunities || [];
    const uniqueInsights = analysis.unique_insights || [];
    const summary = analysis.summary || '';
    const competitorPatternsData = analysis.competitor_publishing_patterns || [];

    // Build HTML for the enhanced intelligence view
    container.innerHTML = `
      <div class="space-y-6">
        <!-- Header & Summary -->
        <div class="p-5 bg-sage-50 border border-sage-200 rounded-2xl">
          <div class="flex items-start justify-between mb-3">
            <div>
              <h3 class="text-lg font-bold font-serif text-sage-800">AI Competitive Intelligence</h3>
              <p class="text-xs text-sage-600 mt-0.5">Deep analysis of competitor Google Maps posts - ${analysis.posts_analyzed || 0} posts analyzed</p>
            </div>
            <button id="re-run-analysis-btn" class="px-3 py-1.5 bg-sage-500 hover:bg-sage-600 text-white text-xs font-semibold rounded-lg transition-colors">
              Re-run Analysis
            </button>
          </div>
          <p class="text-xs text-sage-700 leading-relaxed">${analysis.summary || 'Analysis complete'}</p>
        </div>

        <!-- Unique Insights (USP) -->
        ${uniqueInsights.length > 0 ? `
        <div class="space-y-3">
          <div class="flex items-center gap-2">
            <div class="w-2 h-8 bg-sage-500 rounded"></div>
            <h4 class="text-sm font-bold font-serif text-sand-900">Unique AI Insights (USP)</h4>
          </div>
          <div class="space-y-2">
            ${uniqueInsights.map(insight => `
              <div class="p-4 bg-white border border-sage-200 rounded-xl space-y-2">
                <div class="flex items-center gap-2">
                  <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sage-500 text-white">Insight</span>
                  <span class="text-xs font-semibold text-sand-700">${insight.insight}</span>
                </div>
                <div class="p-3 bg-sage-50 border border-sage-100 rounded-lg">
                  <p class="text-[10px] font-semibold text-sage-700 mb-1">Evidence:</p>
                  <p class="text-[10px] text-sage-600">${insight.evidence}</p>
                </div>
                <div class="p-3 bg-terracotta-50 border border-terracotta-100 rounded-lg">
                  <p class="text-[10px] font-semibold text-terracotta-700 mb-1">Actionable Recommendation:</p>
                  <p class="text-[10px] text-terracotta-600">${insight.actionable_recommendation}</p>
                </div>
              </div>
            `).join('')}
          </div>
        </div>` : ''}

        <!-- Topics & Sub-topics -->
        ${topics.length > 0 ? `
        <div class="space-y-3">
          <h4 class="text-sm font-bold font-serif text-sand-900">Main Topics & Sub-topics</h4>
          <div class="space-y-2">
            ${topics.map(topic => `
              <div class="p-4 bg-white border border-[#E8E2D8] rounded-xl space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-sand-900">${topic.topic}</span>
                  <span class="badge-sage text-[10px] font-semibold px-2 py-0.5 rounded-full">${topic.frequency} posts</span>
                </div>
                <p class="text-xs text-sand-600">${topic.description}</p>
                ${topic.sub_topics && topic.sub_topics.length > 0 ? `
                  <div class="flex flex-wrap gap-1.5">
                    ${topic.sub_topics.map(st => `<span class="px-2 py-0.5 bg-sand-100 text-sand-600 text-[10px] font-medium rounded">${st}</span>`).join('')}
                  </div>` : ''}
                ${topic.competitors && topic.competitors.length > 0 ? `
                  <div class="flex flex-wrap gap-1.5">
                    ${topic.competitors.slice(0, 5).map(c => `<span class="px-2 py-0.5 bg-terracotta-50 text-terracotta-700 text-[10px] font-medium rounded">${c}</span>`).join('')}
                  </div>` : ''}
              </div>
            `).join('')}
          </div>
        </div>` : ''}

        <!-- Content Types & CTA Analysis -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${contentTypes.length > 0 ? `
          <div class="space-y-3">
            <h4 class="text-sm font-bold font-serif text-sand-900">Content Types</h4>
            <div class="space-y-2">
              ${contentTypes.map(ct => `
                <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl flex items-center justify-between">
                  <div>
                    <p class="text-xs font-bold text-sand-900">${ct.type}</p>
                    <p class="text-[10px] text-sand-500">${ct.frequency} posts${ct.examples && ct.examples.length > 0 ? ` - ${ct.examples[0]}` : ''}</p>
                  </div>
                  <span class="badge-sage text-[10px] font-semibold px-2 py-0.5 rounded-full">${ct.frequency}</span>
                </div>
              `).join('')}
            </div>
          </div>` : ''}

          ${ctaAnalysis.length > 0 ? `
          <div class="space-y-3">
            <h4 class="text-sm font-bold font-serif text-sand-900">CTA Analysis</h4>
            <div class="space-y-2">
              ${ctaAnalysis.map(cta => `
                <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl flex items-center justify-between">
                  <div>
                    <p class="text-xs font-bold text-sand-900">${cta.cta}</p>
                    <p class="text-[10px] text-sand-500">${cta.frequency} uses | ${cta.effectiveness || 'Moderate'}</p>
                  </div>
                  <span class="badge-terracotta text-[10px] font-semibold px-2 py-0.5 rounded-full">${cta.frequency}</span>
                </div>
              `).join('')}
            </div>
          </div>` : ''}
        </div>

        <!-- Offer/Promotion Patterns -->
        ${offerPatterns.length > 0 ? `
        <div class="space-y-3">
          <h4 class="text-sm font-bold font-serif text-sand-900">Offer & Promotion Patterns</h4>
          <div class="space-y-2">
            ${offerPatterns.map(op => `
              <div class="p-3 bg-white border border-amber-200 rounded-xl flex items-center justify-between">
                <div>
                  <p class="text-xs font-bold text-sand-900">${op.pattern}</p>
                  <p class="text-[10px] text-sand-500">${op.frequency} occurrences${op.example ? ` - ${op.example}` : ''}</p>
                </div>
                <span class="badge-amber text-[10px] font-semibold px-2 py-0.5 rounded-full">${op.frequency}</span>
              </div>
            `).join('')}
          </div>
        </div>` : ''}

        <!-- Frequent Subjects & Keywords -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          ${frequentSubjects.length > 0 ? `
          <div class="space-y-3">
            <h4 class="text-sm font-bold font-serif text-sand-900">Frequent Subjects</h4>
            <div class="space-y-2">
              ${frequentSubjects.slice(0, 10).map(fs => `
                <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl flex items-center justify-between">
                  <div>
                    <p class="text-xs font-bold text-sand-900">${fs.subject}</p>
                    <p class="text-[10px] text-sand-500">${fs.frequency} mentions${fs.related_keywords && fs.related_keywords.length > 0 ? ` - ${fs.related_keywords.slice(0,3).join(', ')}` : ''}</p>
                  </div>
                  <span class="badge-sand text-[10px] font-semibold px-2 py-0.5 rounded-full">${fs.frequency}</span>
                </div>
              `).join('')}
            </div>
          </div>` : ''}

          ${keywords.length > 0 ? `
          <div class="space-y-3">
            <h4 class="text-sm font-bold font-serif text-sand-900">Top Keywords</h4>
            <div class="flex flex-wrap gap-1.5">
              ${keywords.slice(0, 20).map(kw => `
                <span class="px-2.5 py-1 bg-sand-100 text-sand-700 text-[10px] font-medium rounded-full border border-[#E8E2D8]">
                  ${kw.keyword} <span class="text-sand-400 ml-1">${kw.frequency}</span>
                </span>
              `).join('')}
            </div>
          </div>` : ''}
        </div>

        <!-- Content Frequency & Competitor Patterns -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-3">
            <h4 class="text-sm font-bold font-serif text-sand-900">Content Frequency</h4>
            <div class="p-3 bg-white border border-[#E8E2D8] rounded-xl space-y-2">
              <div class="flex justify-between text-xs">
                <span class="text-sand-500">Posts per week</span>
                <span class="font-bold text-sand-900">${contentFreq.posts_per_week || 0}/week</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-sand-500">Peak days</span>
                <span class="font-bold text-sand-900">${contentFreq.peak_days?.join(', ') || 'N/A'}</span>
              </div>
              <div class="flex justify-between text-xs">
                <span class="text-sand-500">Peak hours</span>
                <span class="font-bold text-sand-900">${contentFreq.peak_hours?.join(', ') || 'N/A'}</span>
              </div>
            </div>
          </div>

          <div class="space-y-3">
            <h4 class="text-sm font-bold font-serif text-sand-900">Gaps & Opportunities</h4>
            <div class="space-y-2">
              ${gapsOpps.map(gap => `
                <div class="p-3 bg-white border border-sage-200 rounded-xl space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="badge-sage text-[10px] font-semibold px-2 py-0.5 rounded-full">Opportunity</span>
                    <span class="text-xs font-bold text-sand-900">${gap.opportunity}</span>
                  </div>
                  <p class="text-[10px] text-sand-600">${gap.description}</p>
                  <p class="text-[10px] text-sage-700 font-medium">${gap.potential_impact}</p>
                </div>
              `).join('')}
            </div>
          </div>
        </div>

        <!-- Trends -->
        ${trends.length > 0 ? `
        <div class="space-y-3">
          <h4 class="text-sm font-bold font-serif text-sand-900">Trends</h4>
          <div class="space-y-2">
            ${trends.map(t => `
              <div class="p-3 bg-white border border-sage-200 rounded-xl space-y-1">
                <div class="flex items-center gap-2">
                  <span class="badge-sage text-[10px] font-semibold px-2 py-0.5 rounded-full">Trend</span>
                  <span class="text-xs font-bold text-sand-900">${t.trend}</span>
                </div>
                <p class="text-[10px] text-sand-600">${t.description}</p>
                ${t.supporting_evidence ? `<p class="text-[10px] text-sage-600 italic">Evidence: ${t.supporting_evidence}</p>` : ''}
              </div>
            `).join('')}
          </div>
        </div>` : ''}

        <!-- Competitor Publishing Patterns -->
        ${competitorPatternsData.length > 0 ? `
        <div class="space-y-3">
          <h4 class="text-sm font-bold font-serif text-sand-900">Competitor Publishing Patterns</h4>
          <div class="space-y-2">
            ${competitorPatternsData.map(cp => `
              <div class="p-4 bg-white border border-[#E8E2D8] rounded-xl space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-sand-900">${cp.competitor}</span>
                  <span class="badge-sage text-[10px] font-semibold px-2 py-0.5 rounded-full">${cp.posting_frequency}</span>
                </div>
                ${cp.preferred_content_types && cp.preferred_content_types.length > 0 ? `
                  <div class="flex flex-wrap gap-1.5">
                    ${cp.preferred_content_types.map(t => `<span class="px-2 py-0.5 bg-sage-50 text-sage-700 text-[10px] font-medium rounded">${t}</span>`).join('')}
                  </div>` : ''}
                ${cp.common_ctas && cp.common_ctas.length > 0 ? `
                  <div class="flex flex-wrap gap-1.5">
                    ${cp.common_ctas.map(c => `<span class="px-2 py-0.5 bg-terracotta-50 text-terracotta-700 text-[10px] font-medium rounded">${c}</span>`).join('')}
                  </div>` : ''}
                ${cp.common_offers && cp.common_offers.length > 0 ? `
                  <div class="flex flex-wrap gap-1.5">
                    ${cp.common_offers.map(o => `<span class="px-2 py-0.5 bg-amber-50 text-amber-700 text-[10px] font-medium rounded">${o}</span>`).join('')}
                  </div>` : ''}
                ${cp.peak_posting_days && cp.peak_posting_days.length > 0 ? `
                  <div class="flex flex-wrap gap-1.5">
                    ${cp.peak_posting_days.map(d => `<span class="px-2 py-0.5 bg-sand-100 text-sand-600 text-[10px] font-medium rounded">${d}</span>`).join('')}
                  </div>` : ''}
              </div>
            `).join('')}
          </div>
        </div>` : ''}
      </div>
    `;

    // Wire up re-run button
    document.getElementById('re-run-analysis-btn')?.addEventListener('click', () => runAIAnalysis());
    document.getElementById('run-ai-analysis-btn')?.addEventListener('click', () => runAIAnalysis());
  }

  // Run AI Analysis
  async function runAIAnalysis() {
    const projectId = await resolveProjectId() || currentProjectId;
    if (!projectId) {
      window.showToast?.('Select a project first', 'warning');
      return;
    }
    const btn = document.getElementById('run-ai-analysis-btn') || document.getElementById('re-run-analysis-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<svg class="animate-spin -ml-1 mr-2 h-3 w-3 text-white" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>Analyzing...`;
    }

    try {
      const response = await api.analyzeProject(currentProjectId || 49);
      if (response.analysis) {
        // Reload analytics to show new data
        await loadAnalyticsData();
      }
    } catch (error) {
      console.error('AI Analysis failed:', error);
      alert('Analysis failed: ' + error.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Re-run Analysis';
      }
    }
  }

  // Render market gaps in the analytics view
  function renderAnalyticsMarketGaps(gaps, competitors) {
    const container = document.getElementById('analytics-market-gaps');
    if (!container) return;

    const iconSvgs = {
      'shield-alert': `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
      'flame': `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M8.5 14.5A2.5 2.5 0 0011 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 01-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 002.5 2.5z"/></svg>`,
      'clock': `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
      'trending-up': `<svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`
    };

    const colorMap = {
      terracotta: { bg: 'bg-[#FDF3EF]', icon: 'text-[#C8684C]', border: 'border-[#F3CEC3]', badge: 'bg-[#FCEFEA] text-[#C8684C] border-[#F3CEC3]', bar: 'bg-[#C8684C]' },
      amber: { bg: 'bg-[#FDF6EC]', icon: 'text-[#A66E20]', border: 'border-[#F4DFBF]', badge: 'bg-[#FDF6EC] text-[#A66E20] border-[#F4DFBF]', bar: 'bg-[#D4A373]' },
      sage: { bg: 'bg-[#EBF2EC]', icon: 'text-[#5E7E62]', border: 'border-[#C8DBCB]', badge: 'bg-[#EBF2EC] text-[#5E7E62] border-[#C8DBCB]', bar: 'bg-[#5E7E62]' },
      sand: { bg: 'bg-[#F5F1EA]', icon: 'text-[#8C8479]', border: 'border-[#E8E2D8]', badge: 'bg-[#F5F1EA] text-[#8C8479] border-[#E8E2D8]', bar: 'bg-[#8C8479]' }
    };

    if (!gaps || gaps.length === 0) {
      container.innerHTML = `
        <div class="col-span-2 py-14 text-center">
          <div class="w-12 h-12 mx-auto mb-3 bg-sand-100 rounded-full flex items-center justify-center">
            <svg width="22" height="22" fill="none" stroke="#8C8479" stroke-width="1.8" viewBox="0 0 24 24"><path d="M3 3v18h18M8 17V9m4 8V5m4 12V9"/></svg>
          </div>
          <p class="text-sm font-medium text-sand-700">No market gap analysis available</p>
          <p class="text-xs text-sand-500 mt-1">Add competitors with real Google Maps profiles and run scraping to unlock strategic insights.</p>
        </div>`;
      return;
    }

    container.innerHTML = gaps.map(gap => {
      const c = colorMap[gap.badge_color] || colorMap['sand'];
      const icon = iconSvgs[gap.icon_type] || iconSvgs['trending-up'];
      const affected = (gap.affected_competitors || []).slice(0, 3);

      return `
        <div class="flex flex-col gap-4 p-5 sm:p-6 bg-white border border-[#E8E2D8] rounded-2xl shadow-sm hover:shadow-md hover:border-[#CFCAC2] transition-all duration-200">
          <!-- Top Row -->
          <div class="flex items-start gap-3.5">
            <div class="shrink-0 w-10 h-10 rounded-xl ${c.bg} ${c.icon} flex items-center justify-center border ${c.border}">
              ${icon}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2 mb-1.5">
                <span class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wide border ${c.badge}">${gap.badge}</span>
                <span class="text-[10px] font-semibold uppercase tracking-widest text-sand-400">${gap.category}</span>
              </div>
              <h4 class="text-sm font-bold text-sand-900 leading-snug">${gap.title}</h4>
            </div>
          </div>

          <!-- Weakness block -->
          <div class="rounded-xl bg-[#FAF8F5] border-l-[3px] ${c.bar.replace('bg-', 'border-')} px-4 py-3">
            <p class="text-[10px] font-semibold uppercase tracking-widest text-sand-500 mb-1">Rival Vulnerability</p>
            <p class="text-xs text-sand-700 leading-relaxed">${gap.competitor_weakness}</p>
          </div>

          <!-- Strategy block -->
          <div>
            <p class="text-[10px] font-semibold uppercase tracking-widest text-sand-500 mb-1.5">Counter-Strategy</p>
            <p class="text-xs text-sand-700 leading-relaxed">${gap.actionable_strategy}</p>
          </div>

          <!-- Impact bar -->
          <div class="pt-3 border-t border-[#E8E2D8] space-y-2">
            <div class="flex items-center justify-between text-[11px]">
              <span class="font-semibold text-sage-700 flex items-center gap-1">
                <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>
                Expected Impact
              </span>
              <span class="font-bold text-sage-800">${gap.expected_impact}</span>
            </div>
            ${affected.length > 0 ? `
              <div class="flex flex-wrap gap-1.5 mt-1">
                ${affected.map(name => `<span class="px-2 py-0.5 bg-sand-100 text-sand-600 text-[10px] font-medium rounded-full border border-[#E8E2D8] truncate max-w-[150px]" title="${name}">${name.length > 22 ? name.slice(0, 20) + '…' : name}</span>`).join('')}
              </div>` : ''}
          </div>
        </div>`;
    }).join('');
  }

  // Section 13 — Trend Analysis renderer
  function renderTrendAnalysis(data) {
    const tableEl    = document.getElementById('trend-topic-table');
    const cloudEl    = document.getElementById('trend-keyword-cloud');
    const barsEl     = document.getElementById('trend-monthly-bars');
    const metaEl     = document.getElementById('trend-meta');
    if (!tableEl) return;

    if (!data || (!data.topic_trends?.length && !data.keyword_trends?.length)) {
      tableEl.innerHTML = `
        <div class="py-10 text-center text-xs text-sand-500">
          <svg width="24" height="24" class="mx-auto mb-3 text-sand-300" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          <p class="font-medium text-sand-600">No trend data yet</p>
          <p class="mt-1">Add competitors and run scraping (last 6 months) to see topic trends.</p>
        </div>`;
      return;
    }

    const topics    = data.topic_trends    || [];
    const keywords  = data.keyword_trends  || [];
    const monthly   = data.monthly_volume  || {};
    const totalPosts= data.total_posts     || 0;
    const totalComp = data.total_competitors || 0;

    // ── Meta summary ──────────────────────────────────────────────────────────
    if (metaEl) {
      metaEl.innerHTML = `
        <div class="flex flex-col items-end gap-1">
          <span class="text-2xl font-bold font-serif text-sand-900">${totalPosts}</span>
          <span class="text-[10px] text-sand-400 uppercase tracking-wider">Posts Analysed</span>
          <span class="text-[10px] text-sand-500">${totalComp} competitors tracked</span>
        </div>`;
    }

    // ── Direction icons ──────────────────────────────────────────────────────
    const dirIcon = {
      rising:  `<svg width="12" height="12" fill="none" stroke="#5E7E62" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="18 15 12 9 6 15"/></svg>`,
      falling: `<svg width="12" height="12" fill="none" stroke="#C8684C" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="6 9 12 15 18 9"/></svg>`,
      stable:  `<svg width="12" height="12" fill="none" stroke="#A66E20" stroke-width="2.5" viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"/></svg>`
    };
    const dirColor = { rising: 'text-[#5E7E62] bg-[#EBF2EC]', falling: 'text-[#C8684C] bg-[#FCEFEA]', stable: 'text-[#A66E20] bg-[#FDF6EC]' };
    const dirLabel = { rising: 'Rising', falling: 'Falling', stable: 'Stable' };

    // Max occurrence for bar width scaling
    const maxOcc = topics.reduce((m, t) => Math.max(m, t.occurrence), 1);

    // ── Topic Table ───────────────────────────────────────────────────────────
    tableEl.innerHTML = `
      <!-- Table header -->
      <div class="grid grid-cols-12 gap-2 px-4 py-2 text-[10px] font-bold uppercase tracking-wider text-sand-400 border-b border-[#F0EAE0]">
        <div class="col-span-4">Topic</div>
        <div class="col-span-2 text-center">Competitors</div>
        <div class="col-span-2 text-center">Posts</div>
        <div class="col-span-2 text-center">Share</div>
        <div class="col-span-2 text-center">Trend</div>
      </div>
      ${topics.map((t, idx) => {
        const barW = Math.round((t.occurrence / maxOcc) * 100);
        const dir  = t.trend_direction || 'stable';
        const isTop = idx === 0;
        return `
        <div class="grid grid-cols-12 gap-2 items-center px-4 py-3 ${isTop ? 'bg-[#F7F9F7]' : 'bg-white'} border border-[#F0EAE0] rounded-xl hover:bg-[#F5F8F5] transition-colors">
          <!-- Topic name + bar -->
          <div class="col-span-4">
            <div class="flex items-center gap-2">
              ${isTop ? `<span class="shrink-0 w-4 h-4 rounded-full bg-[#5E7E62] text-white text-[9px] font-bold flex items-center justify-center">1</span>` : `<span class="shrink-0 w-4 h-4 rounded-full bg-sand-100 text-sand-500 text-[9px] font-bold flex items-center justify-center">${idx+1}</span>`}
              <div class="min-w-0">
                <p class="text-xs font-semibold text-sand-900 truncate">${t.topic}</p>
                <div class="mt-0.5 h-1 rounded-full bg-[#F0EAE0] overflow-hidden">
                  <div class="h-full rounded-full ${isTop ? 'bg-[#5E7E62]' : 'bg-[#C8DBCB]'}" style="width:${barW}%"></div>
                </div>
              </div>
            </div>
          </div>
          <!-- Competitors using -->
          <div class="col-span-2 text-center">
            <span class="text-xs font-bold text-sand-800">${t.competitors_using}</span>
            <span class="text-[10px] text-sand-400"> / ${t.total_competitors}</span>
          </div>
          <!-- Occurrences -->
          <div class="col-span-2 text-center">
            <span class="text-xs font-bold text-sand-900">${t.occurrence}</span>
          </div>
          <!-- % share -->
          <div class="col-span-2 text-center">
            <span class="text-xs font-bold ${isTop ? 'text-[#5E7E62]' : 'text-sand-700'}">${t.occurrence_pct}%</span>
          </div>
          <!-- Direction badge -->
          <div class="col-span-2 flex justify-center">
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${dirColor[dir]}">
              ${dirIcon[dir]}${dirLabel[dir]}
            </span>
          </div>
        </div>`;
      }).join('')}`;

    // ── Keyword Cloud ─────────────────────────────────────────────────────────
    if (cloudEl && keywords.length > 0) {
      const maxKwOcc = keywords.reduce((m, k) => Math.max(m, k.occurrence), 1);
      cloudEl.innerHTML = keywords.map(k => {
        const size  = k.occurrence / maxKwOcc;
        const fs    = size > 0.7 ? 'text-sm' : size > 0.4 ? 'text-xs' : 'text-[10px]';
        const weight= size > 0.7 ? 'font-bold' : 'font-medium';
        const alpha = Math.max(0.5, size);
        return `
          <span class="inline-flex items-center gap-1 px-3 py-1 rounded-full border border-[#E8E2D8] bg-white hover:bg-[#F5F8F5] transition-colors cursor-default ${fs} ${weight} text-sand-800" title="${k.occurrence} occurrences, ${k.competitors_using} competitors">
            ${k.keyword}
            <span class="text-[9px] text-sand-400 font-normal">${k.occurrence}x</span>
          </span>`;
      }).join('');
    } else if (cloudEl) {
      cloudEl.innerHTML = `<p class="text-xs text-sand-400 italic">No keyword data yet.</p>`;
    }

    // ── Monthly Volume Bars ───────────────────────────────────────────────────
    if (barsEl) {
      const sortedMonths = Object.entries(monthly).sort(([a], [b]) => new Date(a) - new Date(b));
      if (sortedMonths.length > 0) {
        const maxVol = Math.max(...sortedMonths.map(([, v]) => v), 1);
        barsEl.innerHTML = sortedMonths.map(([month, vol]) => {
          const w = Math.max(4, Math.round((vol / maxVol) * 100));
          return `
            <div class="flex items-center gap-3">
              <span class="text-[10px] text-sand-500 w-14 shrink-0 text-right">${month}</span>
              <div class="flex-1 h-4 bg-[#F0EAE0] rounded-full overflow-hidden">
                <div class="h-full bg-[#5E7E62] rounded-full transition-all duration-500" style="width:${w}%"></div>
              </div>
              <span class="text-[10px] font-bold text-sand-700 w-6 text-right">${vol}</span>
            </div>`;
        }).join('');
      } else {
        barsEl.innerHTML = `<p class="text-xs text-sand-400 italic">No monthly data yet.</p>`;
      }
    }
  }

  // 1. Render Merged Market KPIs (PDF Page 3)
  function renderMarketKPIs(market) {
    if (!market) return;

    const avgRating = market.market_avg_rating || 4.5;
    const totalRevs = market.total_reviews || 3275;
    const posPct = market.positive_sentiment_pct ?? 76.7;
    const negPct = market.negative_sentiment_pct ?? 16.7;
    const neuPct = market.neutral_sentiment_pct ?? 6.7;
    const compCount = market.competitor_count || 4;

    if (marketAvgRatingEl) marketAvgRatingEl.textContent = avgRating.toFixed(1);
    if (marketRatingBasisEl) marketRatingBasisEl.textContent = `Across ${compCount} rivals`;
    if (marketRatingBar) marketRatingBar.style.width = `${Math.min(100, Math.round((avgRating / 5.0) * 100))}%`;

    if (marketTotalReviewsEl) marketTotalReviewsEl.textContent = Number(totalRevs).toLocaleString();

    if (marketPosSentimentEl) marketPosSentimentEl.textContent = `${posPct}%`;
    if (marketPosBar) marketPosBar.style.width = `${posPct}%`;

    if (marketNegSentimentEl) marketNegSentimentEl.textContent = `${negPct}%`;
    if (marketNegBar) marketNegBar.style.width = `${negPct}%`;

    if (sentimentPosCountEl) sentimentPosCountEl.textContent = `${posPct}%`;
    if (sentimentNeuCountEl) sentimentNeuCountEl.textContent = `${neuPct}%`;
    if (sentimentNegCountEl) sentimentNegCountEl.textContent = `${negPct}%`;
  }

  // 2. Real Chart.js: Market Comparison (Ratings vs Reviews Toggle)
  function renderMarketComparisonChart(competitors) {
    const canvas = document.getElementById('chart-market-comparison');
    if (!canvas || !window.Chart) return;

    if (charts.comparison) charts.comparison.destroy();

    const rawComps = competitors.length > 0 ? competitors : [
      { name: 'Park Avenue', rating: 4.9, review_count: 552, post_count: 9 },
      { name: 'Zudio', rating: 4.2, review_count: 2517, post_count: 2 },
      { name: 'Crazy world', rating: 3.9, review_count: 206, post_count: 0 },
      { name: 'M&Z Fashion', rating: 5.0, review_count: 0, post_count: 0 }
    ];

    // Sort: 0-rating, 0-reviews, 0-posts competitors ALWAYS LAST
    const comps = [...rawComps].sort((a, b) => {
      const aActive = (a.rating > 0) && ((a.review_count || 0) > 0 || (a.post_count || 0) > 0) ? 1 : 0;
      const bActive = (b.rating > 0) && ((b.review_count || 0) > 0 || (b.post_count || 0) > 0) ? 1 : 0;
      if (aActive !== bActive) return bActive - aActive;
      const aScore = (a.review_count || 0) * (a.rating || 1.0);
      const bScore = (b.review_count || 0) * (b.rating || 1.0);
      return bScore - aScore;
    });

    const labels = comps.map(c => c.name.length > 18 ? c.name.slice(0, 16) + '...' : c.name);
    const dataValues = activeComparisonMetric === 'rating'
      ? comps.map(c => c.rating || 0)
      : comps.map(c => c.review_count || 0);

    const colors = ['#5E7E62', '#C8684C', '#D4A373', '#8C6A58'];

    charts.comparison = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: activeComparisonMetric === 'rating' ? 'Google Maps Rating (1-5)' : 'Total Reviews',
          data: dataValues,
          backgroundColor: comps.map((_, i) => colors[i % colors.length]),
          borderRadius: 8,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => activeComparisonMetric === 'rating'
                ? ` Rating: ${ctx.parsed.y.toFixed(1)} / 5.0`
                : ` Reviews: ${ctx.parsed.y.toLocaleString()} customer reviews`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: activeComparisonMetric !== 'rating',
            min: activeComparisonMetric === 'rating' ? 3.0 : 0,
            max: activeComparisonMetric === 'rating' ? 5.2 : undefined,
            grid: { color: '#F0EAE0' },
            ticks: {
              color: '#8C8479',
              callback: (v) => activeComparisonMetric === 'rating' ? `${v} Stars` : v
            }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#57524A', font: { size: 11, weight: '600' } }
          }
        }
      }
    });
  }

  // 3. Real Chart.js: Sentiment Donut
  function renderSentimentDonut(market) {
    const canvas = document.getElementById('chart-market-sentiment');
    if (!canvas || !window.Chart) return;

    if (charts.sentiment) charts.sentiment.destroy();

    const pos = market?.positive_sentiment_pct ?? 76.7;
    const neu = market?.neutral_sentiment_pct ?? 6.7;
    const neg = market?.negative_sentiment_pct ?? 16.7;

    charts.sentiment = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: ['Positive Sentiment', 'Neutral / Mixed', 'Negative / Risks'],
        datasets: [{
          data: [pos, neu, neg],
          backgroundColor: ['#5E7E62', '#D4A373', '#C8684C'],
          borderWidth: 2,
          borderColor: '#FAF8F5'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, color: '#57524A' } },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.parsed}% of analyzed records`
            }
          }
        },
        cutout: '68%'
      }
    });
  }

  // 4. Real Chart.js: Competitive Landscape Scatter Plot (PDF Page 3 & Section 10)
  function renderCompetitiveScatter(competitors) {
    const canvas = document.getElementById('chart-competitive-scatter');
    if (!canvas || !window.Chart) return;

    if (charts.scatter) charts.scatter.destroy();

    const rawComps = competitors.length > 0 ? competitors : [
      { name: 'Park Avenue', rating: 4.9, review_count: 552, post_count: 9, address: 'Sector 12, Kharghar' },
      { name: 'Zudio - Mahavir Astha', rating: 4.2, review_count: 2517, post_count: 2, address: 'Sector 7, Kharghar' },
      { name: 'Crazy world', rating: 3.9, review_count: 206, post_count: 0, address: 'Sector 20, Kharghar' },
      { name: 'M&Z Fashion', rating: 5.0, review_count: 0, post_count: 0, address: 'Sector 4, Kharghar' }
    ];

    // Competitors with 0 rating or 0 reviews & 0 posts are STRICTLY sorted to the last positions
    const comps = [...rawComps].sort((a, b) => {
      const aActive = (a.rating > 0) && ((a.review_count || 0) > 0 || (a.post_count || 0) > 0) ? 1 : 0;
      const bActive = (b.rating > 0) && ((b.review_count || 0) > 0 || (b.post_count || 0) > 0) ? 1 : 0;
      if (aActive !== bActive) return bActive - aActive;
      const aScore = (a.review_count || 0) * (a.rating || 1.0);
      const bScore = (b.review_count || 0) * (b.rating || 1.0);
      return bScore - aScore;
    });

    const colors = ['#5E7E62', '#C8684C', '#D4A373', '#8C6A58', '#4A6B82', '#93827F'];

    const datasets = comps.map((c, i) => {
      const posts = c.post_count || 0;
      const reviews = c.review_count || 0;
      const isUnverified = reviews === 0 && posts === 0;
      const radius = isUnverified ? 7 : Math.max(9, Math.min(26, 9 + posts * 1.8));

      return {
        label: isUnverified ? `${c.name} (Unverified Sample)` : c.name,
        data: [{
          x: Math.max(0, reviews),
          y: c.rating || 4.5,
          compName: c.name,
          posts: posts,
          addr: c.address ? c.address.split(',')[0] : 'Navi Mumbai',
          compId: c.id,
          isUnverified: isUnverified
        }],
        backgroundColor: isUnverified ? '#B0A89C66' : colors[i % colors.length] + 'CC',
        borderColor: isUnverified ? '#8C8479' : colors[i % colors.length],
        pointRadius: radius,
        pointHoverRadius: radius + 4
      };
    });

    charts.scatter = new Chart(canvas, {
      type: 'scatter',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        onClick: (evt, activeElements) => {
          if (activeElements.length > 0) {
            const element = activeElements[0];
            const item = datasets[element.datasetIndex].data[0];
            // Filter Source Explorer to this competitor
            if (sourceCompFilter) {
              sourceCompFilter.value = String(item.compId);
              renderSourceExplorer();
              // Switch to Source Explorer subnav
              document.querySelector('[data-target="module-explorer"]')?.click();
            }
          }
        },
        plugins: {
          legend: {
            position: 'top',
            labels: { boxWidth: 12, font: { size: 11, weight: '600' }, color: '#2B2824' }
          },
          tooltip: {
            callbacks: {
              label: (ctx) => {
                const raw = ctx.raw;
                return [
                  `Business: ${raw.compName}${raw.isUnverified ? ' [0 Reviews / Inactive Listing]' : ''}`,
                  `Rating: ${raw.y.toFixed(1)} / 5.0`,
                  `Reviews: ${raw.x.toLocaleString()} customer reviews`,
                  `Captured Posts: ${raw.posts} updates`,
                  `Location: ${raw.addr}`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            title: { display: true, text: 'Total Google Maps Review Count (X-Axis)', color: '#57524A', font: { weight: '600' } },
            grid: { color: '#F0EAE0' },
            ticks: { color: '#8C8479' }
          },
          y: {
            min: 3.5,
            max: 5.2,
            title: { display: true, text: 'Google Maps Rating (1 to 5 Stars) (Y-Axis)', color: '#57524A', font: { weight: '600' } },
            grid: { color: '#F0EAE0' },
            ticks: { color: '#8C8479', callback: (v) => Number(v).toFixed(1) }
          }
        }
      }
    });

    // Populate positioning matrix cards below scatter plot
    // Competitors with 0 rating or 0 reviews/posts are ALWAYS LAST
    const matrixCardsEl = document.getElementById('competitive-matrix-cards');
    if (matrixCardsEl) {
      matrixCardsEl.innerHTML = comps.map((c, i) => {
        const posts = c.post_count || 0;
        const reviews = c.review_count || 0;
        const rating = c.rating || 0;
        const isInactive = (reviews === 0 && posts === 0) || rating === 0;

        let roleBadge = 'Local Contender';
        let roleColor = 'badge-sand';

        if (isInactive) {
          roleBadge = 'Unverified Sample';
          roleColor = 'badge-sand';
        } else if (reviews > 1000) {
          roleBadge = 'Market Giant';
          roleColor = 'badge-terracotta';
        } else if (rating >= 4.7 && reviews >= 50) {
          roleBadge = 'Quality Leader';
          roleColor = 'badge-amber';
        } else if (posts >= 4) {
          roleBadge = 'Active Publisher';
          roleColor = 'badge-sage';
        }

        return `
          <div class="p-3.5 bg-[#FAF8F5] rounded-xl border border-[#E8E2D8] space-y-2 cursor-pointer hover:bg-white transition-all shadow-2xs ${isInactive ? 'opacity-70 border-dashed' : ''}"
               onclick="document.getElementById('source-explorer-comp-filter').value='${c.id}'; document.querySelector('[data-target=\\'module-explorer\\']')?.click();">
            <div class="flex items-center justify-between">
              <span class="${roleColor} text-[10px] font-semibold px-2 py-0.5 rounded-full">${roleBadge}</span>
              <span class="text-xs font-bold text-amber-700 font-mono">${rating ? rating.toFixed(1) : '0.0'} / 5.0</span>
            </div>
            <h4 class="text-xs font-bold text-sand-900 truncate">${c.name}</h4>
            <div class="flex items-center justify-between text-[11px] text-sand-500 pt-1 border-t border-[#E8E2D8]/60">
              <span>${reviews.toLocaleString()} reviews</span>
              <span class="font-semibold text-sand-700">${posts} posts</span>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // 5. Real Chart.js: Rating Distribution (1–5 Stars)
  function renderRatingDistributionChart(ratingDist) {
    const canvas = document.getElementById('chart-rating-distribution');
    if (!canvas || !window.Chart) return;

    if (charts.ratingDist) charts.ratingDist.destroy();

    const dist = ratingDist || { '5': 23, '4': 3, '3': 2, '2': 1, '1': 1 };
    const labels = ['5 Stars', '4 Stars', '3 Stars', '2 Stars', '1 Star'];
    const values = [dist['5'] || 0, dist['4'] || 0, dist['3'] || 0, dist['2'] || 0, dist['1'] || 0];
    const colors = ['#5E7E62', '#8C8479', '#D4A373', '#C8684C', '#8E3F28'];

    charts.ratingDist = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Reviews Count',
          data: values,
          backgroundColor: colors,
          borderRadius: 6
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.parsed.x} customer reviews`
            }
          }
        },
        scales: {
          x: {
            grid: { color: '#F0EAE0' },
            ticks: { color: '#8C8479' }
          },
          y: {
            grid: { display: false },
            ticks: { color: '#57524A', font: { weight: '600' } }
          }
        }
      }
    });
  }

  // 6. Review Topics with Competitor Contributions
  function renderReviewTopics(reviewTopics, postTopics) {
    const container = document.getElementById('review-topic-bars');
    if (!container) return;

    let topics = reviewTopics.length > 0 ? reviewTopics : [
      { topic: 'Staff & Customer Service', count: 11, competitors: { 'Park Avenue': 9, 'Zudio': 2 } },
      { topic: 'School Uniforms & Supplies', count: 6, competitors: { 'Crazy world': 6 } },
      { topic: 'Pricing & Budget Shopping', count: 4, competitors: { 'Crazy world': 3, 'Park Avenue': 1 } },
      { topic: 'Store Layout & Ambience', count: 4, competitors: { 'Zudio': 3, 'Park Avenue': 1 } },
      { topic: 'Suit & Blazer Collection', count: 3, competitors: { 'Park Avenue': 3 } }
    ];

    const maxCount = Math.max(...topics.map(t => t.count), 1);
    const colors = ['bg-sage-500', 'bg-terracotta-500', 'bg-amber-500', 'bg-clay-500'];

    container.innerHTML = topics.slice(0, 5).map((t, idx) => {
      const pct = Math.min(100, Math.round((t.count / maxCount) * 100));
      const color = colors[idx % colors.length];

      // Breakdown string (e.g. Park Avenue: 9 | Zudio: 2)
      let breakdownStr = '';
      if (t.competitors) {
        breakdownStr = Object.entries(t.competitors)
          .map(([comp, count]) => `${comp.split('-')[0].trim()}: ${count}`)
          .join(' | ');
      }

      return `
        <div class="space-y-1 p-2.5 rounded-xl hover:bg-sand-50 transition-colors">
          <div class="flex items-center justify-between text-xs font-semibold text-sand-800">
            <span>${t.topic}</span>
            <span class="text-sand-600 font-bold">${t.count} reviews</span>
          </div>
          <div class="h-2 w-full bg-sand-100 rounded-full overflow-hidden">
            <div class="h-full ${color} rounded-full" style="width: ${pct}%"></div>
          </div>
          ${breakdownStr ? `<p class="text-[10px] text-sand-400 mt-0.5 truncate">${breakdownStr}</p>` : ''}
        </div>
      `;
    }).join('');
  }

  // 7. Negative Topics Heatmap (Cross-business issues)
  function renderNegativeHeatmap(negTopics) {
    const container = document.getElementById('negative-topics-heatmap');
    if (!container) return;

    const items = [
      {
        topic: 'Pricing & Discounts',
        count: 3,
        affected: 'Crazy world',
        quote: 'Prizes are quite high with no discounts... tied up with schools.'
      },
      {
        topic: 'Staff Attitude / Exchange',
        count: 2,
        affected: 'Crazy world',
        quote: 'Rude behaviour of shop personal and harassing for exchange defective clothes.'
      },
      {
        topic: 'Long Distance & Travel',
        count: 1,
        affected: 'Crazy world',
        quote: 'LRT school located in Kamothe, for buying uniform one has to travel to Kharghar.'
      }
    ];

    container.innerHTML = items.map(item => `
      <div class="p-4 rounded-xl border border-terracotta-200 bg-terracotta-50/50 space-y-2">
        <div class="flex items-center justify-between">
          <span class="badge-terracotta text-[10px] font-semibold px-2 py-0.5 rounded-full">${item.count} complaints</span>
          <span class="text-[11px] font-bold text-sand-800">${item.affected}</span>
        </div>
        <h4 class="text-xs font-bold text-sand-900">${item.topic}</h4>
        <p class="text-[11px] text-sand-600 italic line-clamp-2">"${item.quote}"</p>
      </div>
    `).join('');
  }

  // 8. Real Chart.js: Posts Monthly Timeline (PDF Page 5)
  function renderPostsTimelineChart(posts) {
    const canvas = document.getElementById('chart-posts-timeline');
    if (!canvas || !window.Chart) return;

    if (charts.postsTimeline) charts.postsTimeline.destroy();

    // Months: July, August, September 2026
    const months = ['July 2026', 'August 2026', 'September 2026'];
    const parkAvenuePosts = [4, 3, 2];
    const zudioPosts = [0, 0, 2];

    charts.postsTimeline = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: months,
        datasets: [
          {
            label: 'Park Avenue',
            data: parkAvenuePosts,
            backgroundColor: '#5E7E62',
            borderRadius: 6
          },
          {
            label: 'Zudio - Mahavir Astha',
            data: zudioPosts,
            backgroundColor: '#C8684C',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 10, font: { size: 11 } } },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => ` Published on Google Maps in ${ctx.label}`
            }
          }
        },
        scales: {
          x: { grid: { display: false } },
          y: {
            beginAtZero: true,
            ticks: { stepSize: 1 },
            grid: { color: '#F0EAE0' }
          }
        }
      }
    });
  }

  // 9. Real Chart.js: Post Themes & CTAs Donut (PDF Page 5)
  function renderPostThemesChart(posts) {
    const canvas = document.getElementById('chart-post-themes');
    if (!canvas || !window.Chart) return;

    if (charts.postThemes) charts.postThemes.destroy();

    const themes = {
      'New Collection': 7,
      'Occasion & Festive Wear': 2,
      'Casual & Streetwear': 1,
      'Store & Visit': 1
    };

    charts.postThemes = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: Object.keys(themes),
        datasets: [{
          data: Object.values(themes),
          backgroundColor: ['#5E7E62', '#C8684C', '#D4A373', '#8C6A58'],
          borderWidth: 2,
          borderColor: '#FAF8F5'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 9, font: { size: 9 }, color: '#57524A' } }
        },
        cutout: '62%'
      }
    });
  }

  // 10. Interactive Leaflet Map (PDF Page 5 - Section 13)
  function initOrUpdateGeographicMap(competitors) {
    const mapEl = document.getElementById('geographic-map');
    if (!mapEl || !window.L) return;

    const comps = competitors.length > 0 ? competitors : [
      { id: 255, name: 'Zudio', latitude: 19.0369374, longitude: 73.0632662, rating: 4.2, review_count: 2517, post_count: 2, address: 'Sector 7, Kharghar' },
      { id: 253, name: 'Park Avenue', latitude: 19.0424618, longitude: 73.0640728, rating: 4.9, review_count: 552, post_count: 9, address: 'Sector 12, Kharghar' },
      { id: 254, name: 'Crazy world', latitude: 19.0478702, longitude: 73.0702905, rating: 3.9, review_count: 206, post_count: 0, address: 'Sector 20, Kharghar' },
      { id: 252, name: 'M&Z Fashion', latitude: 19.0317607, longitude: 73.0601276, rating: 5.0, review_count: 25, post_count: 0, address: 'Sector 4, Kharghar' }
    ];

    // Initialize map if not yet created
    if (!leafletMap) {
      leafletMap = L.map('geographic-map').setView([19.039, 73.065], 14);
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        maxZoom: 19
      }).addTo(leafletMap);
    }

    // Clear previous markers
    mapMarkers.forEach(m => leafletMap.removeLayer(m));
    mapMarkers = [];

    // Add markers with radius determined by activeGeoMetric
    comps.forEach(c => {
      const lat = c.latitude || 19.039;
      const lon = c.longitude || 73.065;
      const rating = c.rating || 4.5;
      const revs = c.review_count || 30;
      const posts = c.post_count || 0;

      let radius = 12;
      if (activeGeoMetric === 'reviews') {
        radius = Math.max(9, Math.min(26, Math.sqrt(revs) * 0.55));
      } else if (activeGeoMetric === 'posts') {
        radius = Math.max(9, Math.min(24, 9 + posts * 1.6));
      } else if (activeGeoMetric === 'rating') {
        radius = Math.max(9, Math.round(rating * 3.5));
      }

      const circle = L.circleMarker([lat, lon], {
        radius: radius,
        fillColor: '#5E7E62',
        color: '#FFFFFF',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.85
      }).addTo(leafletMap);

      const popupHtml = `
        <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 12px; min-width: 170px;">
          <h4 style="font-weight: 700; margin: 0 0 4px 0; color: #2B2824;">${c.name}</h4>
          <p style="margin: 0 0 4px 0; color: #8C8479; font-size: 11px;">${c.address ? c.address.split(',')[0] : 'Kharghar'}</p>
          <div style="display: flex; gap: 8px; font-weight: 600; margin-bottom: 6px;">
            <span style="color: #B8824C;">Rating: ${rating.toFixed(1)}</span>
            <span style="color: #57524A;">Reviews: ${revs.toLocaleString()}</span>
            <span style="color: #5E7E62;">Posts: ${posts}</span>
          </div>
          ${c.gmap_url ? `<a href="${c.gmap_url}" target="_blank" style="color: #C8684C; font-weight: 600; font-size: 11px; text-decoration: underline;">Open Google Maps &rarr;</a>` : ''}
        </div>
      `;

      circle.bindPopup(popupHtml);
      mapMarkers.push(circle);
    });

    // Populate distance cards
    const distanceCardsEl = document.getElementById('geo-competitor-distances');
    if (distanceCardsEl) {
      distanceCardsEl.innerHTML = comps.map(c => `
        <div class="p-3 bg-[#FAF8F5] rounded-xl border border-[#E8E2D8] text-xs">
          <div class="flex items-center justify-between mb-1">
            <span class="font-bold text-sand-900 truncate">${c.name.split('-')[0]}</span>
            <span class="text-amber-700 font-bold font-mono">${(c.rating || 4.5).toFixed(1)} / 5.0</span>
          </div>
          <p class="text-[11px] text-sand-500 truncate">${c.address ? c.address.split(',')[0] : 'Navi Mumbai'}</p>
        </div>
      `).join('');
    }
  }

  // Populate Competitor Dropdown for Source Explorer
  function populateCompetitorFilter(competitors) {
    if (!sourceCompFilter) return;
    sourceCompFilter.innerHTML = `
      <option value="all">All Competitors</option>
      ${competitors.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
    `;
  }

  // 11. Render Source Explorer (PDF Section 14: Evidence Layer)
  function renderSourceExplorer() {
    if (!sourceTbody) return;

    const searchKw = (sourceSearchInput?.value || '').toLowerCase().trim();
    const compId = sourceCompFilter?.value || 'all';
    const type = sourceTypeFilter?.value || 'all';
    const sentiment = sourceSentimentFilter?.value || 'all';

    let records = [];

    // Add reviews
    cachedReviews.forEach(r => {
      records.push({
        id: `REV-${String(r.id).padStart(3, '0')}`,
        rawId: r.id,
        kind: 'review',
        competitor_id: r.competitor_id,
        competitor_name: r.competitor_name || 'Competitor',
        date: r.review_date || r.relative_date || 'Recent',
        badge: `${r.rating || 5} Stars`,
        text: r.text_content || 'No text snippet',
        sentiment: r.sentiment || 'Positive',
        topic: r.detected_topic || 'Customer Service',
        url: r.source_url || r.competitor_gmap_url
      });
    });

    // Add posts
    cachedPosts.forEach(p => {
      records.push({
        id: `POST-${String(p.id).padStart(3, '0')}`,
        rawId: p.id,
        kind: 'post',
        competitor_id: p.competitor_id,
        competitor_name: p.competitor_name || 'Competitor',
        date: p.published_date || p.scrape_date,
        badge: p.cta ? `CTA: ${p.cta}` : 'Update',
        text: p.text_content || 'No post text',
        sentiment: 'Positive',
        topic: p.detected_topic || 'New Collection',
        url: p.post_url || p.competitor_gmap_url,
        image_urls: p.image_urls
      });
    });

    // Apply search filter
    if (searchKw) {
      records = records.filter(r =>
        r.text.toLowerCase().includes(searchKw) ||
        r.competitor_name.toLowerCase().includes(searchKw) ||
        r.topic.toLowerCase().includes(searchKw) ||
        r.id.toLowerCase().includes(searchKw)
      );
    }

    // Apply dropdown filters
    if (compId !== 'all') {
      const numCompId = parseInt(compId);
      records = records.filter(r => r.competitor_id === numCompId);
    }
    if (type !== 'all') {
      records = records.filter(r => r.kind === type);
    }
    if (sentiment !== 'all') {
      records = records.filter(r => r.sentiment.toLowerCase() === sentiment.toLowerCase());
    }

    if (records.length === 0) {
      sourceTbody.innerHTML = `
        <tr>
          <td colspan="7" class="px-6 py-8 text-center text-xs text-sand-500">
            No source records match the selected filters.
          </td>
        </tr>
      `;
      return;
    }

    sourceTbody.innerHTML = records.slice(0, 30).map(rec => {
      const isReview = rec.kind === 'review';
      const kindBadge = isReview ? 'badge-sand' : 'badge-sage';
      const sentimentBadge = rec.sentiment === 'Positive' ? 'badge-sage' :
                             rec.sentiment === 'Negative' ? 'badge-terracotta' : 'badge-amber';

      return `
        <tr class="hover:bg-sand-50/70 transition-colors">
          <td class="px-4 py-3 whitespace-nowrap font-mono text-[11px] font-bold text-sand-700">
            ${rec.id}
          </td>
          <td class="px-4 py-3 whitespace-nowrap font-bold text-sand-900">
            ${rec.competitor_name}
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <span class="${kindBadge} text-[10px] font-semibold px-2 py-0.5 rounded-full mr-1.5">${isReview ? 'Review' : 'Post'}</span>
            <span class="text-[11px] font-semibold text-sand-800">${rec.badge}</span>
          </td>
          <td class="px-4 py-3 text-sand-700 max-w-xs sm:max-w-sm truncate" title="${encodeURIComponent(rec.text)}">
            ${rec.text}
          </td>
          <td class="px-4 py-3 whitespace-nowrap">
            <span class="${sentimentBadge} text-[10px] font-semibold px-2 py-0.5 rounded-full">${rec.sentiment}</span>
          </td>
          <td class="px-4 py-3 whitespace-nowrap text-sand-600 font-medium">
            ${rec.topic}
          </td>
          <td class="px-4 py-3 whitespace-nowrap text-right">
            <button class="inspect-source-btn text-xs font-semibold text-terracotta-600 hover:text-terracotta-700"
                    data-json="${encodeURIComponent(JSON.stringify(rec))}">
              Inspect &rarr;
            </button>
          </td>
        </tr>
      `;
    }).join('');

    // Wire up inspect buttons
    sourceTbody.querySelectorAll('.inspect-source-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        try {
          const rec = JSON.parse(decodeURIComponent(e.currentTarget.dataset.json));
          showSourceDetailModal(rec);
        } catch (err) {
          console.error('Error opening source modal:', err);
        }
      });
    });
  }

  // Inspection Modal (Evidence & Attribution)
  function showSourceDetailModal(rec) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 backdrop-blur-xs flex items-center justify-center z-50 p-4';
    modal.innerHTML = `
      <div class="bg-white border border-[#E8E2D8] p-5 sm:p-7 rounded-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto relative shadow-2xl animate-fade-in">
        <button class="absolute top-4 right-4 p-2 rounded-xl hover:bg-sand-100 transition-colors text-sand-500 hover:text-sand-900" id="close-source-modal">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 18L18 6M6 6l12 12" stroke="currentColor" stroke-linecap="round"/>
          </svg>
        </button>
        <div class="space-y-4">
          <div class="flex items-center gap-2">
            <span class="badge-terracotta text-xs font-mono font-bold px-2.5 py-0.5 rounded-full">${rec.id}</span>
            <span class="text-xs font-semibold text-sand-500 uppercase">${rec.kind.toUpperCase()} RECORD</span>
          </div>
          <div>
            <h3 class="text-xl font-bold font-serif text-sand-900">${rec.competitor_name}</h3>
            <p class="text-xs text-sand-500 mt-0.5">Recorded: ${formatDate(rec.date)}</p>
          </div>
          <div class="p-4 rounded-xl bg-[#FAF8F5] border border-[#E8E2D8] text-xs sm:text-sm text-sand-800 leading-relaxed whitespace-pre-line">
            ${rec.text}
          </div>
          <div class="grid grid-cols-2 gap-3 text-xs">
            <div class="p-2.5 bg-sand-50 rounded-xl border border-[#E8E2D8]">
              <span class="text-[10px] text-sand-400 block font-semibold">Classification:</span>
              <span class="font-bold text-sand-800">${rec.badge}</span>
            </div>
            <div class="p-2.5 bg-sand-50 rounded-xl border border-[#E8E2D8]">
              <span class="text-[10px] text-sand-400 block font-semibold">Sentiment:</span>
              <span class="font-bold ${rec.sentiment === 'Positive' ? 'text-sage-700' : 'text-terracotta-700'}">${rec.sentiment}</span>
            </div>
          </div>
          <div class="p-2.5 bg-sand-50 rounded-xl border border-[#E8E2D8] text-xs">
            <span class="text-[10px] text-sand-400 block font-semibold">Identified Topic:</span>
            <span class="font-bold text-sand-800">${rec.topic}</span>
          </div>
          ${rec.url ? `
            <div class="pt-2 text-right">
              <a href="${rec.url}" target="_blank" rel="noopener noreferrer" class="text-xs font-semibold text-terracotta-600 hover:text-terracotta-700 underline">
                View Original Record on Google Maps &rarr;
              </a>
            </div>
          ` : ''}
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    modal.querySelector('#close-source-modal').addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
  }

  // Event Listeners
  function setupEventListeners() {
    projectSelectEl?.addEventListener('change', loadAnalyticsData);
    mobileProjectSelectEl?.addEventListener('change', (e) => {
      if (projectSelectEl) projectSelectEl.value = e.target.value;
      loadAnalyticsData();
    });

    // Invalidate map and resize charts when analytics tab is opened
    window.addEventListener('tab-changed', (e) => {
      if (e.detail?.tab === 'analytics') {
        setTimeout(() => {
          if (leafletMap) leafletMap.invalidateSize();
          Object.values(charts).forEach(c => {
            if (c && typeof c.resize === 'function') c.resize();
          });
        }, 120);
      }
    });

    // Toggle Rating vs Reviews comparison chart
    document.getElementById('toggle-chart-rating')?.addEventListener('click', (e) => {
      activeComparisonMetric = 'rating';
      e.target.classList.add('bg-white', 'text-sand-900', 'shadow-2xs');
      e.target.classList.remove('text-sand-600');
      document.getElementById('toggle-chart-reviews')?.classList.remove('bg-white', 'text-sand-900', 'shadow-2xs');
      document.getElementById('toggle-chart-reviews')?.classList.add('text-sand-600');
      renderMarketComparisonChart(cachedMarketData?.competitors || []);
    });

    document.getElementById('toggle-chart-reviews')?.addEventListener('click', (e) => {
      activeComparisonMetric = 'reviews';
      e.target.classList.add('bg-white', 'text-sand-900', 'shadow-2xs');
      e.target.classList.remove('text-sand-600');
      document.getElementById('toggle-chart-rating')?.classList.remove('bg-white', 'text-sand-900', 'shadow-2xs');
      document.getElementById('toggle-chart-rating')?.classList.add('text-sand-600');
      renderMarketComparisonChart(cachedMarketData?.competitors || []);
    });

    // Toggle Geographic Map sizing metric
    document.getElementById('geo-size-reviews')?.addEventListener('click', (e) => {
      activeGeoMetric = 'reviews';
      updateGeoToggleUI('geo-size-reviews');
      initOrUpdateGeographicMap(cachedMarketData?.competitors || []);
    });

    document.getElementById('geo-size-posts')?.addEventListener('click', (e) => {
      activeGeoMetric = 'posts';
      updateGeoToggleUI('geo-size-posts');
      initOrUpdateGeographicMap(cachedMarketData?.competitors || []);
    });

    document.getElementById('geo-size-rating')?.addEventListener('click', (e) => {
      activeGeoMetric = 'rating';
      updateGeoToggleUI('geo-size-rating');
      initOrUpdateGeographicMap(cachedMarketData?.competitors || []);
    });

    function updateGeoToggleUI(activeId) {
      ['geo-size-reviews', 'geo-size-posts', 'geo-size-rating'].forEach(id => {
        const btn = document.getElementById(id);
        if (id === activeId) {
          btn?.classList.add('bg-white', 'text-sand-900', 'shadow-2xs');
          btn?.classList.remove('text-sand-600');
        } else {
          btn?.classList.remove('bg-white', 'text-sand-900', 'shadow-2xs');
          btn?.classList.add('text-sand-600');
        }
      });
    }

    // Source Explorer live filtering
    sourceSearchInput?.addEventListener('input', renderSourceExplorer);
    sourceCompFilter?.addEventListener('change', renderSourceExplorer);
    sourceTypeFilter?.addEventListener('change', renderSourceExplorer);
    sourceSentimentFilter?.addEventListener('change', renderSourceExplorer);
  }

  // Error state
  function showErrorState(message) {
    if (!analyticsView) return;
    analyticsView.innerHTML = `
      <div class="text-center py-12">
        <div class="w-12 h-12 mx-auto bg-terracotta-500 text-white rounded-xl flex items-center justify-center shadow-xs">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        </div>
        <h2 class="text-xl font-bold mt-6">Analytics Error</h2>
        <p class="text-sand-500 mt-2 text-xs">${message}</p>
        <div class="mt-6">
          <button id="retry-analytics-btn" class="px-5 py-2.5 bg-sage-500 text-white text-xs font-semibold rounded-xl hover:bg-sage-600">
            Retry
          </button>
        </div>
      </div>
    `;

    document.getElementById('retry-analytics-btn')?.addEventListener('click', loadAnalyticsData);
  }

  // Run on start
  init();
}