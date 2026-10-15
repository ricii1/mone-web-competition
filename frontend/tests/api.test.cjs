const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

function harness(response, { token = "private-token", apiUrl } = {}) {
  const calls = [];
  const exports = {};
  const source = readFileSync(join(__dirname, "../lib/api.ts"), "utf8");
  const output = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020 } });
  vm.runInNewContext(output.outputText, {
    exports,
    require: () => ({ getToken: () => token }),
    process: { env: { NEXT_PUBLIC_API_URL: apiUrl } },
    FormData,
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


test("public login omits bearer when signed out and honors configured API origin", async () => {
  const h = harness({ ok: true, status: 200, json: async () => ({ access_token: "new-token" }) }, {
    token: null, apiUrl: "https://api.example.test",
  });
  const result = await h.api.login("murid@example.test", "test-password");
  assert.equal(result.access_token, "new-token");
  assert.equal(h.calls[0][0], "https://api.example.test/api/v1/auth/login");
  assert.equal(h.calls[0][1].headers.Authorization, undefined);
  assert.deepEqual(JSON.parse(h.calls[0][1].body), { email: "murid@example.test", password: "test-password" });
});

test("API errors preserve server status and readable detail", async () => {
  const h = harness({ ok: false, status: 403, json: async () => ({ detail: "Kamu belum bergabung di kelas ini" }) });
  await assert.rejects(h.api.listLevels("class"), (error) => {
    assert.equal(error.status, 403);
    assert.equal(error.message, "Kamu belum bergabung di kelas ini");
    return true;
  });
});

test("non-JSON errors show a friendly Indonesian retry message", async () => {
  const h = harness({ ok: false, status: 502, statusText: "Bad Gateway", json: async () => { throw new SyntaxError("HTML response"); } });
  await assert.rejects(h.api.me(), (error) => error.status === 502 && error.message === "Layanan belum bisa dihubungi. Coba lagi ya.");
});

test("material upload uses browser multipart boundary and bearer authentication", async () => {
  const h = harness({ ok: true, status: 200, json: async () => ({ id: "material" }) });
  await h.api.uploadMaterial("class", new Blob(["%PDF-1.4"], { type: "application/pdf" }));
  const init = h.calls[0][1];
  assert.equal(init.method, "POST");
  assert.equal(init.headers.Authorization, "Bearer private-token");
  assert.equal(init.headers["Content-Type"], undefined);
  assert.ok(init.body instanceof FormData);
  assert.equal(await init.body.get("file").text(), "%PDF-1.4");
});

test("section preview paginates and forwards cancellation signal", async () => {
  const h = harness({ ok: true, status: 200, json: async () => ({ sections: [] }) });
  const controller = new AbortController();
  await h.api.listMaterialSections("class", "material", 20, controller.signal);
  assert.equal(h.calls[0][0], "http://localhost:8000/api/v1/classes/class/materials/material/sections?offset=20&limit=10");
  assert.equal(h.calls[0][1].signal, controller.signal);
});


test("validation details stay readable and do not expose rejected input", async () => {
  const detail = [{ loc: ["body", "name"], msg: "raw validation", input: "private-input" }, { loc: ["body", "password"], ctx: { secret: "private-context" } }];
  const h = harness({ ok: false, status: 422, json: async () => ({ detail }) });
  await assert.rejects(h.api.register("x", "x", "x", "student"), (error) => {
    assert.equal(error.status, 422);
    assert.match(error.message, /Nama, Kata sandi belum sesuai/);
    assert.doesNotMatch(error.message, /object Object|private|raw validation/);
    return true;
  });
});

test("JSON and upload share safe normalization for unknown and malformed errors", async () => {
  for (const detail of [{ message: "private-details" }, [{ loc: "malformed", msg: "private-details" }], null, 7, [null, "private-details"], [{ loc: ["__proto__", "constructor"] }]]) {
    const h = harness({ ok: false, status: 422, json: async () => ({ detail }) });
    for (const call of [() => h.api.me(), () => h.api.uploadMaterial("class", new Blob(["pdf"]))]) {
      await assert.rejects(call(), (error) => {
        assert.equal(error.status, 422);
        assert.match(error.message, /Coba lagi|coba lagi/);
        assert.doesNotMatch(error.message, /object Object|private-details/);
        return true;
      });
    }
  }
});
