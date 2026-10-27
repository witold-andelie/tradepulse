import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifest = JSON.parse(readFileSync(path.join(root, "vendor-manifest.json"), "utf8"));
for (const [name, expected] of Object.entries(manifest.files)) {
  const bytes = Buffer.from(readFileSync(path.join(root, "vendor", name), "utf8").replace(/\r\n/g, "\n"));
  const actual = createHash("sha1").update(`blob ${bytes.length}\0`).update(bytes).digest("hex");
  if (actual !== expected) throw new Error(`Vendored upstream file changed: ${name}`);
}
console.log(JSON.stringify({ status: "ok", files: Object.keys(manifest.files).length, commit: manifest.commit }));
