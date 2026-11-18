---
description: Fill and submit a Google Form with any of your saved Google accounts.
argument-hint: <formUrl> [--email you@example.com] [--no-submit]
---

Fill and submit the Google Form at `$ARGUMENTS`.

Follow the `aswath-gform-fill` skill in `skills/utilities/aswath-gform-fill/SKILL.md`.

1. If the arguments name no email, list the saved accounts and pick the one the
   user means; if there is exactly one, use it:
   `node skills/utilities/aswath-gform-fill/scripts/gform.mjs account list`
2. If that email is not saved yet, add it with the password (and the TOTP
   secret, if the account has one) — ask the user for the password, never for
   it twice:
   `node skills/utilities/aswath-gform-fill/scripts/gform.mjs account add --email <email> --password <password>`
   The store lives at `~/.gform-accounts.json` on this machine and is never
   committed.
3. Inspect the form, then fill it from an answers file:
   `node skills/utilities/aswath-gform-fill/scripts/gform.mjs inspect --url <formUrl> --email <email>`
   `node skills/utilities/aswath-gform-fill/scripts/gform.mjs fill --url <formUrl> --answers <file> --email <email> --no-submit`
4. Show the dry-run result. Only if nothing is missing, run the same command
   without `--no-submit`.
5. Report the recorded state and the response URL.

Never commit an account's password or TOTP secret. Never click Submit twice.
