const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { join } = require("node:path");
const { test } = require("node:test");
const vm = require("node:vm");
const ts = require("typescript");

function harness(throws = false) {
  const timers = new Map();
  const intervals = new Map();
  const sockets = [];
  let nextId = 0;
  class Socket {
    constructor() {
      if (throws) throw new Error("WebSocket unavailable");
      sockets.push(this);
    }
    close() { this.onclose?.(); }
  }
  const exports = {};
  const context = {
    exports,
    require: () => ({ getToken: () => "token" }),
    process: { env: {} },
    WebSocket: Socket,
    setTimeout: (fn) => { timers.set(++nextId, fn); return nextId; },
    clearTimeout: (id) => timers.delete(id),
    setInterval: (fn) => { intervals.set(++nextId, fn); return nextId; },
    clearInterval: (id) => intervals.delete(id),
  };
  const source = readFileSync(join(__dirname, "../lib/realtime.ts"), "utf8");
  const output = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } });
  vm.runInNewContext(output.outputText, context);
  return { connect: exports.connectRealtime, sockets, timers, intervals };
}

test("polls at startup, reconnect and disconnect; cleanup leaves no timers", () => {
  const h = harness();
  let polls = 0;
  const stop = h.connect("/ws/live/session", () => {}, () => { polls++; });
  assert.equal(polls, 1);
  h.sockets[0].onopen();
  assert.equal(polls, 2);
  assert.equal(h.intervals.size, 1);
  h.sockets[0].onclose();
  assert.equal(h.timers.size, 1);
  const retry = [...h.timers.values()][0];
  retry();
  assert.equal(h.sockets.length, 2);
  h.sockets[1].onopen();
  assert.equal(polls, 3);
  stop();
  assert.equal(h.intervals.size, 0);
  assert.equal(h.timers.size, 0);
});

test("constructor failure keeps polling and schedules a reconnect", () => {
  const h = harness(true);
  let polls = 0;
  const stop = h.connect("/ws/live/session", () => {}, () => { polls++; });
  assert.equal(polls, 1);
  assert.equal(h.intervals.size, 1);
  assert.equal(h.timers.size, 1);
  stop();
  assert.equal(h.intervals.size, 0);
  assert.equal(h.timers.size, 0);
});
