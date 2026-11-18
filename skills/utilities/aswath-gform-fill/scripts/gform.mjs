#!/usr/bin/env node
// Fill and submit a Google Form through a real Chrome, driven over CDP.
//
//   node gform.mjs account list
//   node gform.mjs account add --email E [--password P] [--totp SECRET]
//   node gform.mjs account remove --email E
//   node gform.mjs inspect --url <formUrl> [--email E]
//   node gform.mjs fill    --url <formUrl> --answers FILE [--email E]
//                          [--otp-file FILE] [--no-submit]
//
// Each email gets its own Chrome profile and its own DevTools port, so several
// Google accounts can be signed in side by side and each one signs in only once.
// The browser is never closed by this script.

import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { findAccount, loadAccounts, saveAccounts, slug, totp, upsertAccount } from './lib.mjs';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// --- args ----------------------------------------------------------------------------
const argv = process.argv.slice(2);
const cmd = argv[0] || 'help';
const flag = (name, dflt = null) => {
  const i = argv.indexOf('--' + name);
  if (i === -1) return dflt;
  const v = argv[i + 1];
  return v && !v.startsWith('--') ? v : true;
};
const URLFORM = flag('url');
const ANSWERS_FILE = flag('answers');
const EMAIL = flag('email');
const PASSWORD = flag('password');
const TOTP_SECRET = flag('totp');
const OTP_FILE = flag('otp-file');
const NO_SUBMIT = flag('no-submit', false) === true;
const OUT = String(flag('out', 'gform-result.json'));
const PROFILE_ROOT = String(flag('profile-root', join(homedir(), '.gform-profiles')));

// --- account store ---------------------------------------------------------------------
if (cmd === 'account') {
  const action = argv[1] || 'list';
  const store = loadAccounts();
  if (action === 'list') {
    if (!store.accounts.length) console.log('no accounts yet - add one with: account add --email you@example.com');
    for (const a of store.accounts) {
      console.log(`${a.email}  port=${a.port || '-'}  profile=${a.profile || '-'}  password=${a.password ? 'yes' : 'no'}  totp=${a.totp ? 'yes' : 'no'}`);
    }
    process.exit(0);
  }
  if (!EMAIL) { console.error('account add/remove needs --email'); process.exit(1); }
  if (action === 'remove') {
    store.accounts = store.accounts.filter((a) => a.slug !== slug(EMAIL));
    saveAccounts(store);
    console.log('removed', EMAIL);
    process.exit(0);
  }
  if (action !== 'add') { console.error('unknown account action: ' + action); process.exit(1); }
  const fields = {};
  if (PASSWORD) fields.password = String(PASSWORD);
  if (TOTP_SECRET) fields.totp = String(TOTP_SECRET);
  const acc = upsertAccount(store, EMAIL, fields);
  if (!acc.port) acc.port = 9400 + (store.accounts.indexOf(acc) % 400);
  if (!acc.profile) acc.profile = join(PROFILE_ROOT, acc.slug);
  saveAccounts(store);
  console.log('saved', acc.email, '| port', acc.port, '| profile', acc.profile);
  process.exit(0);
}

// --- the account this run acts as -------------------------------------------------------
const store = loadAccounts();
const account = EMAIL ? findAccount(store, EMAIL) : null;
const PORT = Number(flag('port', account?.port || 9337));
const PROFILE = String(flag('profile', account?.profile || join(PROFILE_ROOT, account ? account.slug : 'default')));
const PASS = PASSWORD || account?.password || null;
const TOTP = TOTP_SECRET || account?.totp || null;

if (!URLFORM) {
  console.error('usage: gform.mjs account|inspect|fill --url <formUrl> [--answers FILE] [--email E] [--no-submit]');
  process.exit(1);
}
if (EMAIL && !account && !PASSWORD) {
  console.log(`no saved account for ${EMAIL} - signing in by hand in the open window`);
}

// --- browser -------------------------------------------------------------------------
function chromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    join(homedir(), 'AppData/Local/Google/Chrome/Application/chrome.exe'),
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
  ].filter(Boolean);
  for (const c of candidates) if (existsSync(c)) return c;
  throw new Error('No Chrome/Edge found. Set CHROME_PATH.');
}

