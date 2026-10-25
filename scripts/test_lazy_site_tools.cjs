"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const src = fs.readFileSync("docs/javascripts/site-tools-loader.js", "utf8");
const base = "https://example.org/eyetrajectoriespy/javascripts/";

function simulate() {
  const ids = new Set(), loaded = [], subscriptions = [];
  let hasCollection = false;
  const document = {
    currentScript: { src: base + "site-tools-loader.js" },
    readyState: "complete",
    getElementById: id => ids.has(id) ? {} : null,
    querySelector: selector => selector === "[data-et-collection]" && hasCollection ? {} : null,
    createElement: tag => {
      assert.equal(tag, "script");
      return { dataset: {} };
    },
    head: { appendChild: node => {
      loaded.push(new URL(node.src).pathname);
      queueMicrotask(() => node.onload());
    } },
  };
  const document$ = { subscribe: fn => subscriptions.push(fn) };
  vm.runInNewContext(src, { document, document$, URL, Promise, console });
  const tick = () => new Promise(resolve => setImmediate(resolve));
  return { ids, loaded, subscriptions, tick, setCollection: value => { hasCollection = value; } };
}

async function run() {
  const ctx = simulate();
  await ctx.tick();
  assert.deepEqual(ctx.loaded, [], "The homepage should not load research tools");
  assert.equal(ctx.subscriptions.length, 1, "Must subscribe to Material instant navigation");

  ctx.ids.add("et-method");
  ctx.subscriptions[0]();
  await ctx.tick();
  assert.deepEqual(ctx.loaded, [
    "/eyetrajectoriespy/javascripts/interactive-explorers.js",
    "/eyetrajectoriespy/javascripts/method-sharing.js"
  ], "Method-sharing must follow interactive selector initialization");

  // A second event on the same route should not download the bundles again.
  ctx.subscriptions[0]();
  await ctx.tick();
  assert.equal(ctx.loaded.length, 2);

  ctx.ids.clear();
  ctx.ids.add("et-integration-navigator");
  ctx.subscriptions[0]();
  await ctx.tick();
  assert.equal(ctx.loaded.at(-1), "/eyetrajectoriespy/javascripts/integration-navigator.js");

  ctx.ids.clear();
  ctx.ids.add("et-data-audit");
  ctx.subscriptions[0]();
  await ctx.tick();
  assert.equal(ctx.loaded.at(-1), "/eyetrajectoriespy/javascripts/gaze-data-readiness.js");

  ctx.ids.clear();
  ctx.setCollection(true);
  ctx.subscriptions[0]();
  await ctx.tick();
  assert.equal(ctx.loaded.length, 4, "Explorer bundle should be reused on figure filters");
  assert.ok(ctx.loaded.every(path => path.startsWith("/eyetrajectoriespy/javascripts/")));
  console.log("PASS: no homepage bundle, route selection, instant-navigation reuse, script ordering");
}
run().catch(error => { console.error(error); process.exitCode = 1; });
