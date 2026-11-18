// Shared pieces of the Google Form filler: the account store and TOTP.
// The store lives outside this repository, on the machine, and holds only what
// the operator typed. Nothing here is ever committed.

import { createHmac } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { dirname, join } from 'node:path';

// --- account store ---------------------------------------------------------------------
export const storePath = () => process.env.GFORM_ACCOUNTS || join(homedir(), '.gform-accounts.json');

export const slug = (email) => String(email).trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export function loadAccounts() {
  const p = storePath();
  if (!existsSync(p)) return { accounts: [] };
  try {
    const raw = JSON.parse(readFileSync(p, 'utf8'));
    return { accounts: Array.isArray(raw.accounts) ? raw.accounts : [] };
  } catch {
    return { accounts: [] };
  }
}

export function saveAccounts(store) {
  const p = storePath();
  mkdirSync(dirname(p), { recursive: true });
  writeFileSync(p, JSON.stringify(store, null, 2));
  return p;
}

export function findAccount(store, email) {
  const s = slug(email);
  return store.accounts.find((a) => a.slug === s) || null;
}

export function upsertAccount(store, email, fields) {
  const s = slug(email);
  const now = new Date().toISOString();
  let acc = store.accounts.find((a) => a.slug === s);
  if (!acc) {
    acc = { slug: s, email: String(email).trim(), port: null, created: now };
    store.accounts.push(acc);
  }
  Object.assign(acc, fields);
  acc.updated = now;
  return acc;
}

// --- TOTP (RFC 6238, SHA-1) -------------------------------------------------------------
const B32 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';

export function base32Decode(secret) {
  const s = String(secret).toUpperCase().replace(/[^A-Z2-7]/g, '');
  let bits = '';
  for (const c of s) {
    const v = B32.indexOf(c);
    if (v < 0) continue;
    bits += v.toString(2).padStart(5, '0');
  }
  const bytes = [];
  for (let i = 0; i + 8 <= bits.length; i += 8) bytes.push(parseInt(bits.slice(i, i + 8), 2));
  return Buffer.from(bytes);
}

export function totp(secret, at = Date.now(), step = 30, digits = 6) {
  const counter = Math.floor(at / 1000 / step);
  const buf = Buffer.alloc(8);
  buf.writeBigUInt64BE(BigInt(counter));
  const hmac = createHmac('sha1', base32Decode(secret)).update(buf).digest();
  const offset = hmac[hmac.length - 1] & 0xf;
  const code = ((hmac[offset] & 0x7f) << 24 | hmac[offset + 1] << 16 | hmac[offset + 2] << 8 | hmac[offset + 3]) % 10 ** digits;
  return String(code).padStart(digits, '0');
}
