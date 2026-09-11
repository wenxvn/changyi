import assert from "node:assert/strict";
import test from "node:test";

import { buildAmapNavigationUrl, openAmapNavigation } from "../src/utils/navigation.ts";

test("builds an AMap navigation URI for a hospital with coordinates", () => {
  const url = buildAmapNavigationUrl({
    name: "常州市第一人民医院",
    address: "局前街",
    lat: 31.7768,
    lng: 119.958,
  });

  assert.ok(url);
  const parsed = new URL(url);
  assert.equal(parsed.hostname, "uri.amap.com");
  assert.equal(parsed.pathname, "/navigation");
  assert.equal(parsed.searchParams.get("to"), "119.958,31.7768,常州市第一人民医院");
  assert.equal(parsed.searchParams.get("mode"), "car");
  assert.equal(parsed.searchParams.get("policy"), "1");
  assert.equal(parsed.searchParams.get("callnative"), "0");
});

test("falls back to an AMap search URL when only a hospital name or address exists", () => {
  const url = buildAmapNavigationUrl({ name: "常州儿童医院", address: "延陵中路" });

  assert.ok(url);
  const parsed = new URL(url);
  assert.equal(parsed.hostname, "www.amap.com");
  assert.equal(parsed.pathname, "/search");
  assert.equal(parsed.searchParams.get("query"), "常州儿童医院 延陵中路");
});

test("does not create a misleading navigation target without location information", () => {
  assert.equal(buildAmapNavigationUrl({}), null);
  assert.equal(buildAmapNavigationUrl({ lat: Number.NaN, lng: 119.9 }), null);
  assert.equal(buildAmapNavigationUrl({ lat: 31.7 }), null);
});

test("opens the exact generated URI in a new tab", () => {
  const calls = [];
  globalThis.window = {
    open(...args) {
      calls.push(args);
    },
  };

  const url = openAmapNavigation({ name: "常州市中医院", address: "和平北路" });

  assert.equal(calls.length, 1);
  assert.equal(calls[0][0], url);
  assert.equal(calls[0][1], "_blank");
  assert.equal(calls[0][2], "noopener,noreferrer");
  delete globalThis.window;
});
