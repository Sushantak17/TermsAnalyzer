/**
 * TermsAnalyzer — Side Panel Logic
 *
 * Handles: text extraction → API call → result rendering → in-page highlighting
 */

const API_BASE = 'http://localhost:8000';

// State
let currentResults = null;
let currentTabId = null;
let highlightsActive = false;

// DOM refs
const views = {
  landing: document.getElementById('landing'),
  loading: document.getElementById('loading'),
  error: document.getElementById('error'),
  results: document.getElementById('results'),
};


// ==================== View Management ====================

function showView(name) {
  Object.values(views).forEach(v => v.classList.remove('active'));
  views[name].classList.add('active');
}


// ==================== Analyze Button ====================

document.getElementById('analyze-btn').addEventListener('click', async () => {
  await startAnalysis();
});

document.getElementById('retry-btn').addEventListener('click', async () => {
  await startAnalysis();
});

document.getElementById('new-analysis-btn').addEventListener('click', async () => {
  // Clear highlights on the page
  if (highlightsActive && currentTabId) {
    try {
      await chrome.tabs.sendMessage(currentTabId, { type: 'CLEAR_HIGHLIGHTS' });
    } catch (e) { /* tab may have navigated */ }
  }
  highlightsActive = false;
  currentResults = null;
  chrome.runtime.sendMessage({ type: 'CLEAR_BADGE' });
  showView('landing');
});


async function startAnalysis() {
  showView('loading');
  updateLoadingStatus('Extracting text from page');

  try {
    // 1. Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) throw new Error('No active tab found');
    currentTabId = tab.id;

    // Check if we can access this page
    if (tab.url.startsWith('chrome://') || tab.url.startsWith('chrome-extension://') || tab.url.startsWith('about:')) {
      throw new Error('Cannot analyze browser internal pages. Please navigate to a website.');
    }

    // 2. Send URL to backend (same endpoint as the web app — uses trafilatura)
    const pageTitle = tab.title || 'Unknown Page';
    updateLoadingStatus('Sending to AI for analysis...');

    const apiResponse = await fetch(`${API_BASE}/api/analyze/url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: tab.url }),
    });

    if (!apiResponse.ok) {
      const errData = await apiResponse.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error: ${apiResponse.status}`);
    }

    updateLoadingStatus('Rendering results...');
    const data = await apiResponse.json();

    // 5. Store and render
    currentResults = data;
    renderResults(data, pageTitle);

    // 6. Update badge
    chrome.runtime.sendMessage({
      type: 'UPDATE_BADGE',
      risk: data.summary.overall_risk,
    });

    showView('results');

  } catch (err) {
    showError(err.message);
  }
}


// ==================== Loading Status ====================

function updateLoadingStatus(text) {
  document.getElementById('loading-status').textContent = text;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}


// ==================== Error ====================

function showError(message) {
  let title = 'Analysis Failed';
  if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
    title = 'Backend Not Running';
    message = 'Could not connect to the TermsAnalyzer server. Make sure it\'s running on localhost:8000.\n\nRun: uvicorn server:app --port 8000';
  }
  document.getElementById('error-title').textContent = title;
  document.getElementById('error-message').textContent = message;
  showView('error');
}


// ==================== Render Results ====================

function renderResults(data, pageTitle) {
  const { clauses, summary, summary_text } = data;

  // Risk banner
  const banner = document.getElementById('risk-banner');
  const riskClass = summary.overall_risk.toLowerCase().replace(/\s+/g, '-');
  banner.className = `risk-banner ${riskClass}`;
  document.getElementById('risk-label').textContent = summary.overall_risk;
  document.getElementById('risk-score').textContent = `${summary.average_risk_score} / 5`;

  // Page info
  document.getElementById('page-title').textContent = pageTitle;

  // Stats
  const bd = summary.breakdown;
  document.getElementById('stat-total').textContent = summary.total_clauses;
  document.getElementById('stat-fair').textContent = bd.fair || 0;
  document.getElementById('stat-risky').textContent = bd.potentially_unfair || 0;
  document.getElementById('stat-unfair').textContent = bd.unfair || 0;

  // Distribution bar
  const total = summary.total_clauses || 1;
  document.getElementById('dist-fair').style.width = `${((bd.fair || 0) / total) * 100}%`;
  document.getElementById('dist-risky').style.width = `${((bd.potentially_unfair || 0) / total) * 100}%`;
  document.getElementById('dist-unfair').style.width = `${((bd.unfair || 0) / total) * 100}%`;

  // Summary text
  document.getElementById('summary-text').textContent = summary_text;

  // Clause list
  renderClauses(clauses, 'all');

  // Reset highlight state
  highlightsActive = false;
  document.getElementById('highlight-btn').style.display = '';
  document.getElementById('clear-highlight-btn').style.display = 'none';
}


