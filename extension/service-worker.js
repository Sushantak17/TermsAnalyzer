/**
 * TermsAnalyzer — Service Worker (Background Script)
 *
 * Opens the side panel when the extension icon is clicked.
 * Handles badge updates based on analysis risk level.
 */

// Open side panel on extension icon click
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });

// Listen for badge update messages from the side panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'UPDATE_BADGE') {
    const { risk } = message;
    let text = '';
    let color = '#22C55E';

    if (risk === 'Very High Risk') {
      text = '!!';
      color = '#DC2626';
    } else if (risk === 'High Risk') {
      text = '!';
      color = '#EF4444';
    } else if (risk === 'Medium Risk') {
      text = '~';
      color = '#EAB308';
    } else if (risk === 'Low Risk') {
      text = '✓';
      color = '#22C55E';
    }

    chrome.action.setBadgeText({ text });
    chrome.action.setBadgeBackgroundColor({ color });
    sendResponse({ ok: true });
  }

  if (message.type === 'CLEAR_BADGE') {
    chrome.action.setBadgeText({ text: '' });
    sendResponse({ ok: true });
  }

  return true;
});