async function browserUp(port) {
  try {
    const r = await fetch(`http://127.0.0.1:${port}/json/version`);
    return r.ok;
  } catch { return false; }
}

async function ensureBrowser(port, profile) {
  if (await browserUp(port)) { console.log(`reusing Chrome on port ${port}`); return; }
  mkdirSync(profile, { recursive: true });
  const exe = chromePath();
  const args = [
    `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`,
    '--no-first-run', '--no-default-browser-check', '--window-size=1440,1000', 'about:blank',
  ];
  console.log(`starting Chrome (profile ${profile}) - it stays open`);
  spawn(exe, args, { stdio: 'ignore', detached: true }).unref();
  for (let i = 0; i < 60; i++) {
    await sleep(500);
    if (await browserUp(port)) return;
  }
  throw new Error('Chrome debug endpoint never came up on port ' + port);
}

// --- CDP ---------------------------------------------------------------------------
await ensureBrowser(PORT, PROFILE);

let nextId = 1;
const pending = new Map();
const wsUrl = (await (await fetch(`http://127.0.0.1:${PORT}/json/version`)).json()).webSocketDebuggerUrl;
const ws = new WebSocket(wsUrl);
await new Promise((r) => { ws.onopen = r; });
ws.onmessage = (ev) => {
  const m = JSON.parse(typeof ev.data === 'string' ? ev.data : Buffer.from(ev.data).toString());
  if (m.id && pending.has(m.id)) {
    const p = pending.get(m.id); pending.delete(m.id);
    m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result);
  }
};
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  const id = nextId++; pending.set(id, { resolve, reject });
  ws.send(JSON.stringify(sessionId ? { id, method, params, sessionId } : { id, method, params }));
  setTimeout(() => { if (pending.delete(id)) reject(new Error('timeout ' + method)); }, 60000);
});

const targets = (await send('Target.getTargets')).targetInfos;
// Prefer a tab already showing this form (same /d/e/<id>/ path), else open one.
const formId = String(URLFORM).match(/\/d\/e\/([A-Za-z0-9_-]+)/);
let page = formId
  ? targets.find((t) => t.type === 'page' && t.url.includes('/d/e/' + formId[1]))
  : targets.find((t) => t.type === 'page' && t.url === URLFORM);
if (!page) {
  const { targetId } = await send('Target.createTarget', { url: URLFORM, newWindow: false });
  page = (await send('Target.getTargets')).targetInfos.find((t) => t.targetId === targetId);
}
const { sessionId } = await send('Target.attachToTarget', { targetId: page.targetId, flatten: true });
await send('Runtime.enable', {}, sessionId);
await send('Page.enable', {}, sessionId);

const evaluate = async (fn, arg) => {
  const expression = `(${fn.toString()})(${arg === undefined ? '' : JSON.stringify(arg)})`;
  const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }, sessionId);
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result?.value;
};

const pageState = () => evaluate(`() => ({
  url: location.href,
  head: document.body.innerText.slice(0, 400).replace(/\\n+/g, ' | '),
  buttons: Array.from(document.querySelectorAll('[role="button"]'))
    .filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0; })
    .map(b => (b.getAttribute('jsname') || '') + ':' + b.textContent.trim().slice(0, 25)).filter(Boolean),
  recorded: /Thank you for your response|response has been recorded/i.test(document.body.innerText)
})`);

const clickButton = (jsname, textRe) => evaluate(`((a) => {
  const b = document.querySelector('[jsname="' + a.js + '"]') ||
    Array.from(document.querySelectorAll('[role="button"]')).find(x => new RegExp(a.re, 'i').test(x.textContent.trim()));
  if (!b) return false;
  b.click();
  return true;
})`, { js: jsname || '', re: textRe });

// --- land on the requested form -------------------------------------------------------
{
  const want = String(URLFORM).split('?')[0].replace(/\/viewform$/, '');
  const cur = String(await evaluate(`() => location.href`));
  if (!cur.includes(want)) {
    await send('Page.navigate', { url: URLFORM }, sessionId);
    await sleep(5000);
  }
}

