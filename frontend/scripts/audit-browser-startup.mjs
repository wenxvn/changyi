import { chromium } from "@playwright/test";
const browser = await chromium.launch({headless:true});
try {
  const page = await browser.newPage();
  page.on("pageerror",error=>console.log("PAGE_ERROR",error.message));
  page.on("console",message=>{if(message.type()==="error")console.log("CONSOLE_ERROR",message.text());});
  page.on("request",request=>{if(request.url().includes("/api/"))console.log("API_REQUEST",request.method(),new URL(request.url()).pathname);});
  await page.goto("http://127.0.0.1:5002/triage");
  await page.locator("#triage-condition").fill("咳嗽");
  const button=page.getByRole("button",{name:"查看安全状态"});
  await button.click();
  await page.waitForTimeout(1000);
  console.log("FORM_STATE",await page.locator("#triage-condition").count());
} finally { await browser.close(); }
