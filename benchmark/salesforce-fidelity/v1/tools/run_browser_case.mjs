#!/usr/bin/env node
import { createHash } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { chromium } from "playwright";

function argument(name, fallback = null) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : fallback;
}

const descriptorPath = path.resolve(argument("--descriptor", "execution.json"));
const artifactDir = path.resolve(argument("--artifacts", "evidence/playwright"));
const descriptor = JSON.parse(await readFile(descriptorPath, "utf8"));
const browserContract = descriptor.browser;
const instanceUrl =
  process.env.SCRATCH_ORG_INSTANCE_URL || browserContract.base_url;
const accessToken = process.env.SF_ACCESS_TOKEN;

if (!instanceUrl || instanceUrl.includes("${") || !accessToken) {
  throw new Error(
    "SCRATCH_ORG_INSTANCE_URL and SF_ACCESS_TOKEN are required for browser execution",
  );
}

await mkdir(artifactDir, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  recordVideo: { dir: artifactDir },
});
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
const page = await context.newPage();
const frontdoor = new URL("/secur/frontdoor.jsp", instanceUrl);
frontdoor.searchParams.set("sid", accessToken);
frontdoor.searchParams.set("retURL", browserContract.route);

let resultText = "";
let videoPath = null;
try {
  await page.goto(frontdoor.toString(), { waitUntil: "domcontentloaded" });
  const action = page.locator(browserContract.selectors.action);
  const result = page.locator(browserContract.selectors.result);
  await action.waitFor({ state: "visible" });
  await action.click();
  await result.waitFor({ state: "visible" });
  await page.waitForFunction(
    (selector) => {
      const value = document.querySelector(selector)?.textContent?.trim();
      return value && value !== "Not run" && value !== "RUNNING";
    },
    browserContract.selectors.result,
  );
  resultText = (await result.textContent())?.trim() || "";
  const parsed = JSON.parse(resultText);
  if (parsed.error) {
    throw new Error(`Harness returned an observed error: ${parsed.error}`);
  }
  await page.screenshot({
    path: path.join(artifactDir, "final-state.png"),
    fullPage: true,
  });
  videoPath = await page.video()?.path();
} finally {
  await context.tracing.stop({ path: path.join(artifactDir, "trace.zip") });
  await context.close();
  await browser.close();
}

if (videoPath) {
  await rename(videoPath, path.join(artifactDir, "video.webm"));
}
const resultSha256 = createHash("sha256").update(resultText).digest("hex");
await writeFile(
  path.join(artifactDir, "browser-result.json"),
  `${JSON.stringify(
    {
      case_id: descriptor.case_id,
      observed_result: JSON.parse(resultText),
      observed_result_sha256: resultSha256,
      observed_at: new Date().toISOString(),
    },
    null,
    2,
  )}\n`,
  "utf8",
);
