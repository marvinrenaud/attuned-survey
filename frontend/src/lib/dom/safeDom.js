// frontend/src/lib/dom/safeDom.js
export function safeMatches(el, selector) {
  return !!(el && typeof el.matches === 'function' && el.matches(selector));
}

export function safeClosest(el, selector) {
  if (!el || typeof el.closest !== 'function') return null;
  try { return el.closest(selector) || null; } catch { return null; }
}

export function isBrowser() {
  return typeof window !== 'undefined' && typeof document !== 'undefined';
}


