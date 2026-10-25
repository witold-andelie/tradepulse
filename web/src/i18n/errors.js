// Presentation of client-owned diagnostics. The API transport and validation are unchanged.
export const fixedErrors = [
  'Request cancelled. Please try again.', 'The request timed out. Please try again.',
  'Unable to load TradePulse data. Please check the connection and try again.',
  'The trace response was invalid. Please try again.', 'No API configured: showing fixtures',
  'Data could not be loaded. Please retry.',
  'Unable to reach the API. Check the configured service and retry. No fixture fallback was substituted.',
  'Malformed JSON response. Please retry or contact the data provider.',
];
export function errorSummary(message, t) {
  if (t.locale === 'en') return message;
  if (fixedErrors.includes(message)) return t(message);
  const status = /HTTP (\d{3})/.exec(message)?.[1];
  if (status) return t('API request failed (HTTP {status}). Retry; no fixture data was substituted.', { status });
  if (/^Invalid /.test(message)) return t('The response failed contract validation. No records were discarded. Inspect the original diagnostic.');
  return t('The request could not be completed. Inspect the original technical diagnostic.');
}