// --- sign in -------------------------------------------------------------------------
async function signIn() {
  for (let i = 0; i < 400; i++) {
    const s = await pageState();
    const blocks = await evaluate(`() => document.querySelectorAll('div[role="listitem"] [role="heading"]').length`);
    if (s.recorded || blocks > 0 || /Indicates required question/.test(s.head)) return true;
    const onAccounts = /accounts\.google\.com/.test(s.url);
    const otpField = await evaluate(`() => !!document.querySelector('input[name="Pin"], input[name="totpPin"], input[aria-label*="code" i]')`);
    const idField = await evaluate(`() => !!document.querySelector('input[name="identifier"], input[name="Email"]')`);
    const pwField = await evaluate(`() => !!document.querySelector('input[type="password"]')`);

    if (idField && EMAIL) {
      await evaluate(`(v) => {
        const el = document.querySelector('input[name="identifier"], input[name="Email"]');
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }`, String(EMAIL));
      await clickButton('', '^(next|sign in)$');
      console.log('submitted the email');
      await sleep(2500);
      continue;
    }
    if (pwField && PASS) {
      await evaluate(`(v) => {
        const el = document.querySelector('input[type="password"]');
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }`, String(PASSWORD));
      await clickButton('', '^(next|sign in)$');
      console.log('submitted the password');
      await sleep(2500);
      continue;
    }
    if (otpField) {
      // Either the human types the code in the open window, --otp-file is written for us,
      // or the account carries a TOTP secret and we compute the code ourselves.
      let code = TOTP ? totp(TOTP) : '';
      for (let k = 0; k < 120 && !code; k++) {
        await sleep(2500);
        if (OTP_FILE && existsSync(String(OTP_FILE))) {
          code = readFileSync(String(OTP_FILE), 'utf8').trim().split(/\s+/)[0] || '';
          if (code) { try { writeFileSync(String(OTP_FILE), ''); } catch {} }
        }
        if (!code) {
          const now = await pageState();
          if (!/accounts\.google\.com/.test(now.url)) { console.log('signed in by hand'); return true; }
        }
      }
      if (!code) { console.log('NO 2FA CODE - type it in the open Chrome window'); return false; }
      await evaluate(`(v) => {
        const el = document.querySelector('input[name="Pin"], input[name="totpPin"], input[aria-label*="code" i]');
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v);
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }`, code);
      await clickButton('', '^(next|continue)$');
      console.log('submitted the 2FA code');
      await sleep(2500);
      continue;
    }
    if (onAccounts) { console.log('sign-in page open - complete it in the browser window'); }
    await sleep(3000);
  }
  return false;
}

// --- page reading --------------------------------------------------------------------
const READ_PAGE = `() => {
  const norm = (s) => String(s).replace(/[*\\u200b]/g, '').replace(/\\s+/g, ' ').trim();
  const blocks = Array.from(document.querySelectorAll('div[role="listitem"]')).filter(el => {
    if (el.parentElement && el.parentElement.closest('div[role="listitem"]')) return false;
    if (!el.querySelector('[role="heading"]')) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
  return blocks.map(b => {
    const title = norm(b.querySelector('[role="heading"]').innerText);
    const radios = Array.from(b.querySelectorAll('[role="radio"]')).map(r => r.getAttribute('aria-label') || '');
    const gridCells = radios.filter(a => /^\\d+, response for /.test(a));
    const boxes = Array.from(b.querySelectorAll('[role="checkbox"]')).map(c => c.getAttribute('aria-label') || '');
    const textEl = Array.from(b.querySelectorAll('input, textarea')).find(e => e.getAttribute('jsname') === 'YPqjbf' || e.tagName === 'TEXTAREA');
    const rows = {};
    for (const a of gridCells) {
      const m = a.match(/^(\\d+), response for (.*)$/);
      if (m) (rows[m[2]] = rows[m[2]] || []).push(m[1]);
    }
    const checked = Array.from(b.querySelectorAll('[role="radio"]')).filter(r => r.getAttribute('aria-checked') === 'true').map(r => r.getAttribute('aria-label') || '');
    return {
      title,
      kind: Object.keys(rows).length ? 'grid' : gridCells.length ? 'grid' : radios.length ? 'radio' : boxes.length ? 'checkbox' : textEl ? 'text' : 'none',
      options: radios.filter(a => !/^\\d+, response for /.test(a)),
      rows,
      boxes,
      checked,
      text: textEl ? textEl.value : null
    };
  });
}`;

