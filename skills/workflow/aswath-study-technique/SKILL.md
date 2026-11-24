---
name: aswath-study-technique
description: Build exam-ready Obsidian study vaults for university subjects — unit maps, one full teaching note per syllabus topic with an Excalidraw diagram, per-question files with diagrams, glossary, and active-recall cards. Use when the user wants to study/prepare for an exam from a syllabus or analysis PDF ("start studying for X", "make unit-wise notes", "obsidian notes for my exam", "exam ready notes").
compatibility: Windows. Needs Obsidian installed, the obsidian-excalidraw-plugin in the vault, Node 18+ for the builders, and Python + Pillow (only if you want to render-check layout).
---

# aswath-study-technique

Turn a syllabus into a vault a student can actually revise from. Not a summary
generator: every topic gets what it is, why it exists, how it works, an analogy, a
diagram, a model answer, the terminology, the traps, and recall cards.

## The teaching contract (applies to every note you write)

Act as the student's teacher, strategist and technical mentor. The goal is not to
answer questions but to make them able to answer without you.

**Explain from first principles, in this order.** What it is → why it exists →
what problem it solves → how it works internally → a real analogy → a practical
example → where it is used. Simple → intuitive → technical → practical. Never
assume a prerequisite has been established.

**Depth layers.** Intuition (plain English) → problem (why it was necessary) →
mechanism (ordered steps) → example (real scenario) → technical depth
(terminology, tradeoffs, internals) → practical application. Use only the layers
the topic deserves; never mechanically all six.

**Answer shape.** Direct answer first, then expand only as needed. Headings for
distinct ideas, bullets for lists, tables for comparisons, numbered steps for
processes, a diagram for anything structural. No walls of text, no filler
introductions, no restating the prompt.

**Retention.** Chunking, mental models, memory hooks, analogies, Feynman
explanations, links to previously learned topics, active recall, short recaps,
progressive difficulty. For long topics build the mental map first.

**Honesty.** Distinguish verified fact, estimate, assumption and opinion. Be
honest when an idea is weak or a topic is genuinely ambiguous in the syllabus.
Never fabricate a citation, statistic or exam pattern.

**Modes** (select silently, do not announce): TEACH (deep concepts), FAST
(direct answer), EXAM (syllabus-focused, memorisable), REVISION (condensed,
high-retention), DEBUG (find the real cause). The vault is EXAM + TEACH; the
recall cards are REVISION.

## What the vault looks like

```
<vault>/
  <Course> <CODE>.md                  course MOC: paper shape, marks, unit links
  <Course> <CODE>/
    Unit 1 - <name>/
      Unit 1 - <name>.md              unit map: read order, priorities, questions
      01 <Topic>.md                   one full teaching note per syllabus topic
      Questions/
        MCQ 01 - <topic>.md           one file per question, diagram embedded
        Part B 01 - <question>.md
    Diagrams/
      U1 01 <Topic>.excalidraw.md     real plugin drawing, embedded in the note
    Glossary/
      Glossary.md + Term - <term>.md
```

Every syllabus topic is verbatim from the official syllabus. Never paraphrase a
topic name — an examiner uses those words.

## Build pipeline

The pipeline has four stages. Run them in order; each stage is verifiable.

### 1. Get the syllabus, unit by unit

Prefer structured data over prose. If the subject already exists as an analysis
PDF or spec, extract the source it was rendered from rather than re-reading the
PDF: the structured form has topics, priorities, diagram specs and question banks.

Fallback: read the official syllabus PDF and list topic names verbatim.

```bash
python scripts/extract-subject.py --ts <subject.ts> --out subject.json
# or, from a PDF with a text layer:
pdftotext -layout syllabus.pdf syllabus.txt
```

### 2. Author the deep content

The analyst spec gives a one-liner, three principles, an analogy and a diagram.
That is a summary, not a lesson. Content is split across three files per unit so
each stays readable and can be rewritten independently:

