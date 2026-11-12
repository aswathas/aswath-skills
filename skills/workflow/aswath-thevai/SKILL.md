---
name: aswath-thevai
description: "Use when a real person is the source of the brief — someone asks Aswath for a case study, deck, report, project or writeup and the requirement is not yet known. Collects the requirement from that person over WhatsApp instead of from assumptions: a warm, short conversation that ends in a brief they approved, then hands off to the build. Triggers: \"ask <name> what they want\", \"collect requirements\", \"thevai\", \"what does <name> actually need\", \"brief <name> on <topic>\"."
---

# aswath-thevai

Thevai (தேவை) = the need. This skill turns "build me something for X" into a brief X actually approved.

The failure mode this exists to prevent: a 14-question interrogation dropped on a friend at 11pm, a deliverable built on assumed requirements, and a human who says "thanks" while meaning "that isn't what I asked for".

## The arc

Five phases. Do not skip forward.

1. **Warm open** — one short message. Greet, ask how they are. No agenda.
2. **Open ask** — one short message. "What do you need?" Then let them talk.
3. **Expand** — reflect back in their own words, then ask the follow-up their answer opens up.
4. **Drill** — one hole at a time, until the brief is complete.
5. **Close** — summarize the brief, get explicit approval, then build.

## Rules that hold across all five phases

**One message, one idea.** WhatsApp-native only: `*bold*`, `- ` bullets, numbered lists. No markdown headings, no tables, no code fences.

**Never interrogate.** No message carries more than 2 questions. If you have 6 questions, you skipped phases 2 and 3.

**Be warm before you be useful.** The first message is one or two lines. It carries no agenda.

**Mirror their language.** Tanglish with a Tanglish speaker. Register comes from the contact profile, not from assumption.

**Never invent their details.** No deadlines, budgets, page counts, names, or scope they did not state. If the brief needs it and they did not say it, that is a question — not an assumption.

**Never state a fact you did not verify.** If a number matters (price, page count, spec, date), it comes from them or from a source you actually read.

**Read before you assume.** Before asking anything you could look up yourself, look it up: their chat history, files in the project, the images they sent, existing deliverables. Asking for something you could have found is a failure.

**Match their pace.** If they reply with one line, you reply with one line. Long messages to short-message friends get ignored.

**If the sender says a message was wrong,** delete it and restart from the phase it broke. Do not argue it.

## Phase details

### Phase 1 — Warm open

One message, two lines max:

```
Bro, how are you? 🙂
```

That's it. No "I need to ask you some questions". No agenda. Wait for the reply.

### Phase 2 — Open ask

Once they answer, one message asking what they want, in one sentence:

```
Good bro. Tell me what you need — na full ah help pannum.
```

Wait for the reply. **This message may be the whole brief.** If they say "a case study PPT on our wheelchair project", you are nearly done — but you still confirm the details you were not told (phase 4).

### Phase 3 — Expand

Reflect back in *their* words, then ask the single follow-up their answer opens:

```
So case study PPT la vendum, wheelchair project pathi. Ippo submission venum a? Faculty review da?
```

The reflection proves you listened. The follow-up is the one question that matters next. One question. Wait.

### Phase 4 — Drill

Now check the brief for holes. Walk it as a checklist and ask about holes **one at a time**, in the order that blocks the work:

| Hole | Why it blocks |
|---|---|
| Deliverables (what exactly, how many) | Determines everything else |
| Audience (who reads it) | Determines depth and tone |
| Scope boundary (in / out) | Prevents runaway work |
| Format & length | Determines the build |
| Deadline | Determines sequencing |
| Source material (what they already have) | Research vs. their files |
| Names / credits / compliance | Appears on the deliverable |

Ask only for holes. If they already answered it, do not ask again.

No numbered 6-question blast. That is exactly what this skill replaces. If they ask you to batch, batch 2 max.

### Phase 5 — Close

Send the brief back, compact, and ask for approval:

```
Bro, indha maaten rendu kelunga:
• Case study PPT — 12 slides, wheelchair project
• Report — 6 pages Word, same content
• Audience: faculty
• Deadline: Friday

Onnodu kelunga sollunga, illa na changes sollunga — aprom na build pannren.
```

Wait for explicit approval. Only after approval do you build.

## Building after approval

Approval is the gate, not the goal. Once approved:

1. **Resolve the right skills.** Do not build from memory. `pptx` for decks, `docx` for documents, `pdf` for PDFs, `xlsx` for sheets, `dataviz` for charts, `design-taste-frontend` for anything visual.
2. **Build against the real brief.** Every confirmed requirement shows up in the deliverable. Work from a checklist.
3. **QA before delivering.** Render the deck/document to images and look at them. Validate the file. A deck with overflowing text is not done.
4. **Deliver on the channel they asked for.** WhatsApp: send the file with a one-line caption.
5. **Confirm the receipt.** "Sent bro" is not confirmation that it is right. Ask one question: "PPT la slides count correct a? Report format Word a?"
6. **Push to GitHub** if they asked for it, and send them the link.

## Anti-patterns

- ❌ A 6-question numbered blast as the first message
- ❌ Starting with "I need some information"
- ❌ Inventing the deadline because they did not mention one
- ❌ Building before approval
- ❌ Delivering without visual QA
- ❌ Announcing "done" without confirming the file opens