const FILL = `(rules) => {
  const out = { filled: [], missing: [], notes: [] };
  const norm = (s) => String(s).replace(/[*\\u200b]/g, '').replace(/\\s+/g, ' ').trim();
  const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const blocks = Array.from(document.querySelectorAll('div[role="listitem"]')).filter(el => {
    if (el.parentElement && el.parentElement.closest('div[role="listitem"]')) return false;
    if (!el.querySelector('[role="heading"]')) return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  });
  const setText = (el, val) => {
    const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, val);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
    el.dispatchEvent(new Event('blur', { bubbles: true }));
  };
  for (const b of blocks) {
    const title = norm(b.querySelector('[role="heading"]').innerText);
    if (!title) continue;
    const radios = Array.from(b.querySelectorAll('[role="radio"]'));
    const grid = radios.filter(r => /^\\d+, response for /.test(r.getAttribute('aria-label') || ''));
    const textEl = Array.from(b.querySelectorAll('input, textarea')).find(e => e.getAttribute('jsname') === 'YPqjbf' || e.tagName === 'TEXTAREA');

    if (grid.length) {                                       // rating grid: one cell per row
      const rows = {};
      for (const r of grid) {
        const m = (r.getAttribute('aria-label') || '').match(/^(\\d+), response for (.*)$/);
        if (!m) continue;
        (rows[m[2]] = rows[m[2]] || []).push({ v: m[1], el: r });
      }
      let hits = 0;
      for (const row of Object.keys(rows)) {
        const cells = rows[row];
        if (cells.some(c => c.el.getAttribute('aria-checked') === 'true')) continue;
        const pick = rules.grid.find(v => cells.some(c => c.v === v));
        if (!pick) { out.missing.push(title + ' row[' + row.slice(0, 40) + ']'); continue; }
        const cand = cells.filter(c => c.v === pick);
        (cand.find(c => visible(c.el)) || cand[0]).el.click();
        hits++;
      }
      out.filled.push(title + ' [grid rows=' + Object.keys(rows).length + ' set=' + hits + ']');
      continue;
    }
    if (radios.length) {                                     // single-choice question
      const want = rules.radio[title];
      if (!want) { out.notes.push('radio untouched: ' + title); continue; }
      const cand = radios.filter(r => (r.getAttribute('aria-label') || '') === want || (r.getAttribute('aria-label') || '').startsWith(want));
      if (!cand.length) { out.missing.push(title + ' (no option ' + want + ')'); continue; }
      (cand.find(visible) || cand[0]).click();
      out.filled.push(title + ' = ' + (cand.find(visible) || cand[0]).getAttribute('aria-label'));
      continue;
    }
    if (textEl) {                                            // short / long text
      const want = rules.text[title] !== undefined ? rules.text[title] : rules.textDefault;
      if (!want) { out.notes.push('text left empty: ' + title); continue; }
      setText(textEl, want);
      out.filled.push(title + ' = ' + want);
      continue;
    }
  }
  return out;
}`;

// --- walk the pages -------------------------------------------------------------------
async function walkPages(onPage) {
  const pages = [];
  for (let i = 0; i < 12; i++) {
    const s = await pageState();
    if (!s.buttons.some((b) => b.startsWith('GeGHKb:Back'))) break;
    await clickButton('GeGHKb', '^back$');
    await sleep(2500);
  }
  for (let n = 1; n <= 60; n++) {
    const blocks = await evaluate(READ_PAGE);
    const s = await pageState();
    const hasSubmit = s.buttons.some((b) => /:submit$/i.test(b));
    const hasNext = s.buttons.some((b) => b.startsWith('OCpkoe:Next'));
    pages.push({ page: n, blocks });
    if (await onPage(n, blocks, s)) return pages;
    if (!hasNext) { console.log('no Next button on this page - stopping'); return pages; }
    await clickButton('OCpkoe', '^next$');
    await sleep(3500);
  }
  return pages;
}

