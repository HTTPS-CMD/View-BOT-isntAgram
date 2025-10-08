// login-instagram-monitored.js
// لاگین اینستاگرام با selenium (Safari) + مانیتورینگ کامل + human-in-loop
// نکته: این کد هیچ مکانیزم امنیتی را دور نمی‌زند. کپچا/چلنچ را تشخیص می‌دهد و برای تأیید دستی صبر می‌کند.

const fs = require("fs");
const path = require("path");
const { Builder, By, Key, until } = require("selenium-webdriver");
const safari = require("selenium-webdriver/safari");
let notifier;
try { notifier = require("node-notifier"); } catch { notifier = null; }

// ====================== CONFIG ======================
const ACCOUNTS_FILE = path.join("data", "accounts.json");
const COOKIES_DIR   = path.join("data", "cookies");
const LOGS_DIR      = path.join("data", "logs");
const PENDING_DIR   = path.join("data", "pending_verification");
const METRICS_FILE  = path.join("data", "metrics.json");

const MAX_LOGIN_ATTEMPTS = 3;
const BACKOFF_BASE_MS    = 10_000;           // 10s
const MANUAL_TIMEOUT_MS  = 5 * 60_000;       // 5 min
const LONG_COOLDOWN_MIN  = 30;               // minutes
const LONG_COOLDOWN_MAX  = 60;               // minutes
const PAGE_SRC_SNIPPET   = 800;              // chars

// ====================== INIT FS =====================
for (const d of [COOKIES_DIR, LOGS_DIR, PENDING_DIR]) {
  fs.mkdirSync(d, { recursive: true });
}

// ====================== UTILS =======================
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const rand  = (a,b) => Math.random()*(b-a)+a;
const rint  = (a,b) => Math.floor(rand(a,b));
const nowISO = () => new Date().toISOString();
const writeJson = (p, obj) => fs.writeFileSync(p, JSON.stringify(obj, null, 2));

function loadAccounts() {
  if (!fs.existsSync(ACCOUNTS_FILE)) {
    console.error("❌ accounts.json یافت نشد:", ACCOUNTS_FILE);
    process.exit(1);
  }
  return JSON.parse(fs.readFileSync(ACCOUNTS_FILE, "utf8"));
}

function loadMetrics() {
  try {
    if (fs.existsSync(METRICS_FILE)) return JSON.parse(fs.readFileSync(METRICS_FILE, "utf8"));
  } catch {}
  return { totalAttempts:0, successes:0, failures:0, challenges:0, perAccount:{} };
}
function updateMetrics(fn) {
  const m = loadMetrics();
  fn(m);
  writeJson(METRICS_FILE, m);
}

function perAccountLog(username) {
  const stamp = nowISO().replace(/[:.]/g,"-");
  return path.join(LOGS_DIR, `${username}-${stamp}.log.json`);
}

async function screenshot(driver, username, tag="shot") {
  try {
    const data = await driver.takeScreenshot();
    const file = path.join(LOGS_DIR, `${username}-${Date.now()}-${tag}.png`);
    fs.writeFileSync(file, data, "base64");
    return file;
  } catch { return null; }
}

// =================== HUMAN BEHAVIOR =================
async function humanType(el, text) {
  for (const ch of text.split("")) {
    await el.sendKeys(ch);
    await sleep(rint(30, 90));
  }
}
async function humanScroll(driver) {
  try {
    await driver.executeScript(`window.scrollBy(0, ${rint(250, 900)});`);
    await sleep(rint(250, 900));
    await driver.executeScript(`window.scrollBy(0, -${rint(80, 500)});`);
  } catch {}
}
async function humanMoveAndClick(driver, el) {
  try {
    await driver.executeScript("arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", el);
    await sleep(rint(120, 420));
    await el.click();
    await sleep(rint(120, 420));
  } catch {}
}

// =================== COOKIES HELPERS =================
async function saveCookies(driver, username) {
  try {
    const cookies = await driver.manage().getCookies();
    fs.writeFileSync(path.join(COOKIES_DIR, `${username}.json`), JSON.stringify(cookies, null, 2));
  } catch (e) {
    console.warn("⚠️ unable to save cookies:", e?.message);
  }
}
async function loadCookies(driver, username) {
  const p = path.join(COOKIES_DIR, `${username}.json`);
  if (!fs.existsSync(p)) return false;
  try {
    const cookies = JSON.parse(fs.readFileSync(p,"utf8"));
    await driver.get("https://www.instagram.com/");
    for (const c of cookies) {
      const cc = {
        name: c.name,
        value: c.value,
        path: c.path || "/",
        domain: c.domain || ".instagram.com",
        httpOnly: !!c.httpOnly,
        secure:   !!c.secure,
      };
      try { await driver.manage().addCookie(cc); } catch {}
    }
    return true;
  } catch (e) {
    console.warn("⚠️ unable to load cookies:", e?.message);
    return false;
  }
}

