const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join, resolve, dirname } = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

// Execute the actual TSX components with React's server renderer; no DOM or event simulation.
function load(relativePath, cache = new Map()) {
  const filename = resolve(__dirname, "..", relativePath);
  if (cache.has(filename)) return cache.get(filename);
  const exports = {};
  cache.set(filename, exports);
  const output = ts.transpileModule(readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022 },
  });
  vm.runInNewContext(output.outputText, {
    exports,
    require: (name) => {
      if (!name.startsWith("@/") && !name.startsWith(".")) return require(name);
      const base = name.startsWith("@/") ? resolve(__dirname, "..", name.slice(2)) : resolve(dirname(filename), name);
      for (const extension of [".ts", ".tsx"]) {
        try { return load(base + extension, cache); } catch (error) { if (error.code !== "ENOENT") throw error; }
      }
      throw new Error(`Module missing: ${name}`);
    },
  }, { filename });
  return exports;
}

const render = (Component, props) => renderToStaticMarkup(React.createElement(Component, props));

test("Markdown renders headings, lists, emphasis and CRLF paragraphs", () => {
  const Markdown = load("components/Markdown.tsx").default;
  const html = render(Markdown, { source: "### Air\r\n\r\nAir **bersih** dan *sehat*.\r\n\r\n- Minum\r\n- Mandi" });
  assert.match(html, /<h3[^>]*>.*Air<\/h3>/);
  assert.match(html, /<strong>bersih<\/strong>/);
  assert.match(html, /<em>sehat<\/em>/);
  assert.equal((html.match(/<li /g) || []).length, 2);
});

test("Markdown escapes teacher and generated HTML rather than executing it", () => {
  const Markdown = load("components/Markdown.tsx").default;
  const html = render(Markdown, { source: '<script>alert("x")</script>\n\n<img src=x onerror=alert(1)>\n\n[klik](javascript:alert(1))' });
  assert.ok(!html.includes("<script"));
  assert.ok(!html.includes("<img"));
  assert.ok(!html.includes("<a "));
  assert.match(html, /&lt;script&gt;/);
});

test("Stars render the accessible score at each passing threshold", () => {
  const Stars = load("components/Stars.tsx").default;
  for (const [percent, expected] of [[0, 0], [69, 0], [70, 1], [84, 1], [85, 2], [99, 2], [100, 3]]) {
    assert.match(render(Stars, { percent }), new RegExp(`role="img" aria-label="${expected} dari 3 bintang"`));
  }
});

test("AnswerTile exposes selected and disabled state without leaking result before closure", () => {
  const AnswerTile = load("components/AnswerTile.tsx").default;
  const idle = render(AnswerTile, { index: 0, label: "Akar", state: "idle" });
  assert.match(idle, /aria-pressed="false"/);
  assert.ok(!idle.includes("disabled="));
  assert.ok(!idle.includes("<span class=\"rounded-full"));
  const chosen = render(AnswerTile, { index: 1, label: "Batang", state: "chosen", disabled: true });
  assert.match(chosen, /disabled=""/);
  assert.match(chosen, /aria-pressed="true"/);
  assert.match(chosen, />B<\/span>/);
  const closed = render(AnswerTile, { index: 2, label: "Daun", state: "correct", disabled: true, count: 7 });
  assert.match(closed, />7<\/span>/);
});

test("RoleChooser renders both modes with exactly one active choice", () => {
  const RoleChooser = load("components/RoleChooser.tsx").default;
  for (const role of ["student", "teacher"]) {
    const html = render(RoleChooser, { value: role, onChange: () => {} });
    assert.equal((html.match(/aria-pressed="true"/g) || []).length, 1);
    assert.equal((html.match(/type="button"/g) || []).length, 2);
    assert.match(html, /Murid/);
    assert.match(html, /Guru/);
  }
});


test("PDF source labels convert internal zero-based pages for display", () => {
  const { formatSource } = load("lib/levels.ts");
  assert.equal(formatSource({ page_start: 0, page_end: 0, section_title: "Air" }), "Hal. 1 - Air");
  assert.equal(formatSource({ page_start: 0, page_end: 2, section_title: "" }), "Hal. 1-3");
  assert.equal(formatSource({ page_start: 9, page_end: 11, section_title: "Hujan" }), "Hal. 10-12 - Hujan");
});
