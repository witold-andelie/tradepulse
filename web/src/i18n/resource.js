// Only validated, successfully loaded resources enter the cache. Failed imports
// are evicted so explicit retries can recover without reloading the application.
export function createCachedLoader(importers, validate = (value) => value, initial = {}) {
  const loaded = new Map(Object.entries(initial));
  const pending = new Map();
  const attempts = new Map();
  function load(id) {
    if (loaded.has(id)) return Promise.resolve(loaded.get(id));
    if (pending.has(id)) return pending.get(id);
    if (!Object.hasOwn(importers, id)) return Promise.reject(new Error('Unsupported catalog'));
    const attempt = attempts.get(id) || 0;
    attempts.set(id, attempt + 1);
    const request = Promise.resolve().then(() => importers[id](attempt)).then((module) => {
      const value = validate(module.default ?? module, id);
      loaded.set(id, value);
      return value;
    }).finally(() => pending.delete(id));
    pending.set(id, request);
    return request;
  }
  return { load, has: (id) => loaded.has(id), get: (id) => loaded.get(id) };
}

// Browsers cache a rejected ESM fetch for the current document. Explicit retries
// use the same versioned, same-origin JSON asset, keeping route and view state.
// The caller still validates the complete catalog before caching or activation.
export async function retryJsonCatalog(url) {
  if (typeof window !== 'undefined' && new URL(url).origin !== window.location.origin) throw new Error('Catalog must be same-origin');
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(url, { signal: controller.signal, cache: 'reload', credentials: 'same-origin' });
    if (!response.ok) throw new Error('Catalog asset unavailable');
    return await response.json();
  } finally { clearTimeout(timer); }
}