// ============== COOKIE CONSENT HANDLER ===============
async function tryAcceptCookies(driver, timeoutMs = 8000) {
  const textVariants = [
    "allow all cookies","allow all","allow cookies","accept all cookies",
    "accept all","accept","allow","i accept","agree","enable all cookies",
    "save & accept","save and accept"
  ];
  const cssCandidates = [
    "button[data-testid*='cookie']",
    "button[class*='cookie']",
    "button[class*='accept']",
    "button[class*='btn']",
    "div[role='dialog'] button",
    "button[role='button']",
    "button"
  ];
  const clickIf = async (el) => {
    try { await humanMoveAndClick(driver, el); return true; } catch { return false; }
  };

  // 1) try inside iframes
  try {
    const iframes = await driver.findElements(By.css("iframe"));
    for (const f of iframes) {
      try {
        await driver.switchTo().frame(f);
        for (const txt of textVariants) {
          const xp = `//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'${txt}')]`;
          const els = await driver.findElements(By.xpath(xp));
          for (const el of els) if (await clickIf(el)) { await driver.switchTo().defaultContent(); return true; }
        }
        for (const sel of cssCandidates) {
          const els = await driver.findElements(By.css(sel));
          for (const el of els) {
            const t = (await el.getText()).trim().toLowerCase();
            const cls = (await el.getAttribute("class")||"").toLowerCase();
            if ((t && textVariants.some(v=>t.includes(v))) || /cookie|accept|allow|agree/.test(cls)) {
              if (await clickIf(el)) { await driver.switchTo().defaultContent(); return true; }
            }
          }
        }
      } catch {}
      finally { try { await driver.switchTo().defaultContent(); } catch {} }
    }
  } catch {}

  // 2) main DOM
  for (const txt of textVariants) {
    const xp = `//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'${txt}')]`;
    const els = await driver.findElements(By.xpath(xp));
    for (const el of els) if (await clickIf(el)) return true;
  }
  for (const sel of cssCandidates) {
    const els = await driver.findElements(By.css(sel));
    for (const el of els) {
      const t = (await el.getText()).trim().toLowerCase();
      const cls = (await el.getAttribute("class")||"").toLowerCase();
      if ((t && textVariants.some(v=>t.includes(v))) || /cookie|accept|allow|agree/.test(cls)) {
        if (await clickIf(el)) return true;
      }
    }
  }

  // 3) generic fallback
  try {
    const els = await driver.findElements(By.css("button, a, div[role='button']"));
    for (const el of els) {
      const t = (await el.getText()).trim().toLowerCase();
      if (t && textVariants.some(v=>t.includes(v))) {
        if (await clickIf(el)) return true;
      }
    }
  } catch {}

  return false;
}

// ============== CHALLENGE DETECTION ==================
function hasChallenge(str) {
  if (!str) return false;
  return /challenge|checkpoint|two[_\s-]?factor|captcha|verify/i.test(str);
}

async function waitForManualVerification(driver, username, timeoutMs = MANUAL_TIMEOUT_MS) {
  const f = path.join(PENDING_DIR, `${username}.wait`);
  fs.writeFileSync(f, `pending ${nowISO()}`);
  if (notifier) try {
    notifier.notify({ title: "Instagram • Manual verification required", message: `Complete verification for ${username}.`, timeout: 5 });
  } catch {}

  console.log(`⚠️ Manual verification for ${username} — waiting ${Math.round(timeoutMs/1000)}s...`);
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    await sleep(2000);
    try {
      const url = await driver.getCurrentUrl();
      const src = await driver.getPageSource();
      if (!/login/i.test(url) && !hasChallenge(url + src)) {
        try { fs.unlinkSync(f); } catch {}
        console.log("✅ Manual verification finished.");
        return true;
      }
    } catch {}
  }
  console.log("❌ Manual verification timeout.");
  return false;
}

