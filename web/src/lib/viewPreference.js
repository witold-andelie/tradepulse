// Persist only a non-sensitive presentation preference. Storage can be unavailable.
export const VIEW_KEY = 'tradepulse.view';
export const normalizeView = (value) => value === 'pro' ? 'pro' : 'simple';
export function readView(storage) {
  try { return normalizeView(storage?.getItem(VIEW_KEY)); } catch { return 'simple'; }
}
export function writeView(storage, value) {
  try { storage?.setItem(VIEW_KEY, normalizeView(value)); return Boolean(storage); } catch { return false; }
}