| File | Holds | Why separate |
|---|---|---|
| `<code>-u<n>.json` | definitions, problems, mechanisms, terminology, recall, `revision` | the spine |
| `<code>-u<n>-enrich.json` | annotated code, full model answers, advantages/limitations, memory tricks, modern context | the expensive layer, merged over the spine |
| `<code>-u<n>-revision.json` | the one-page revision sheet (mental map, top questions, drill) | rewritten last, per unit |

Base file:

```json
{
  "unit": 2,
  "glossary": { "Term": { "definition": "...", "whyItMatters": "...",
                           "confusions": ["..."], "topics": ["Topic A"] } },
  "topics": [{
    "name": "Structure of a Contract",
    "definition": "One precise sentence.",
    "problem": "The old problem this solves.",
    "scenario": "A concrete situation that makes it necessary.",
    "mechanism": ["Step 1...", "Step 2..."],
    "terminology": [["Term", "Meaning"]],
    "examAnswer": { "question": "Likely question.", "points": ["1 mark...", "..."] },
    "traps": ["What loses marks."],
    "revision": "One line to memorise.",
    "recall": [["Question", "Answer"]]
  }]
}
```

Enrichment file — the layer that separates a summary from a lesson:

```json
{
  "topics": {
    "Structure of a Contract": {
      "code": [{ "title": "...", "lang": "solidity", "snippet": "...",
                 "breakdown": [["pragma solidity", "Compiler version constraint"]],
                 "note": "..." }],
      "examAnswer": { "question": "...", "full": "The whole answer, written out." },
      "advantages": ["..."],
      "limitations": ["..."],
      "memoryTrick": "**State = data | Function = action.**",
      "modernNote": "What has changed since the course material was written."
    }
  }
}
```

Rules that matter:

- `definition` must be one sentence a marker would award the first mark for.
- `mechanism` is ordered and names parts, not adjectives.
- `examAnswer.full` is the answer a student could copy: definition, components in
  order, worked numbers, consequence. `points` is the tick-list beside it.
- `code` must come with a `breakdown` table — a snippet with no line-by-line
  meaning is a wall of syntax.
- `advantages` **and** `limitations` together. A benefit with no stated cost
  scores as an unexamined claim.
- `memoryTrick` is one line, mnemonic, and survives being said out loud.
- `traps` earns its place only if it prevents a real, common error.
- `recall` answers live in collapsible `<details>` — active recall, not reading.
- `modernNote` matters where tooling is dead: Mist, pyethapp, pre-Merge geth.
  Earn the marks for the syllabus *and* say what is true now.

Anything omitted falls back to the analyst text, so no section is ever empty.

### 3. Render

```bash
node scripts/build-notes.cjs --subject subject.json --vault "C:\Users\ADMIN\Projects\Sem7 Prep" --unit 1
```

Writes the course MOC (once), the unit map, one note per topic, one file per
question, the drawings, the glossary, and the unit revision sheet. `--all` builds
every unit; run one unit at a time in practice so you can check quality before
scaling.

### 4. Gate on depth, not on "it rendered"

A note that renders is not a note that teaches. This is the check that matters:

```bash
python scripts/verify-vault.py "<vault>/<Course> <CODE>" subject.json
```

For every **must-know** topic it requires a precise definition, an ordered
mechanism of ≥3 steps, a model answer, advantages *or* traps, ≥3 recall cards,
and an embedded drawing; it warns when a memory hook is missing. It exits 1 on
failure, so it can gate a build. Skim topics only need to exist.

Passing this is the difference between a summary and an exam-ready note:

| Thin (fails) | Deep (passes) |
|---|---|
| one definition line | definition + the problem it solves + a concrete scenario |
| three bullets | ordered mechanism you can write as the answer body |
| "you should know this" | annotated code with a line-by-line table |
| "benefits" | advantages **and** the cost that pays for each |
| nothing to practise | model answer written out + recall cards with answers |

### 5. Verify the drawings actually render

