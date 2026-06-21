// Logs into the real app (localhost dev server pointed at the prod backend),
// drives each view into the right state, and saves genuine PNG screenshots to
// marketing/screens/ for the deck. Crops to the main panel (no global sidebar /
// header), matching the existing deck screens.
//
// Run: node capture.mjs    (dev server must be running on :3001)
import puppeteer from 'puppeteer-core';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const SCREENS = join(__dirname, '..', 'screens');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE = 'http://localhost:3001';
const EMAIL = process.env.EMAIL || 'patrykcebo11@gmail.com';
const PASSWORD = process.env.PASSWORD;
if (!PASSWORD) { console.error('Set PASSWORD env var'); process.exit(1); }

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const HIDE_HEADER = `:root{} .app-main > header{display:none!important} .app-main{padding:18px!important}`;

async function clickByText(page, selector, text) {
  const ok = await page.evaluate((sel, t) => {
    const el = [...document.querySelectorAll(sel)].find(e => e.textContent.trim().includes(t));
    if (el) { el.click(); return true; }
    return false;
  }, selector, text);
  if (!ok) throw new Error(`clickByText not found: ${selector} "${text}"`);
}

async function setHeaderHidden(page, hidden) {
  await page.evaluate((css, hide) => {
    let s = document.getElementById('cap-hide-style');
    if (hide) {
      if (!s) { s = document.createElement('style'); s.id = 'cap-hide-style'; document.head.appendChild(s); }
      s.textContent = css;
    } else if (s) { s.remove(); }
  }, HIDE_HEADER, hidden);
}

async function shotPanel(page, name) {
  await setHeaderHidden(page, true);
  await sleep(350);
  const box = await page.evaluate(() => {
    const m = document.querySelector('.app-main');
    const r = m.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  });
  const vh = page.viewport().height;
  const clip = {
    x: Math.max(0, Math.floor(box.x)),
    y: Math.max(0, Math.floor(box.y)),
    width: Math.floor(box.width),
    height: Math.floor(Math.min(box.height, vh - Math.max(0, box.y))),
  };
  await page.screenshot({ path: join(SCREENS, `${name}.png`), clip });
  await setHeaderHidden(page, false);
  console.log(`saved ${name}.png  ${clip.width}x${clip.height} @2x`);
}

async function nav(page, label) {
  await clickByText(page, 'nav button', label);
  await sleep(1200);
}

async function main() {
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: 'new',
    defaultViewport: { width: 1440, height: 980, deviceScaleFactor: 2 },
    args: ['--no-sandbox', '--force-color-profile=srgb'],
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  // ── Login ──
  await page.goto(BASE, { waitUntil: 'networkidle2' });
  await page.waitForSelector('input[type="email"], input[placeholder="trener@klub.pl"]');
  await page.type('input[type="email"], input[placeholder="trener@klub.pl"]', EMAIL);
  await page.type('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForSelector('nav button', { timeout: 30000 });
  await sleep(2500); // bootstrap
  console.log('logged in');

  // ── 1) Pulpit (dashboard, while match still active) ──
  await nav(page, 'Pulpit');
  await page.waitForSelector('.kpi-card', { timeout: 15000 }).catch(() => {});
  await sleep(800);
  await shotPanel(page, 'pulpit');

  // ── 2) Statystyki — single match → per-player flag table ──
  await nav(page, 'Statystyki');
  await page.waitForSelector('.match-select-item', { timeout: 15000 });
  await clickByText(page, 'button', 'Wyczyść').catch(() => {});
  await sleep(400);
  await clickByText(page, '.match-select-item', 'Arkonia');
  await page.waitForSelector('.stats-table', { timeout: 15000 });
  await sleep(900);
  await shotPanel(page, 'stats');

  // ── 3) Asystent — live scorekeeper with a player selected ──
  await nav(page, 'Asystent');
  await page.waitForSelector('.main-layout .player', { timeout: 15000 });
  await clickByText(page, '.player', 'Kamiński').catch(async () => { await clickByText(page, '.player', 'Wiśniewski'); });
  await sleep(700);
  await shotPanel(page, 'asystent');

  // ── 4) MVP — end the match, capture the summary overlay ──
  await setHeaderHidden(page, false);
  await clickByText(page, '.app-main > header button, header button', 'Zakończ mecz');
  await page.waitForSelector('.popup .btn.danger', { timeout: 8000 });
  await clickByText(page, '.popup .btn.danger', 'Zakończ mecz');
  await page.waitForSelector('.popup--wide', { timeout: 15000 });
  await sleep(1200);
  const mvpEl = await page.$('.popup--wide');
  await mvpEl.screenshot({ path: join(SCREENS, 'mvp.png') });
  console.log('saved mvp.png');

  await browser.close();
  console.log('All screenshots captured.');
}

main().catch(e => { console.error('CAPTURE FAILED:', e.message); process.exit(1); });
