// Test-only preload preserves all existing synchronous catalog assertions while
// production imports stay lazy. This file is never imported by application code.
import { supportedLocales, loadCatalog, loadGuideCatalog } from './catalog.js';
await Promise.all(supportedLocales.map(async ({ id }) => { await loadCatalog(id); await loadGuideCatalog(id); }));
