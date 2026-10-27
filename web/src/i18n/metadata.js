// Small eager metadata; translation catalogs are loaded separately.
export const supportedLocales = [
  {
    "id": "en",
    "name": "English",
    "dir": "ltr"
  },
  {
    "id": "zh-CN",
    "name": "简体中文",
    "dir": "ltr"
  },
  {
    "id": "zh-TW",
    "name": "繁體中文",
    "dir": "ltr"
  },
  {
    "id": "es",
    "name": "Español",
    "dir": "ltr"
  },
  {
    "id": "fr",
    "name": "Français",
    "dir": "ltr"
  },
  {
    "id": "de",
    "name": "Deutsch",
    "dir": "ltr"
  },
  {
    "id": "pt-BR",
    "name": "Português (Brasil)",
    "dir": "ltr"
  },
  {
    "id": "ja",
    "name": "日本語",
    "dir": "ltr"
  },
  {
    "id": "ko",
    "name": "한국어",
    "dir": "ltr"
  },
  {
    "id": "cs",
    "name": "Čeština",
    "dir": "ltr"
  },
  {
    "id": "ar",
    "name": "العربية",
    "dir": "rtl"
  }
];
export function normalizeLocale(value) { return supportedLocales.some((item) => item.id === value) ? value : 'en'; }
