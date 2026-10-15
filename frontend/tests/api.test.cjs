const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

function harness(response) {
  const calls = [];
  const exports = {};
  const source = readFileSync(join(__dirname, "../lib/api.ts"), "utf8");
  const output = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } });
  vm.runInNewContext(output.outputText, {
    exports,
    require: () => ({ getToken: () => "private-token" }),
    process: { env: {} },
    fetch: async (...args) => { calls.push(args); return response; },
  });
  return { api: exports.api, calls };
}

test("PDF uses authenticated API request and returns a blob", async () => {
  const blob = new Blob(["%PDF-1.4"], { type: "application/pdf" });
  const h = harness({ ok: true, status: 200, blob: async () => blob });
  const controller = new AbortController();
  const result = await h.api.getMaterialPdf("class", "material", controller.signal);
  assert.equal(result, blob);
  assert.equal(h.calls[0][0], "http://localhost:8000/api/v1/classes/class/materials/material/file");
  assert.equal(h.calls[0][1].headers.Authorization, "Bearer private-token");
  assert.equal(h.calls[0][1].signal, controller.signal);
  assert.ok(!h.calls[0][0].includes("private-token"));
});

test("next live question submits the current question ID", async () => {
  const h = harness({ ok: true, status: 204 });
  await h.api.nextLiveQuestion("session", "question");
  assert.deepEqual(JSON.parse(h.calls[0][1].body), { question_id: "question" });
});