function renderClauses(clauses, filter) {
  const list = document.getElementById('clause-list');
  list.innerHTML = '';

  const filtered = filter === 'all' ? clauses : clauses.filter(c => c.label === filter);

  if (!filtered.length) {
    list.innerHTML = '<p style="text-align:center; color:#64748B; padding:24px;">No clauses in this category.</p>';
    return;
  }

  // Sort: unfair first, then risky, then fair
  const order = { unfair: 0, potentially_unfair: 1, fair: 2 };
  const sorted = [...filtered].sort((a, b) => (order[a.label] ?? 9) - (order[b.label] ?? 9) || b.confidence - a.confidence);

  for (const clause of sorted) {
    const card = document.createElement('div');
    card.className = `clause-card ${clause.label}`;

    const labelText = {
      fair: 'Fair',
      potentially_unfair: 'Potentially Unfair',
      unfair: 'Clearly Unfair',
    }[clause.label] || clause.label;

    let html = `
      <div class="clause-header">
        <span class="clause-badge ${clause.label}">${labelText}</span>
        <span class="clause-confidence">${Math.round(clause.confidence * 100)}%</span>
      </div>
      <p class="clause-text">${escapeHtml(clause.clause)}</p>
    `;

    if (clause.category && clause.category !== 'General') {
      html += `<span class="clause-category">${escapeHtml(clause.category)}</span>`;
    }

    // RAG explanations
    if (clause.explanations && clause.explanations.length > 0) {
      const id = `exp-${Math.random().toString(36).slice(2, 8)}`;
      html += `
        <div class="clause-explanations">
          <button class="explanation-toggle" data-target="${id}">
            ▶ Similar cases (${clause.explanations.length})
          </button>
          <div class="explanation-list" id="${id}">
            ${clause.explanations.map(exp => `
              <div class="explanation-item">
                <div class="explanation-meta">
                  <span class="explanation-company">${escapeHtml(exp.company)}</span>
                  <span class="explanation-similarity">${Math.round(exp.similarity * 100)}% similar</span>
                </div>
                <p class="explanation-text">${escapeHtml(exp.explanation || exp.similar_clause)}</p>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }

    card.innerHTML = html;
    list.appendChild(card);
  }
}


// ==================== Filter Tabs ====================

document.querySelectorAll('.filter-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const filter = tab.dataset.filter;
    if (currentResults) {
      renderClauses(currentResults.clauses, filter);
    }
  });
});


// ==================== Explanation Toggle ====================

document.addEventListener('click', (e) => {
  const toggle = e.target.closest('.explanation-toggle');
  if (!toggle) return;

  const targetId = toggle.dataset.target;
  const list = document.getElementById(targetId);
  if (!list) return;

  const isOpen = list.classList.toggle('open');
  toggle.textContent = isOpen
    ? `▼ Similar cases (${list.children.length})`
    : `▶ Similar cases (${list.children.length})`;
});


// ==================== Highlight Button ====================

document.getElementById('highlight-btn').addEventListener('click', async () => {
  if (!currentResults || !currentTabId) return;

  try {
    // Inject content script (idempotent due to __termsanalyzerInjected guard)
    await chrome.scripting.executeScript({
      target: { tabId: currentTabId },
      files: ['content-script.js']
    });

    await sleep(100);

    const response = await chrome.tabs.sendMessage(currentTabId, {
      type: 'HIGHLIGHT_CLAUSES',
      clauses: currentResults.clauses,
    });

    highlightsActive = true;
    document.getElementById('highlight-btn').style.display = 'none';
    document.getElementById('clear-highlight-btn').style.display = '';

  } catch (e) {
    console.error('Highlight error:', e);
  }
});

document.getElementById('clear-highlight-btn').addEventListener('click', async () => {
  if (!currentTabId) return;

  try {
    await chrome.tabs.sendMessage(currentTabId, { type: 'CLEAR_HIGHLIGHTS' });
  } catch (e) { /* page may have navigated */ }

  highlightsActive = false;
  document.getElementById('highlight-btn').style.display = '';
  document.getElementById('clear-highlight-btn').style.display = 'none';
});


// ==================== Helpers ====================

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
