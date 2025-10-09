// watch-video-after-login.js
// ماژولی برای تماشای Reel بعد از لاگین
// Export: watchVideoWithDriver(driver, username) و watchVideoWithCookies(username)

const fs = require("fs");
const path = require("path");
const { Builder, By } = require("selenium-webdriver");
const chrome = require("selenium-webdriver/chrome");

const VIDEO_URL = "https://www.instagram.com/reel/DGs2jGntCHJ/?utm_source=ig_web_copy_link";
const COOKIES_DIR = path.join("data", "cookies");
const REPORT_FILE = path.join("data", "report.json");

const sleep = ms => new Promise(r => setTimeout(r, ms));
const rint = (a,b) => Math.floor(Math.random()*(b-a)+a);

function ensureReport() {
  if (!fs.existsSync(path.dirname(REPORT_FILE))) fs.mkdirSync(path.dirname(REPORT_FILE), { recursive: true });
  if (!fs.existsSync(REPORT_FILE)) fs.writeFileSync(REPORT_FILE, JSON.stringify({}, null, 2), "utf8");
}

// ---------- Human-like interactions ----------
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
async function humanMoveAndClick(driver, element) {
  try {
    await driver.executeScript("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", element);
    await sleep(rint(120, 420));
    await element.click();
    await sleep(rint(120, 420));
    return true;
  } catch {
    return false;
  }
}

// ---------- Cookie loader ----------
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

// ---------- Block detection ----------
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

// ---------- Try click Play ----------
async function tryClickPlay(driver, timeoutMs = 5000) {
  const start = Date.now();
  const playSelector = '[aria-label="Play"]';

  while (Date.now() - start < timeoutMs) {
    try {
      // 1) direct CSS lookup
      const els = await driver.findElements(By.css(playSelector));
      for (const el of els) {
        try {
          const displayed = await el.isDisplayed().catch(()=>false);
          if (!displayed) continue;
        } catch {}
        const ok = await humanMoveAndClick(driver, el);
        if (ok) return true;
      }

      // 2) XPath lookup
      const xels = await driver.findElements(By.xpath('//*[@aria-label="Play"]'));
      for (const el of xels) {
        try {
          const displayed = await el.isDisplayed().catch(()=>false);
          if (!displayed) continue;
        } catch {}
        const ok = await humanMoveAndClick(driver, el);
        if (ok) return true;
      }

      // 3) some candidate selectors as fallback
      const cssCandidates = [
        'button[aria-label="Play"]',
        'div[aria-label="Play"]',
        'button[title*="Play"]',
        'div[class*="play"], button[class*="play"]'
      ];
      for (const sel of cssCandidates) {
        const cands = await driver.findElements(By.css(sel));
        for (const el of cands) {
          const ok = await humanMoveAndClick(driver, el);
          if (ok) return true;
        }
      }
    } catch (e) {
      // ignore and retry
    }
    await sleep(300);
  }

  // fallback: click center of viewport
  try {
    await driver.executeScript(`
      window.scrollTo(0, Math.max(0, (document.body.scrollHeight - window.innerHeight)/2));
    `);
    await sleep(300);
    await driver.executeScript(`
      (function(){
        const cx = Math.floor(window.innerWidth/2), cy = Math.floor(window.innerHeight/2);
        const el = document.elementFromPoint(cx, cy);
        if (el) {
          const ev = new MouseEvent('click', {bubbles:true, cancelable:true, clientX: cx, clientY: cy});
          el.dispatchEvent(ev);
        }
      })();
    `);
    await sleep(500);
    return true;
  } catch {
    return false;
  }
}

// ---------- Watch video using existing driver ----------
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
      await sleep(rint(4000, 6000));

      // try click Play (the exact aria-label element)
      try {
        await tryClickPlay(driver);
      } catch (e) {
        // ignore
      }

      await humanScroll(driver);
      await humanMouseMove(driver);

      const watchTime = rint(15, 25);
      console.log(`⏱️ [${username}] Watching ${watchTime}s for view ${i+1}`);
      await sleep(watchTime * 1000);

      record.views += 1;

      if (i < 3) await sleep(1000); // 1s gap as in original
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

// ---------- Watch video by launching new Chrome and loading cookies ----------
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