A drawing can be valid JSON and still be unreadable. Check every one:

```bash
python scripts/render.py <scene>.json <out>.png     # then LOOK at the PNGs
```

Layout rules learned the hard way:

- Flow diagrams go **top to bottom**. A wide left-to-right chain is clipped in
  the note's preview pane.
- Keep labels quoted and short; a box that wraps looks broken.
- Compare layouts are two columns with the pairing as a row, never a long list.
- Cycle layouts need the arrow endpoints pulled inside the box edge, otherwise
  the arrowhead crosses the label.
- Never ship a half-drawn or clipped board — "it renders" is not "it is legible".

## The Excalidraw format (get this exactly right)

A drawing is `<name>.excalidraw.md` with plugin frontmatter and a JSON scene:

```markdown
---
excalidraw-plugin: parsed
tags: [excalidraw]

---
==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: 'Decompress current Excalidraw file'. For more info check in plugin settings under 'Saving'

## Drawing
```json
{"type":"excalidraw","version":2,"source":"...","elements":[...],"files":{},"appState":{...}}
```
%%
```

- Uncompressed `json` is valid and needs no library. `compressed-json` needs
  LZString `compressToBase64` — only worth it for large hand-drawn scenes.
- `elements[].index` must be absent or a valid fractional index; a bad one makes
  the plugin restore an empty scene.
- Embed with an Obsidian embed, no parentheses:
  `![[U1 01 Blockchain Evolution.excalidraw]]`
- The note is not the deliverable — the rendered preview is. Say which note you
  created and let the window speak.

## First-run setup (do this once per vault)

1. Install the plugin into `<vault>/vault/.obsidian/plugins/obsidian-excalidraw-plugin/`
   (`main.js`, `manifest.json`, `styles.css` from the release asset).
2. Add `"obsidian-excalidraw-plugin"` to `.obsidian/community-plugins.json`.
3. **Register the vault in `%APPDATA%\obsidian\obsidian.json` — without a BOM.**
   PowerShell's `Set-Content -Encoding UTF8` writes a BOM and Obsidian then
   silently ignores the whole vault list. Write it with
   `[System.IO.File]::WriteAllText(..., (New-Object System.Text.UTF8Encoding($false)))`
   or a Node `fs.writeFileSync(p, s, 'utf8')`.
4. The first launch asks "Do you trust the author of this vault?" — the plugin
   does not load until that is accepted.
5. Windows paths are case-insensitive. `Projects\Sem7-Prep` and
   `Projects\sem7-prep` are **the same folder**. Pick a genuinely distinct name,
   and confirm with `dir` before generating into it.

## Gotchas

- **Do not generate into a folder that already holds a project.** Check first.
- Obsidian rewrites `obsidian.json` on quit, so register the vault while it is
  closed, then launch.
- Electron windows expose nothing to UI Automation — click by screen coordinates.
- A minimised or background browser steals focus; minimise it before screenshotting.
- If a note looks wrong, it is the Markdown, not a hidden editor pane.
- `--unit N` is idempotent: re-running rewrites that unit's files and leaves the
  other units alone. The course MOC is written once.

## Commands

| Task | Command |
|---|---|
| Build one unit | `node scripts/build-notes.cjs --subject subject.json --vault <v> --unit 1` |
| Build all units | same, `--all` |
| Render a drawing to PNG | `python scripts/render.py scene.json out.png` |
| Verify a scene parses | `node -e "JSON.parse(...)"` on the fenced block |
| Open the vault | `obsidian://open?path=<url-encoded absolute path>` |

## Definition of done for one unit

- [ ] Every syllabus topic has a note, named verbatim.
- [ ] Each note has: definition, problem, mechanism, analogy, diagram, model
      answer, terminology, traps, recall cards.
- [ ] Every drawing renders and is legible at default zoom.
- [ ] Each question has its own file with the diagram embedded.
- [ ] The unit map lists read order, priorities and links to every question.
- [ ] The glossary links each term to the topics that use it.