// ============== ONE ATTEMPT (single try) =============
async function loginOnce(account) {
  const username = account.username;
  const log = { username, started: nowISO(), steps: [] };
  const logPath = perAccountLog(username);

  const options = new safari.Options();
  const driver  = await new Builder().forBrowser("safari").setSafariOptions(options).build();

  try {
    const hadCookies = await loadCookies(driver, username);
    log.steps.push({ t: nowISO(), note: `loadCookies=${hadCookies}` });

    await driver.get("https://www.instagram.com/accounts/login/");
    await sleep(rint(400, 900));
    await humanScroll(driver);

    // cookie consent
    await sleep(500);
    const accepted = await tryAcceptCookies(driver, 8000);
    log.steps.push({ t: nowISO(), note: `cookieConsentClicked=${accepted}` });

    // if cookies already logged you in:
    try {
      const url0 = await driver.getCurrentUrl();
      if (!/login/i.test(url0)) {
        log.steps.push({ t: nowISO(), note: `alreadyLoggedIn url=${url0}` });
        await saveCookies(driver, username);
        log.finished = nowISO();
        writeJson(logPath, log);
        await driver.quit();
        return { success: true, challenge: false, driverClosed: true };
      }
    } catch {}

    // locate inputs
    const userInput = await driver.wait(until.elementLocated(By.name("username")), 15000);
    const passInput = await driver.wait(until.elementLocated(By.name("password")), 15000);
    log.steps.push({ t: nowISO(), note: "inputsLocated" });

    try { await userInput.clear(); } catch {}
    await humanType(userInput, account.username);
    await sleep(rint(200, 600));
    try { await passInput.clear(); } catch {}
    await humanType(passInput, account.password);
    await sleep(rint(200, 500));
    await passInput.sendKeys(Key.ENTER);
    log.steps.push({ t: nowISO(), note: "submitted" });

    await sleep(rint(4000, 7000));

    const url1 = await driver.getCurrentUrl();
    const src1 = await driver.getPageSource();
    log.pageDebug = (src1 || "").slice(0, PAGE_SRC_SNIPPET);
    const shot1 = await screenshot(driver, username, "post_submit");
    if (shot1) log.screenshot = shot1;
    log.steps.push({ t: nowISO(), note: `afterSubmit url=${url1}` });

    // challenge?
    if (hasChallenge(url1 + (src1 || ""))) {
      log.steps.push({ t: nowISO(), note: "challengeDetected" });
      await saveCookies(driver, username);
      writeJson(logPath, log);
      await screenshot(driver, username, "challenge");
      // driver را باز نگه می‌داریم برای human-in-loop
      return { success: false, challenge: true, driver };
    }

    if (!/login/i.test(url1)) {
      log.steps.push({ t: nowISO(), note: `loginSuccess url=${url1}` });
      await saveCookies(driver, username);
      updateMetrics(m => {
        m.totalAttempts++; m.successes++;
        m.perAccount[username] = (m.perAccount[username]||0) + 1;
      });
      log.finished = nowISO();
      writeJson(logPath, log);
      await driver.quit();
      return { success: true, challenge: false, driverClosed: true };
    } else {
      log.steps.push({ t: nowISO(), note: "stillOnLogin => likely fail" });
      await saveCookies(driver, username);
      updateMetrics(m => { m.totalAttempts++; m.failures++; });
      log.finished = nowISO();
      writeJson(logPath, log);
      await driver.quit();
      return { success: false, challenge: false, driverClosed: true };
    }
  } catch (e) {
    const err = e?.message || String(e);
    writeJson(logPath, { username, error: err, ts: nowISO() });
    updateMetrics(m => { m.totalAttempts++; m.failures++; });
    try { await driver.quit(); } catch {}
    return { success: false, challenge: false, driverClosed: true, error: err };
  }
}

// ============== SAFE RETRY + HUMAN LOOP =============
async function tryLogin(account) {
  for (let attempt = 1; attempt <= MAX_LOGIN_ATTEMPTS; attempt++) {
    console.log(`${nowISO()} • [${account.username}] Attempt ${attempt}/${MAX_LOGIN_ATTEMPTS}`);
    const res = await loginOnce(account);

    if (res.success) {
      console.log(`${nowISO()} • [${account.username}] ✅ Success`);
      return true;
    }

    if (res.challenge) {
      console.log(`${nowISO()} • [${account.username}] ⚠️ Challenge detected → manual flow`);
      updateMetrics(m => { m.challenges++; });
      const driver = res.driver;
      await screenshot(driver, account.username, "before_manual");
      const ok = await waitForManualVerification(driver, account.username, MANUAL_TIMEOUT_MS);
      if (ok) {
        await saveCookies(driver, account.username);
        try { await driver.quit(); } catch {}
        updateMetrics(m => { m.successes++; });
        console.log(`${nowISO()} • [${account.username}] ✅ Manual verification completed`);
        return true;
      } else {
        try { await driver.quit(); } catch {}
        const cooldown = rint(LONG_COOLDOWN_MIN, LONG_COOLDOWN_MAX) * 60_000;
        console.log(`⏳ Long cooldown ${Math.round(cooldown/60000)}m...`);
        await sleep(cooldown);
        return false;
      }
    }

    // failed (no challenge)
    if (attempt < MAX_LOGIN_ATTEMPTS) {
      const backoff = BACKOFF_BASE_MS * Math.pow(2, attempt-1) + rint(1000, 4000);
      console.log(`${nowISO()} • [${account.username}] ❌ Failed → backoff ${Math.round(backoff/1000)}s`);
      await sleep(backoff);
    } else {
      console.log(`${nowISO()} • [${account.username}] ❌ Max attempts reached`);
      updateMetrics(m => { m.failures++; });
      const cooldown = rint(LONG_COOLDOWN_MIN, LONG_COOLDOWN_MAX) * 60_000;
      console.log(`⏳ Long cooldown ${Math.round(cooldown/60000)}m...`);
      await sleep(cooldown);
      return false;
    }
  }
}

// ===================== RUNNER =======================
(async () => {
  const accounts = loadAccounts();
  for (const acc of accounts) {
    try {
      await tryLogin(acc);
    } catch (e) {
      console.error("Unhandled error for", acc.username, e?.message || e);
    }
    await sleep(rint(5000, 10000)); // فاصله بین اکانت‌ها
  }
  console.log("✅ All done.");
})();
