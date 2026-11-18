# aswath-delivery:feedback-loop

A sub-module of `aswath-delivery`. It governs the part of delivery that happens
*after* the file lands: what the recipient says about it, and what must change
in the next build.

Speed never licenses a defect. "Fast" means the rebuild is one pass, not that
the first pass ships blind.

## The loop

1. **Send.** One build, one send. Clean chat first, as the parent skill says.
2. **Wait for the verdict, do not guess it.** A "." or a thumbs-up is not
   approval. Approval is silence on the artefact itself, or an explicit
   "ok/looks good" about the artefact.
3. **Log every complaint as a defect row**, not as a feeling. A complaint is
   only actionable once it names: what was wrong, which artefact element, and
   what "right" looks like. "Report is not good" is a signal to re-read the
   brief, not a diff to write.
4. **Classify each defect** before touching the build:
   - `MISSING` — an element of the reference/format was absent (logo, seal,
     signature block, section, front-matter page).
   - `MISMATCH` — an element was present but not an exact replica of the
     reference (style, ordering, wording, numbering, line layout).
   - `DEFECT` — something wrong in the content itself (wrong data, broken
     layout, false claim).
   - `MISSED-BRIEF` — a requirement that was stated and not met.
5. **Rebuild once, with every logged defect in the same pass.** Defects do not
   get fixed one at a time across several sends. The recipient must not have
   to re-review three times.
6. **Re-send cleanly.** Revoke the superseded file, send the new build once,
   delete the staging copy. One live file in the chat.
7. **Close the loop** — say what changed in one line, and mark which defect
   rows are closed.

## Format-fidelity checklist (run before every send)

Fast is only acceptable when the format check is mechanical. Walk this list
against the *reference artefact* (the format PDF the recipient supplied), not
against memory of it:

- **Branding** — logo present on every page that carries one, correct file,
  correct aspect ratio, correct position and correct size. Extract the logo
  from the reference PDF's own image objects; do not redraw or substitute it.
- **Cover data** — project title, course code, department, all three team
  names with registration numbers, guide name, institution line, month/year.
- **Front-matter order** — declaration, certificate, acknowledgements, abstract,
  contents, list of figures, list of tables, abbreviations.
- **Chapter order and numbering** — matches the reference exactly.
- **Page-number scheme** — roman for front matter, arabic restarting at the
  body, matching the reference.
- **References** — exact replica of the reference's citation style, including
  how the bracketed number is laid out, whether titles are quoted or italic,
  whether page ranges and editions are given, and whether URLs appear at all.
- **Figures and tables** — captioned and numbered the way the reference numbers
  them, and listed in the front matter.

If the recipient supplies a format artefact, the format artefact is the spec.
"No quality checks" is not a scope reduction — it is a scheduling constraint
that the checklist above satisfies in seconds.

## Measure the reference, do not eyeball it

Eyeballing page images misses differences the recipient notices immediately.
Instead, extract the reference's actual geometry and copy it:

```python
import fitz
d = fitz.open("reference.pdf")
p = d[0]
for im in p.get_images(full=True):                 # logos, seals
    for r in p.get_image_rects(im[0]):
        print(r.x0, r.y0, r.width, r.height)       # place and size, in points
for b in p.get_text("dict")["blocks"]:             # type, size, position
    for l in b.get("lines", []):
        for s in l["spans"]:
            print(round(s["bbox"][0]), round(s["bbox"][1]),
                  s["size"], s["font"], s["text"][:60])
```

Point conversion when rebuilding: `width_pt / 72 * inch`. Getting this wrong
scales the logo to a fraction of its true size — a defect the recipient sees
before reading a word.

Then render the reference page and your page side by side into one image and
compare them in a single pass, rather than reviewing two files separately.

## Always offer the editable source

When the recipient says they need to change something, they are telling you
they want to make the change themselves. Do not only rebuild — send them an
editable copy of the same document so they can work directly, and ask what
specifically needs changing so the next rebuild is one pass.

A PDF-to-DOCX conversion (`pdf2docx`) gives a faithful, fully editable
document with images intact. Send it alongside the PDF, once each.

## Defect log format

Keep it as a short table so the next build has a checklist, not a memory:

```
| # | class | element | what was wrong | what right looks like | status |
|---|-------|---------|----------------|----------------------|--------|
| 1 | MISSING | cover logo | SRM logo absent from cover | logo extracted from the reference PDF's image objects, placed first, aspect preserved | closed |
| 2 | MISMATCH | pages 1-3 | front pages did not follow the reference layout | title 18pt, names 16pt, logo 177x65pt centred; declaration logo top-left with title block right; certificate 'Certified that ... is the bonafide work of ...' with two signature blocks | closed |
```

## Rules

- One send per build. No "here it is again" without a defect being fixed.
- Never ship a file the checklist has not been run against.
- Never leave a revoked file's caption text standing as the latest message.
- The owner gets the defect log summary; the recipient gets the file and one
  line about what changed.
- If a complaint is vague, re-read the reference artefact before asking a
  question. The answer is usually in the artefact the recipient already sent.
- When the complaint names a page range ("first 3 pages"), diff exactly that
  range against the reference before rebuilding. The complaint is a pointer to
  a region, and that region is where the defect lives.
