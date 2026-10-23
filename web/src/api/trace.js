/** Parse JSONL without dropping events or depending on the file's line endings. */
export function parseTraceLines(source) {
  return source.split(/\r?\n/).filter((line) => line.trim()).map((line) => JSON.parse(line));
}
