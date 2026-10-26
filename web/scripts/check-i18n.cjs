// Uses Babel already present in the locked Vite/React toolchain; no new dependency.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const root = path.resolve(__dirname, '../src');
const english = require('../src/i18n/en.json');
const locales = ['zh-CN', 'zh-TW', 'es', 'fr', 'de', 'pt-BR', 'ja', 'ko', 'cs', 'ar'];
const placeholders = (text) => [...new Set([...text.matchAll(/\{([a-zA-Z]\w*)\}/g)].map((match) => match[1]))].sort();
for (const locale of locales) {
  const dictionary = require(`../src/i18n/locales/${locale}.json`);
  assert.deepEqual(Object.keys(dictionary).sort(), Object.keys(english).sort(), `${locale}: key mismatch`);
  for (const key of Object.keys(english)) {
    assert.equal(typeof dictionary[key], 'string', `${locale}: ${key}`);
    assert(dictionary[key].trim(), `${locale}: empty ${key}`);
    assert.deepEqual(placeholders(dictionary[key]), placeholders(english[key]), `${locale}: placeholders ${key}`);
  }
}
const files = ['App.jsx', ...['Discover', 'Leaderboard', 'Detail', 'Factors', 'Regime', 'TrackRecord', 'Trace'].map((name) => `pages/${name}.jsx`), ...['ui', 'ResearchGuide', 'CandidateCard', 'ChartFigure', 'State'].map((name) => `components/${name}.jsx`), 'i18n/Locale.jsx'];
const sites = [];
const literalFailures = [];
const allowedText = new Set(['TradePulse', 'i', 'n', 'ms', 's', 'bp', 'IC', 'UTC']);
for (const file of files) {
  const source = fs.readFileSync(path.join(root, file), 'utf8');
  const ast = parser.parse(source, { sourceType: 'module', plugins: ['jsx'] });
  const record = (key, line) => {
    if (key.startsWith('guide.')) return;
    assert(Object.hasOwn(english, key), `${file}:${line} missing authored key ${key}`);
    sites.push({ file, line, key });
  };
  traverse(ast, {
    CallExpression(p) { if (p.node.callee.name === 't' && p.node.arguments[0]?.type === 'StringLiteral') record(p.node.arguments[0].value, p.node.loc.start.line); },
    JSXAttribute(p) { if (p.node.name.name === 'text' && p.node.value?.type === 'StringLiteral') record(p.node.value.value, p.node.loc.start.line); },
    JSXText(p) {
      const text = p.node.value.replace(/\s+/g, ' ').trim();
      if (!/[A-Za-z]/.test(text) || allowedText.has(text)) return;
      if (p.findParent((node) => node.isJSXElement() && node.node.openingElement.attributes.some((attribute) => attribute.name?.name === 'aria-hidden' && attribute.value?.value === 'true'))) return;
      literalFailures.push(`${file}:${p.node.loc.start.line}: ${text}`);
    },
  });
}
assert.deepEqual(literalFailures, [], 'Unregistered literal application text remains');
console.log(`PASS: ${Object.keys(english).length} application keys in 11 locales; all placeholders and nonempty values match.`);
console.log(`PASS: ${sites.length} explicit authored source sites; no remaining English JSX prose outside declared brands/technical tokens.`);
if (process.env.TRADEPULSE_I18N_INVENTORY) fs.writeFileSync(process.env.TRADEPULSE_I18N_INVENTORY, JSON.stringify(sites, null, 2));
