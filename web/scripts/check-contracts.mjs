// Validate the contract fixtures against contracts/api/tradepulse.schema.json.
// Usage: npm run check:contracts            (validates the committed fixtures)
//        node scripts/check-contracts.mjs path/to/run_output.json   (validates another file)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';

const contracts = fileURLToPath(new URL('../../contracts/', import.meta.url));
const schema = JSON.parse(readFileSync(`${contracts}api/tradepulse.schema.json`, 'utf8'));

const ajv = new Ajv2020({ allErrors: true, strict: false });
addFormats(ajv);
ajv.addSchema(schema);
const validateRun = ajv.getSchema(schema.$id);
const validateTrace = ajv.getSchema(`${schema.$id}#/$defs/TraceEvent`);

function report(label, ok, errors) {
  if (ok) {
    console.log(`ok   ${label}`);
    return 0;
  }
  console.error(`FAIL ${label}`);
  for (const e of (errors || []).slice(0, 20)) console.error(`     ${e.instancePath || '<root>'} ${e.message}`);
  return 1;
}

let failures = 0;
const runPath = process.argv[2] || `${contracts}fixtures/run_output.fixture.json`;
const run = JSON.parse(readFileSync(runPath, 'utf8'));
failures += report(runPath, validateRun(run), validateRun.errors);

if (!process.argv[2]) {
  const lines = readFileSync(`${contracts}fixtures/trace.fixture.jsonl`, 'utf8').split('\n').filter(Boolean);
  lines.forEach((line, i) => {
    failures += report(`trace line ${i + 1}`, validateTrace(JSON.parse(line)), validateTrace.errors);
  });
}
process.exit(failures ? 1 : 0);
