import { describe, expect, it } from 'vitest';
import { dataModeBanner } from './data.js';

describe('run-aware provenance', () => {
  it.each([{ explanations: [] }, { explanations: [{ verdict: 'abstained' }] }, { explanations: [{ verdict: 'explained' }] }])(
    'does not infer successful hosted models from REPLAY or explanation verdicts: %j',
    (run) => {
      const banner = dataModeBanner('REPLAY', { data_mode: 'REPLAY', ...run });
      expect(banner.show).toBe(true);
      expect(banner.text).toContain('model availability');
      expect(banner.text).not.toContain('with recorded model answers');
    },
  );
  it.each(['SYNTHETIC', 'REAL'])('preserves the existing %s disclosure', (mode) => {
    expect(dataModeBanner(mode, { data_mode: mode })).toEqual(dataModeBanner(mode));
  });
});
