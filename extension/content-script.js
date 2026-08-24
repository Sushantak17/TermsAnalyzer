/**
 * TermsAnalyzer — Content Script
 *
 * Injected on demand to:
 * 1. Extract page text (on EXTRACT_TEXT message)
 * 2. Highlight flagged clauses in the page (on HIGHLIGHT_CLAUSES message)
 * 3. Clear highlights (on CLEAR_HIGHLIGHTS message)
 */

(() => {
  // Prevent double-injection
  if (window.__termsanalyzerInjected) return;
  window.__termsanalyzerInjected = true;

  const HIGHLIGHT_CLASS = 'termsanalyzer-highlight';
  const TOOLTIP_CLASS = 'termsanalyzer-tooltip';

  // Inject highlight styles once
  const style = document.createElement('style');
  style.textContent = `
    .${HIGHLIGHT_CLASS} {
      position: relative;
      border-radius: 3px;
      padding: 1px 2px;
      cursor: pointer;
      transition: filter 0.2s;
    }
    .${HIGHLIGHT_CLASS}:hover {
      filter: brightness(0.9);
    }
    .${HIGHLIGHT_CLASS}[data-risk="unfair"] {
      background: rgba(239, 68, 68, 0.2);
      border-bottom: 2px solid #EF4444;
    }
    .${HIGHLIGHT_CLASS}[data-risk="potentially_unfair"] {
      background: rgba(234, 179, 8, 0.15);
      border-bottom: 2px solid #EAB308;
    }
    .${TOOLTIP_CLASS} {
      position: absolute;
      bottom: calc(100% + 6px);
      left: 50%;
      transform: translateX(-50%);
      background: #1E293B;
      color: #F1F5F9;
      padding: 6px 10px;
      border-radius: 6px;
      font-size: 12px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      white-space: nowrap;
      z-index: 999999;
      pointer-events: none;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      opacity: 0;
      transition: opacity 0.15s;
    }
    .${HIGHLIGHT_CLASS}:hover .${TOOLTIP_CLASS} {
      opacity: 1;
    }
  `;
  document.head.appendChild(style);


  /**
   * Extract main text content from the page.
   */
  function extractText() {
    const selectors = [
      'article', 'main', '[role="main"]',
      '.terms', '.privacy-policy', '.tos', '.legal',
      '.content', '.post-content', '.entry-content',
      '#content', '#main-content'
    ];

    let container = null;
    for (const sel of selectors) {
      container = document.querySelector(sel);
      if (container && container.innerText.trim().length > 200) break;
      container = null;
    }
    if (!container) container = document.body;

    // Clone and strip non-content elements
    const clone = container.cloneNode(true);
    clone.querySelectorAll(
      'nav, footer, header, aside, [role="navigation"], script, style, noscript, iframe, svg, img, video, audio, .cookie-banner, .nav, .sidebar, .footer, .header, .menu'
    ).forEach(el => el.remove());

    return clone.innerText.trim();
  }


  /**
   * Highlight matching clauses in the live page.
   * Uses substring matching on text nodes via TreeWalker.
   */
  function highlightClauses(clauses) {
    // Clear any existing highlights first
    clearHighlights();

    const flagged = clauses.filter(c => c.label !== 'fair');
    if (!flagged.length) return 0;

    let highlighted = 0;

    for (const clause of flagged) {
      // Use a distinctive substring for matching (first ~100 chars)
      const searchText = clause.clause.substring(0, 100).trim();
      if (searchText.length < 20) continue;

      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null
      );

      let node;
      while ((node = walker.nextNode())) {
        const text = node.textContent;
        const idx = text.toLowerCase().indexOf(searchText.toLowerCase().substring(0, 60));
        if (idx === -1) continue;

        // Skip nodes inside our own highlights or hidden elements
        const parent = node.parentElement;
        if (!parent || parent.closest(`.${HIGHLIGHT_CLASS}`) || parent.closest('script, style, noscript')) continue;

        try {
          // Find the full clause extent in this text node
          const matchLength = Math.min(clause.clause.length, text.length - idx);
          const range = document.createRange();
          range.setStart(node, idx);
          range.setEnd(node, idx + matchLength);

          const span = document.createElement('span');
          span.className = HIGHLIGHT_CLASS;
          span.dataset.risk = clause.label;
          span.dataset.confidence = clause.confidence;

          // Tooltip
          const labelText = clause.label === 'unfair' ? 'Clearly Unfair' : 'Potentially Unfair';
          const tooltip = document.createElement('span');
          tooltip.className = TOOLTIP_CLASS;
          tooltip.textContent = `${labelText} — ${Math.round(clause.confidence * 100)}% confidence`;
          span.appendChild(tooltip);

          range.surroundContents(span);
          highlighted++;
        } catch (e) {
          // Range may cross element boundaries — skip gracefully
        }
        break; // Only highlight first occurrence of each clause
      }
    }

    return highlighted;
  }


  /**
   * Remove all TermsAnalyzer highlights from the page.
   */
  function clearHighlights() {
    document.querySelectorAll(`.${HIGHLIGHT_CLASS}`).forEach(span => {
      // Remove tooltips
      span.querySelectorAll(`.${TOOLTIP_CLASS}`).forEach(t => t.remove());
      // Unwrap the span
      const parent = span.parentNode;
      while (span.firstChild) {
        parent.insertBefore(span.firstChild, span);
      }
      parent.removeChild(span);
    });
    // Normalize adjacent text nodes
    document.body.normalize();
  }


  // Listen for messages from the side panel
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'EXTRACT_TEXT') {
      const text = extractText();
      sendResponse({ text, url: window.location.href, title: document.title });
    }

    if (message.type === 'HIGHLIGHT_CLAUSES') {
      const count = highlightClauses(message.clauses);
      sendResponse({ highlighted: count });
    }

    if (message.type === 'CLEAR_HIGHLIGHTS') {
      clearHighlights();
      sendResponse({ ok: true });
    }

    return true;
  });
})();
