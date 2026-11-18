---
name: aswath-gform-fill
description: Use when a Google Form (forms.gle or docs.google.com/forms) has to be filled and submitted - a survey, feedback form, feedback quiz, course end-of-course form - especially a long multi-page form with rating grids and branch questions, and especially when it needs a signed-in Google account, a 2FA code, or a human to log in once in a visible browser.
---

## Procedure

1. **Never restart the browser.** One persistent Chrome profile per machine
   (`--user-data-dir`) keeps the Google session alive. Scripts attach to the
   already-running browser over the DevTools protocol; they never close it and
   never relaunch it. A fresh temp profile each run means the human signs in
   every single time - that is the failure mode this skill exists to kill.
2. **Open the form once in that browser.** The human signs in there (password
   and 2FA if Google asks). After that the session is reused for every later
   form.
3. **Inspect before filling.** Run `inspect` to dump every page, question
   heading, option list and grid. Google Forms has 400+ defined questions but
   only the branch matching the chosen answers is live, so the live DOM is the
   only reliable source of what to answer.
4. **Write the answers file** (schema in `references/answers.md`, a starting
   point in `assets/answers.template.json`). Keys are the question heading text
   exactly as it appears.
5. **Dry run first.** `fill --no-submit` fills everything and stops before the
   irreversible Submit click. Check `missing` is empty.
6. **Submit** with `fill`. The script walks Back to page 1, fills each page,
   clicks Next until Submit appears, clicks Submit **once**, then verifies
   "Thank you for your response" and writes `gform-result.json`.
7. **Report** the recorded state and the response URL.

## Commands that work

```
node scripts/gform.mjs inspect --url "<formUrl>"
node scripts/gform.mjs fill --url "<formUrl>" --answers answers.json --no-submit
node scripts/gform.mjs fill --url "<formUrl>" --answers answers.json
node scripts/gform.mjs fill --url "<formUrl>" --answers answers.json \
     --email you@example.com --password "$PW" --otp-file /tmp/code.txt
node scripts/selftest.mjs        # the whole engine against a mock form, headless
```

- `--profile DIR` (default `~/.gform-profile`) - the persistent Chrome profile.
- `--port N` (default 9337) - the DevTools port.
- `--no-submit` - stop before Submit.
- `--email/--password` - automatic sign-in. Omit both and the script waits for
  the human to sign in in the open window.
- `--otp-file FILE` - a file the script polls for the 2FA code (it reads the
  first token, then clears the file). Without it, the human types the code into
  the visible Chrome window and the script detects the sign-in completing.
- Credentials come from the command line or a local file. **Never write real
  credentials or personal answers into this repository.**

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
