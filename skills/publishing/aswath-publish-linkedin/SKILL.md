---
name: aswath-publish-linkedin
description: Use when publishing, scheduling, deleting, or checking LinkedIn posts from an AI agent — including phrases like "post to LinkedIn", "share on LinkedIn", "publish my update", "check my LinkedIn posts", or any task naming LinkedIn as the destination.
---

# Publish to LinkedIn

Two paths on this machine. **postiee first** — it is the user's own CLI on the
official LinkedIn API, it is already authenticated, and it handles images and
carousels. The `everyhand-linkedin` MCP is the fallback and is text-only.

## Path 1 — postiee (default)

Binary: `C:\Users\aswat\postiee-bin\postiee.exe` — **not on PATH**, call it by full path.

| Task | Command |
|---|---|
| Auth check | `postiee.exe --agent auth status` |
| Text post | `postiee.exe post "shipped v0.1 today"` |
| Post from file | `postiee.exe post --file body.md` |
| One image | `postiee.exe post --file body.md --image chart.png --alt "a line chart"` |
| Multi-image (v0.2.0+) | repeat `--image`; alts pipe-separated in order: `--alt 'first|second|third'` |
| Search own posts | `postiee.exe search "pistol"` |
| History | `postiee.exe history` |
| Delete a post | `postiee.exe unpublish urn:li:ugcPost:7518369029841895424` |
| Health | `postiee.exe doctor` |

Limits and behaviour:

- LinkedIn caps a post at ~3000 characters. Keep under it.
- One image posts as the legacy `content.media` shape; two or more becomes
  `content.multiImage`. The URN in the returned URL proves which path ran.
- Near-duplicate content gets throttled by the algorithm. Three posts of the
  same weekend in a few hours means reach drops per post — flag it once, then
  act on the explicit instruction.
- The post URL appears **only** in postiee's stdout. Never construct it.

## Path 2 — everyhand-linkedin MCP (fallback)

Tool `li_publish(text, visibility, confirm)`. Text only, max 3000 chars,
max 3 posts/hour and 10/day.

Two-step confirm, both paths:

1. First call returns `needs_confirm` plus a preview and a 6-digit code shown
   to the account owner.
2. Call again with the same arguments plus `confirm=<the 6-digit code>` **only
   after the owner says yes**. Single use, 6 minutes, never guess it.

If `li_status` reports `logged_out`, the session is expired — stop and tell the
user to log in through the EveryHand app, then `li_daemon action=reload`, then
re-check `li_status` before posting.

## Rules

- Show the exact text and images to the user and get an explicit go-ahead
  before the first publish call. A post cannot be recalled.
- Do not run `postiee login` without an explicit request — it opens a browser
  and blocks on OAuth.
- Do not use unofficial LinkedIn clients, cookie scrapers, or the
  `linkedin-api` npm package for posting. postiee is the official-API path.
- The same post within 10 minutes returns the first result (`duplicate: true`),
  never a second post. Do not retry it as a "failure".
- On a 429 with `cooldown_until`, wait. Do not retry.
- Clean up scratch files in `/home/aswath/` after posting.

## Verifying what a viewer actually sees

`postiee search` reads **postie's local record of what it sent**, not LinkedIn.
A byte-identical match proves what went out; it does not prove what renders.

To see the rendered post, open the live URL in a browser and read the DOM:

```bash
agent-browser open "https://www.linkedin.com/feed/update/urn:li:ugcPost:<id>/"
agent-browser get text body
```

## Two characters that break a post

**Never put an unescaped `(` in a LinkedIn post body.** LinkedIn truncates the
post at the first unescaped parenthesis: everything from that character onward
is silently dropped, and the post looks fine to the sender. Verified across
five live posts: no parenthesis -> stored whole; a parenthesis -> the post ends
exactly there. `)` on its own is harmless, but a post with `(` anywhere gets cut.

**Never put `_` in the body.** LinkedIn strips underscores from the rendered
post: `curl_cffi` renders as `curlcffi`, `applied_filters` as `appliedfilters`.
Use a hyphen instead (`curl-cffi`) — pip treats them as the same package name.

Both rules are enforced by `tools/linkedin_post.py` in the olx-car-search repo.

After posting, always re-read the live DOM and check the last line is there.
A post that silently lost its tail still looks correct in postie's history.


