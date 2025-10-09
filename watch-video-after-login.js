// watch-video-after-login.js
// ماژولی که قابلیت تماشای ویدئو را فراهم می‌کند.
// Export شده: watchVideoWithDriver(driver, username) و watchVideoWithCookies(username)

const fs = require("fs");
const path = require("path");
const { Builder } = require("selenium-webdriver");
const chrome = require("selenium-webdriver/chrome");

const VIDEO_URL = "https://www.instagram.com/reel/DIB2dl6KM2_/";
const COOKIES_DIR = path.join("data", "cookies");
const REPORT_FILE = path.join("data", "report.json");

const sleep = ms => new Promise(r => setTimeout(r, ms));
const rint = (a,b) => Math.floor(Math.random()*(b-a)+a);

function ensureReport() {
  if (!fs.existsSync(path.dirname(REPORT_FILE))) fs.mkdirSync(path.dirname(REPORT_FILE), { recursive: true });
  if (!fs.existsSync(REPORT_FILE)) fs.writeFileSync(REPORT_FILE, JSON.stringify({}, null, 2), "utf8");
}

async function humanScroll(driver) {
  try {
    await driver.executeScript(`window.scrollBy(0, ${rint(250, 900)});`);
    await sleep(rint(250, 900));
    await driver.executeScript(`window.scrollBy(0, -${rint(80, 500)});`);
  } catch {}
}
async function humanMouseMove(driver) {
  try {
    await driver.executeScript(`
      (function(){
        const e = new MouseEvent('mousemove',{bubbles:true,cancelable:true,clientX: Math.random()*800, clientY: Math.random()*600});
        document.dispatchEvent(e);
      })();
    `);
    await sleep(rint(200, 500));
  } catch {}
}

async function loadCookiesIntoDriver(driver, username) {
  const cookiePath = path.join(COOKIES_DIR, `${username}.json`);
  if (!fs.existsSync(cookiePath)) throw new Error("cookies not found for " + username);
  const cookies = JSON.parse(fs.readFileSync(cookiePath, "utf8"));
  await driver.get("https://www.instagram.com/");
  await sleep(1500);
  for (const c of cookies) {
    const cc = {
      name: c.name,
      value: c.value,
      path: c.path || "/",
      domain: c.domain || ".instagram.com",
      httpOnly: !!c.httpOnly,
      secure: !!c.secure,
      ...(c.expiry ? { expiry: c.expiry } : {})
    };
    try { await driver.manage().addCookie(cc); } catch (e) { /* ignore */ }
  }
  await driver.navigate().refresh();
  await sleep(1500);
}

async function isAccountBlocked(driver) {
  try {
    const currentUrl = await driver.getCurrentUrl();
    if (/checkpoint|consent/i.test(currentUrl)) return true;
    const title = await driver.getTitle().catch(()=> "");
    if (!/Instagram/i.test(title)) return true;
    return false;
  } catch {
    return true;
  }
}

async function watchVideoWithDriver(driver, username) {
  ensureReport();
  const reportData = JSON.parse(fs.readFileSync(REPORT_FILE, "utf8") || "{}");
  const record = { views: 0, status: "unknown", ts: new Date().toISOString() };

  try {
    if (!driver) throw new Error("driver is required for watchVideoWithDriver");
    if (await isAccountBlocked(driver)) {
      record.status = "blocked";
      reportData[username] = record;
      fs.writeFileSync(REPORT_FILE, JSON.stringify(reportData, null, 2), "utf8");
      return record;
    }

    for (let i = 0; i < 4; i++) {
      await driver.get(VIDEO_URL);
      await sleep(Math.random() * (6000-4000) + 4000);
      await humanScroll(driver);
      await humanMouseMove(driver);

      const watchTime = rint(15, 25);
      await sleep(watchTime * 1000);

      record.views += 1;

      if (i < 3) await sleep(1000);
    }

    record.status = record.views === 4 ? "success" : "partial";
  } catch (e) {
    record.status = "error";
    record.error = e && e.message ? e.message : String(e);
  } finally {
    record.finished = new Date().toISOString();
    reportData[username] = record;
    fs.writeFileSync(REPORT_FILE, JSON.stringify(reportData, null, 2), "utf8");
    return record;
  }
}

async function watchVideoWithCookies(username) {
  ensureReport();
  const options = new chrome.Options();
  options.addArguments("--mute-audio");
  const driver = await new Builder().forBrowser("chrome").setChromeOptions(options).build();
  try {
    await loadCookiesIntoDriver(driver, username);
    const res = await watchVideoWithDriver(driver, username);
    return res;
  } finally {
    try { await driver.quit(); } catch {}
  }
}

module.exports = {
  watchVideoWithDriver,
  watchVideoWithCookies
};