// --- run -------------------------------------------------------------------------------
if (!(await signIn())) { console.log('NOT SIGNED IN - finish the sign-in in the browser window and rerun'); process.exit(2); }

if (/alreadyresponded/.test(String(await evaluate(`() => location.href`)))) {
  console.log('this account has already answered this form - nothing to fill, nothing submitted');
  process.exit(3);
}

if (cmd === 'inspect') {
  const pages = await walkPages(async (n, blocks) => {
    console.log(`\n--- page ${n} ---`);
    for (const b of blocks) {
      if (b.kind === 'grid') console.log(`  GRID    ${b.title}  rows=${Object.keys(b.rows).length} values=${[...new Set(Object.values(b.rows).flat())].join('/')}`);
      else if (b.kind === 'radio') console.log(`  RADIO   ${b.title}  options=${JSON.stringify(b.options)}`);
      else if (b.kind === 'checkbox') console.log(`  CHECK   ${b.title}  options=${JSON.stringify(b.boxes)}`);
      else if (b.kind === 'text') console.log(`  TEXT    ${b.title}`);
      else console.log(`  -       ${b.title}`);
    }
    return false;
  });
  writeFileSync('gform-inspect.json', JSON.stringify({ url: URLFORM, pages }, null, 2));
  console.log('\nwrote gform-inspect.json');
  process.exit(0);
}

if (cmd !== 'fill') { console.error('unknown command: ' + cmd); process.exit(1); }

const answers = JSON.parse(readFileSync(String(ANSWERS_FILE), 'utf8'));
const rules = {
  text: answers.text || {},
  radio: answers.radio || {},
  grid: (answers.grid && answers.grid.default) || ['4', '5', '3', '2', '1'],
  textDefault: answers.textDefault,
};

const report = { filled: [], missing: [], notes: [], pages: [] };
const pages = await walkPages(async (n, blocks) => {
  let last = null;
  for (let pass = 0; pass < 4; pass++) {
    const r = await evaluate(FILL, rules);
    last = r;
    report.filled.push(...r.filled.map((x) => `p${n} ${x}`));
    report.missing.push(...r.missing.map((x) => `p${n} ${x}`));
    report.notes.push(...r.notes.map((x) => `p${n} ${x}`));
    await sleep(1500);
    const again = await evaluate(FILL, rules);
    if (again.filled.length === r.filled.length) break;
    report.filled.push(...again.filled.map((x) => `p${n} ${x}`));
    report.missing.push(...again.missing.map((x) => `p${n} ${x}`));
  }
  const s = await pageState();
  const hasSubmit = s.buttons.some((b) => /:submit$/i.test(b));
  report.pages.push({ page: n, filled: last.filled.length, missing: last.missing.length, hasSubmit });
  console.log(`page ${n}: filled=${last.filled.length} missing=${last.missing.length}${hasSubmit ? ' (submit here)' : ''}`);
  if (hasSubmit) {
    if (NO_SUBMIT) { console.log('dry run: stopped before Submit'); return true; }
    const clicked = await clickButton('', '^submit$');
    console.log('submit clicked:', clicked);
    return true;
  }
  return false;
});

await sleep(9000);
const after = await pageState();
writeFileSync(OUT, JSON.stringify({ report, after, pages: pages.length }, null, 2));
console.log('recorded:', after.recorded, '| url:', after.url.slice(0, 100));
console.log('missing:', report.missing.length, report.missing.slice(0, 10).join(' | '));
if (/alreadyresponded/.test(after.url)) {
  console.log('this account has already answered this form - nothing submitted');
  process.exit(3);
}
if (NO_SUBMIT) process.exit(report.missing.length ? 1 : 0);
process.exit(after.recorded ? 0 : 1);
