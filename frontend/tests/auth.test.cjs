const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

function harness(browser = true) {
  const exports = {};
  const values = new Map();
  const localStorage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
  const output = ts.transpileModule(readFileSync(join(__dirname, "../lib/auth.ts"), "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 },
  });
  vm.runInNewContext(output.outputText, { exports, localStorage, ...(browser ? { window: {} } : {}) });
  return { ...exports, values };
}

test("authentication stores, reads and removes the final brand token key", () => {
  const auth = harness();
  auth.saveToken("test-token");
  assert.equal(auth.values.get("petapintar_token"), "test-token");
  assert.equal(auth.values.size, 1);
  assert.equal(auth.getToken(), "test-token");
  auth.clearToken();
  assert.equal(auth.getToken(), null);
  assert.equal(auth.values.size, 0);
});

test("authentication stays signed out when rendering on the server", () => {
  assert.equal(harness(false).getToken(), null);
});
