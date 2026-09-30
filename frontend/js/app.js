// Main Application Entry Point
import { initAPI } from './components/api.js';
import { initDashboard } from './components/dashboard.js';
import { initCompetitors } from './components/competitors.js';
import { initPosts } from './components/posts.js';
import { initAnalytics } from './components/analytics.js';
import { initIdeas } from './components/ideas.js';

console.log('MapCompete frontend initializing...');

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  console.log('DOM loaded, initializing app');
  try {
    // Initialize API service. initAPI() is async because on localhost it first
    // verifies which local backend (if any) is actually running, and only then
    // hands the components a working base URL. Every component below therefore
    // starts with a resolved API instead of racing the detection.
    const api = await initAPI();
    console.log('API service initialized');

    // Initialize components
    initDashboard(api);
    console.log('Dashboard initialized');
    initCompetitors(api);
    console.log('Competitors initialized');
    initPosts(api);
    console.log('Posts initialized');
    initAnalytics(api);
    console.log('Analytics initialized');
    initIdeas(api);
    console.log('Ideas initialized');

    // Initialize UI interactions
    initUI();
    console.log('UI interactions initialized');

    console.log('MapCompete initialized successfully');
  } catch (error) {
    console.error('Error initializing MapCompete:', error);
    // Show error on page
    const errorDiv = document.createElement('div');
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '0';
    errorDiv.style.left = '0';
    errorDiv.style.width = '100%';
    errorDiv.style.backgroundColor = '#fee2e2';
    errorDiv.style.color = '#991b1b';
    errorDiv.style.padding = '1rem';
    errorDiv.style.zIndex = '9999';
    errorDiv.textContent = `Application Error: ${error.message}`;
    document.body.appendChild(errorDiv);
  }
});

// Initialize UI interactions (theme toggle, mobile sidebar, etc.)
function initUI() {
  // Theme toggle
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      document.documentElement.classList.toggle('dark');
      // Save preference to localStorage
      const isDark = document.documentElement.classList.contains('dark');
      localStorage.setItem('theme', isDark ? 'dark' : 'light');

      // Update icon
      const icon = themeToggle.querySelector('svg');
      if (isDark) {
        icon.setAttribute('stroke', 'currentColor');
      } else {
        icon.setAttribute('stroke', 'currentColor');
      }
    });
  }

  // Load theme preference from localStorage
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark');
  }

  // Mobile sidebar
  const mobileProjectBtn = document.getElementById('mobile-project-btn');
  const mobileSidebar = document.getElementById('mobile-sidebar');
  const mobileCloseBtn = document.getElementById('mobile-close-btn');

  if (mobileProjectBtn && mobileSidebar) {
    mobileProjectBtn.addEventListener('click', () => {
      mobileSidebar.classList.remove('-translate-x-full');
    });
  }

  if (mobileCloseBtn && mobileSidebar) {
    mobileCloseBtn.addEventListener('click', () => {
      mobileSidebar.classList.add('-translate-x-full');
    });
  }

  // Tab switching
  const tabs = {
    dashboard: document.getElementById('dashboard-tab'),
    competitors: document.getElementById('competitors-tab'),
    posts: document.getElementById('posts-tab'),
    analytics: document.getElementById('analytics-tab'),
    ideas: document.getElementById('ideas-tab')
  };

  const views = {
    dashboard: document.getElementById('dashboard-view'),
    competitors: document.getElementById('competitors-view'),
    posts: document.getElementById('posts-view'),
    analytics: document.getElementById('analytics-view'),
    ideas: document.getElementById('ideas-view')
  };

  // Set initial active tab
  if (tabs.dashboard) {
    tabs.dashboard.classList.add('tab-active');
    views.dashboard?.classList.remove('hidden');
  }

  // Add click listeners to tabs
  Object.keys(tabs).forEach(tabKey => {
    const tab = tabs[tabKey];
    const view = views[tabKey];

    if (tab && view) {
      tab.addEventListener('click', () => {
        // Deactivate all tabs
        Object.values(tabs).forEach(t => {
          t?.classList.remove('tab-active');
        });

        // Activate clicked tab
        tab.classList.add('tab-active');

        // Hide all views
        Object.values(views).forEach(v => {
          v?.classList.add('hidden');
        });

        // Show selected view
        view.classList.remove('hidden');

        // Dispatch tab-changed event for responsive chart & map auto-adjustment
        window.dispatchEvent(new CustomEvent('tab-changed', { detail: { tab: tabKey } }));
        window.dispatchEvent(new Event('resize'));
      });
    }
  });

  // Handle CAPTCHA modal
  const captchaModal = document.getElementById('captcha-modal');
  const captchaContinue = document.getElementById('captcha-continue');
  const captchaCancel = document.getElementById('captcha-cancel');

  if (captchaContinue && captchaModal) {
    captchaContinue.addEventListener('click', () => {
      captchaModal.classList.add('hidden');
      showToast('Verification completed. Resuming scraping...', 'success');
    });
  }

  if (captchaCancel && captchaModal) {
    captchaCancel.addEventListener('click', () => {
      captchaModal.classList.add('hidden');
      showToast('Scraping cancelled due to verification requirement', 'warning');
    });
  }

  // Header buttons
  const helpBtn = document.getElementById('help-btn');
  if (helpBtn) {
    helpBtn.addEventListener('click', () => {
      showToast('MapCompete monitors local competitor Google Maps posts to inspire your marketing strategy.', 'info');
    });
  }

  // Toast notification system with Earthy & Pastel design
  window.showToast = (message, type = 'info') => {
    const existingToast = document.getElementById('toast-notification');
    if (existingToast) {
      existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = `fixed bottom-5 right-5 px-4 py-3 rounded-xl text-xs font-semibold shadow-lg transition-all duration-300 flex items-center gap-2 z-50 ${
      type === 'success' ? 'bg-sage-600 text-white' :
      type === 'warning' ? 'bg-amber-600 text-white' :
      type === 'error' ? 'bg-terracotta-600 text-white' :
      'bg-sand-900 text-white'
    }`;
    toast.textContent = message;
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(12px)';

    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(12px)';
      setTimeout(() => {
        if (toast.parentNode) {
          toast.parentNode.removeChild(toast);
        }
      }, 300);
    }, 3200);
  };
}