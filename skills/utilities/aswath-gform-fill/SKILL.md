---
name: aswath-gform-fill
description: Use when a Google Form (forms.gle or docs.google.com/forms) has to be filled and submitted - a survey, feedback form, feedback quiz, course end-of-course form - especially a long multi-page form with rating grids and branch questions, and especially when it needs a signed-in Google account, a 2FA code, or a human to log in once in a visible browser.
---

## Procedure

1. **Never restart the browser.** One persistent Chrome profile per account
   (`--user-data-dir`) keeps the Google session alive. Scripts attach to the
   already-running browser over the DevTools protocol; they never close it and
   never relaunch it. A fresh temp profile each run means the human signs in
   every single time - that is the failure mode this skill exists to kill.
2. **Pick the account.** Each email gets its own profile and its own DevTools
   port, so several Google accounts can be signed in side by side and each
   signs in only once. `account list` shows them.
3. **Open the form once in that browser.** The human signs in there (password
   and 2FA if Google asks), or the script signs in itself from the saved
   account. After that the session is reused for every later form.
4. **Inspect before filling.** Run `inspect` to dump every page, question
   heading, option list and grid. Google Forms has 400+ defined questions but
   only the branch matching the chosen answers is live, so the live DOM is the
   only reliable source of what to answer.
5. **Write the answers file** (schema in `references/answers.md`, a starting
   point in `assets/answers.template.json`). Keys are the question heading text
   exactly as it appears.
6. **Dry run first.** `fill --no-submit` fills everything and stops before the
   irreversible Submit click. Check `missing` is empty.
7. **Submit** with `fill`. The script walks Back to page 1, fills each page,
   clicks Next until Submit appears, clicks Submit **once**, then verifies
   "Thank you for your response" and writes `gform-result.json`.
8. **Report** the recorded state and the response URL.

## Commands that work

```
node scripts/gform.mjs account list
node scripts/gform.mjs account add --email you@example.com --password "$PW" [--totp SECRET]
node scripts/gform.mjs account remove --email you@example.com

node scripts/gform.mjs inspect --url "<formUrl>" --email you@example.com
node scripts/gform.mjs fill --url "<formUrl>" --answers answers.json --email you@example.com --no-submit
node scripts/gform.mjs fill --url "<formUrl>" --answers answers.json --email you@example.com
node scripts/selftest.mjs        # the whole engine against a mock form, headless
```

- `--email E` - which account to act as. It selects the profile and the
  port, and pulls the saved password and TOTP secret.
- `--profile DIR` - the persistent Chrome profile (default: one per account
  under `~/.gform-profiles/`).
- `--port N` - the DevTools port (default: one per account, from 9400 up).
- `--no-submit` - stop before Submit.
- `--password P` - sign in with this password instead of the saved one.
- `--totp SECRET` - compute the 2FA code from this base32 secret.
- `--otp-file FILE` - a file the script polls for the 2FA code (it reads the
  first token, then clears the file). Without it and without a secret, the human
  types the code into the visible Chrome window and the script detects the
  sign-in completing.
- Credentials live in `~/.gform-accounts.json` on this machine (or
  `$GFORM_ACCOUNTS`). **Never write real credentials or personal answers into
  this repository.**

`scripts/selftest.mjs` proves the engine without touching a real form: it opens
`tests/mock-form.html` in a throwaway headless Chrome, fills it, submits it and
asserts what the page holds. Run it after changing the script.

## Mistakes to avoid

- **Launching a new Chrome per run.** That throws away the session and forces a
  fresh login every time. Attach instead.
- **Matching answers by `entry.<id>` name attribute.** Google no longer names
  text inputs. Match by question heading text.
- **Treating a grid row as one question.** Grid cells are radios whose
  `aria-label` is `"<value>, response for <row>"`; each row needs one cell.
- **Ignoring branch re-render.** Choosing an option can re-render the page and
  wipe what was just set. Fill, wait, re-read, repeat (the script does up to
  four passes per page).
- **Clicking Submit before a dry run.** Submit is the one irreversible action.
- **Closing the browser.** The human may still need it, and the session dies
  with it.
- **One profile for every account.** Two Google accounts in one Chrome profile
  fight over the session and sign each other out. One profile and one port per
  account.
- **Committing the account store.** `~/.gform-accounts.json` holds passwords
  and TOTP secrets. It stays on the machine.
