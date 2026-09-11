import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const sourceRoot = new URL("../src/", import.meta.url);
const productFiles = [
  "pages/HomePage.tsx",
  "pages/TriagePage.tsx",
  "pages/ResourcesPage.tsx",
  "pages/MapPage.tsx",
  "pages/ProfilePage.tsx",
  "components/medical/TriageResults.tsx",
  "components/visualization/JourneyPreview.tsx",
];

const forbiddenProductCopy = [
  "提示词",
  "参赛",
  "竞赛",
  "比赛",
  "评委",
  "获奖",
  "后端安全门",
  "后端返回",
  "来源迁移中",
  "地图（建设中）",
  "打开地图（建设中）",
  "非导航地图",
  "已从 v1 读取",
  "资源推荐会单独从 v1 获取",
];

test("ordinary product surfaces do not expose forbidden competition or engineering copy", async () => {
  const contents = await Promise.all(productFiles.map((file) => readFile(new URL(file, sourceRoot), "utf8")));
  const joined = contents.join("\n");

  for (const phrase of forbiddenProductCopy) {
    assert.equal(joined.includes(phrase), false, `forbidden product copy remains: ${phrase}`);
  }
});

test("technical evidence remains available behind an explicit disclosure", async () => {
  const trustPage = await readFile(new URL("pages/TrustPage.tsx", sourceRoot), "utf8");
  assert.match(trustPage, /<details className="trust-technical-details">/);
  assert.match(trustPage, /技术详情/);
});
