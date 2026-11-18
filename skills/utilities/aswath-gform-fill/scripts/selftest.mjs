#!/usr/bin/env node
// Self-check: fill and submit the mock form in a throwaway headless Chrome, then
// assert what the page holds. Run: node scripts/selftest.mjs
import { spawn } from 'node:child_process';
import { existsSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const skillRoot = dirname(here);
const mock = join(skillRoot, 'tests', 'mock-form.html');
const mockUrl = `file:///${mock.replace(/\\/g, '/')}`;
const PORT = Number(process.env.GFORM_TEST_PORT || 9400 + (process.pid % 500));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let passed = 0, failed = 0;
const check = (name, ok, detail = '') => {
  if (ok) { passed++; console.log('  ok   ' + name); }
  else { failed++; console.log('  FAIL ' + name + (detail ? ' :: ' + detail : '')); }
};

function chromePath() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
    join(process.env.HOME || process.env.USERPROFILE || '', 'AppData/Local/Google/Chrome/Application/chrome.exe'),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
  ].filter(Boolean);
  for (const c of candidates) if (existsSync(c)) return c;
  throw new Error('no Chrome found; set CHROME_PATH');
}

// --- one CDP connection, used for both the filler and the assertions -------------------
let ws, nextId = 1;
const pending = new Map();
const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
  const id = nextId++; pending.set(id, { resolve, reject });
  ws.send(JSON.stringify(sessionId ? { id, method, params, sessionId } : { id, method, params }));
  setTimeout(() => { if (pending.delete(id)) reject(new Error('timeout ' + method)); }, 30000);
});
const connect = async (port) => {
  ws = new WebSocket((await (await fetch(`http://127.0.0.1:${port}/json/version`)).json()).webSocketDebuggerUrl);
  await new Promise((r) => { ws.onopen = r; });
  ws.onmessage = (ev) => {
    const m = JSON.parse(typeof ev.data === 'string' ? ev.data : Buffer.from(ev.data).toString());
    if (m.id && pending.has(m.id)) {
      const p = pending.get(m.id); pending.delete(m.id);
      m.error ? p.reject(new Error(m.error.message)) : p.resolve(m.result);
    }
  };
};

// --- account store and TOTP (no browser needed) -----------------------------------------
{
  const storeFile = join(tmpdir(), `gform-accounts-${process.pid}.json`);
  process.env.GFORM_ACCOUNTS = storeFile;
  const lib = await import('./lib.mjs');

  check('TOTP matches RFC 6238 (t=59, 8 digits)', lib.totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ', 59000, 30, 8) === '94287082');
  check('TOTP matches RFC 6238 (t=59, 6 digits)', lib.totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ', 59000, 30, 6) === '287082');
  check('TOTP matches RFC 6238 (t=1111111109)', lib.totp('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ', 1111111109000, 30, 8) === '07081804');

  const store = lib.loadAccounts();
  const acc = lib.upsertAccount(store, 'Test.User+Tag@Example.com', { password: 'x', port: 9401, profile: 'p' });
  check('a new account gets a slug', acc.slug === 'test-user-tag-example-com', acc.slug);
  check('a new account is findable', lib.findAccount(store, 'test.user+tag@example.com') === acc);
  lib.saveAccounts(store);
  check('the account survives a reload', lib.findAccount(lib.loadAccounts(), 'TEST.USER+TAG@EXAMPLE.COM') !== null);
  check('the store lives outside the repo', lib.storePath() === storeFile, lib.storePath());

  const cli = spawn(process.execPath, [join(here, 'gform.mjs'), 'account', 'list'], { stdio: ['ignore', 'pipe', 'pipe'] });
  let cliOut = '';
  cli.stdout.on('data', (d) => { cliOut += d; });
  cli.stderr.on('data', (d) => { cliOut += d; });
  await new Promise((res) => cli.on('close', res));
  check('the CLI lists the saved account', /Test\.User\+Tag@Example\.com/.test(cliOut), cliOut.slice(-400));
  rmSync(storeFile, { force: true });
  delete process.env.GFORM_ACCOUNTS;
}

const profile = mkdtempSync(join(tmpdir(), 'gform-selftest-'));
const chrome = spawn(chromePath(), [
  `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
  '--headless=new', '--no-first-run', '--no-default-browser-check',
  mockUrl,
], { stdio: 'ignore', detached: true });
process.on('exit', () => { try { rmSync(profile, { recursive: true, force: true }); } catch {} });

for (let i = 0; i < 60; i++) {
  await sleep(500);
  try { if ((await fetch(`http://127.0.0.1:${PORT}/json/version`)).ok) break; } catch {}
}

// --- run the filler --------------------------------------------------------------------
const answers = join(profile, 'answers.json');
writeFileSync(answers, JSON.stringify({
  text: { Name: 'Test User' },
  radio: { Section: 'E' },
  grid: { default: ['4', '5'] },
  textDefault: 'None',
}));

const out = join(profile, 'result.json');
const run = spawn(process.execPath, [
  join(here, 'gform.mjs'), 'fill',
  '--url', mockUrl,
  '--answers', answers,
  '--port', String(PORT),
  '--profile', profile,
  '--out', out,
], { stdio: ['ignore', 'pipe', 'pipe'] });
let log = '';
run.stdout.on('data', (d) => { log += d; });
run.stderr.on('data', (d) => { log += d; });
const code = await new Promise((res) => run.on('close', res));

console.log('--- selftest: ' + skillRoot.split(/[\\/]/).pop() + ' ---');
check('the filler exits 0', code === 0, 'exit ' + code + '\n' + log.slice(-800));
check('both pages are walked', /page 1:/.test(log) && /page 2:/.test(log), log.slice(-600));
check('nothing is missing', /missing: 0/.test(log), log.slice(-600));
check('the response is recorded', /recorded: true/.test(log), log.slice(-600));

// --- what the page actually holds ------------------------------------------------------
await connect(PORT);
const tg = await send('Target.getTargets');
const page = tg.targetInfos.find((t) => t.type === 'page' && t.url.includes('mock-form'));
const { sessionId } = await send('Target.attachToTarget', { targetId: page.targetId, flatten: true });
await send('Runtime.enable', {}, sessionId);
const rr = await send('Runtime.evaluate', {
  expression: `(() => ({
    thanks: !document.getElementById('thanks').classList.contains('hide'),
    checked: Array.from(document.querySelectorAll('[role="radio"][aria-checked="true"]')).map(x => x.getAttribute('aria-label')),
    values: Array.from(document.querySelectorAll('input,textarea')).map(x => x.value)
  }))()`,
  returnByValue: true,
}, sessionId);
const state = rr.result.value;

check('the thank-you page is shown', state.thanks === true);
check('the radio answer stuck', state.checked.includes('E'), JSON.stringify(state.checked));
check('the grid row for Outcome A is 4', state.checked.includes('4, response for Outcome A'), JSON.stringify(state.checked));
check('the grid row for Outcome B is 4', state.checked.includes('4, response for Outcome B'), JSON.stringify(state.checked));
check('the text answer stuck', state.values.includes('Test User'), JSON.stringify(state.values));
check('the free-text default stuck', state.values.includes('None'), JSON.stringify(state.values));

// --- close the browser, so the next run starts clean -----------------------------------
try { await send('Browser.close'); } catch {}
try { process.kill(-chrome.pid); } catch {}

console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
