import { test } from "node:test";
import assert from "node:assert/strict";
import { parseTavilyResult } from "./parse-tavily.ts";

test("returns [] for empty / no results", () => {
  assert.deepEqual(parseTavilyResult(""), []);
  assert.deepEqual(parseTavilyResult("No web results found."), []);
});

test("parses two results separated by blank line", () => {
  const raw = "Title A\nhttps://a.example\nbody A line 1\nbody A line 2\n\nTitle B\nhttps://b.example\nbody B";
  const out = parseTavilyResult(raw);
  assert.equal(out.length, 2);
  assert.equal(out[0].title, "Title A");
  assert.equal(out[0].url, "https://a.example");
  assert.equal(out[0].content, "body A line 1\nbody A line 2");
  assert.equal(out[1].url, "https://b.example");
});

test("skips malformed blocks (single line)", () => {
  const out = parseTavilyResult("orphan line");
  assert.equal(out.length, 0);
});
