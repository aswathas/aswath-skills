'use strict';

/**
 * Build an Obsidian study vault for one subject, one unit at a time.
 *
 *   node build-notes.cjs --subject <subject.json> --vault <vault dir> --unit 1 [--all]
 *
 * subject.json shape: see reference/subject-schema.md (the analyst SubjectSpec).
 * Emits: course MOC, unit map, one full teaching note per topic, one file per
 * question (MCQ / Part B / Part C) with a diagram embedded, and one
 * Excalidraw drawing per diagram as <vault>/<Course>/Diagrams/<slug>.excalidraw.md
 */

const fs = require('fs');
const path = require('path');
const { scene } = require('./layout.cjs');
const { buildTopicNote, buildUnitRevisionSheet, mdTable } = require('./render-note.cjs');

const args = process.argv.slice(2);
const opt = (name, fallback = null) => {
  const i = args.indexOf('--' + name);
  return i === -1 ? fallback : args[i + 1];
};
const flag = (name) => args.includes('--' + name);

const SUBJECT_PATH = opt('subject');
const VAULT = opt('vault');
const UNIT_ARG = opt('unit');
const ALL = flag('all');

if (!SUBJECT_PATH || !VAULT) {
  console.error('usage: node build-notes.cjs --subject <subject.json> --vault <dir> --unit <n> | --all');
  process.exit(2);
}

const spec = JSON.parse(fs.readFileSync(SUBJECT_PATH, 'utf8'));
const COURSE = `${spec.shortTitle} ${spec.code}`;
const COURSE_DIR = path.join(VAULT, COURSE);
const CONTENT_DIR = opt('content', path.join(__dirname, '..', 'content'));

const PRIORITY_LABEL = { must: 'MUST LEARN', should: 'LEARN IF TIME', skip: 'SKIM ONLY' };
const PRIORITY_TAG = { must: 'must', should: 'should', skip: 'skim' };

function safe(name) {
  return name
    .replace(/[:\\/*?"<>|]/g, ' -')
    .replace(/\s+/g, ' ')
    .replace(/\s-\s/g, ' - ')
    .trim();
}

function slug(name) {
  return safe(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

function pad(n, width = 2) {
  return String(n).padStart(width, '0');
}

/**
 * Deep per-topic content, authored once per unit as
 * content/<code-lowercase>-u<unit>.json. Optional: the note falls back to the
 * analyst text when a topic has no deep entry, so nothing is ever blank.
 */
const deepByUnit = {};
const glossary = {};
const revisionByUnit = {};
const deepSources = [];

function loadDeep(unitNo) {
  const p = path.join(CONTENT_DIR, `${spec.code.toLowerCase()}-u${unitNo}.json`);
  if (!fs.existsSync(p)) return { byTopic: {}, glossary: {} };
  const raw = JSON.parse(fs.readFileSync(p, 'utf8'));
  const byTopic = {};
  for (const t of raw.topics || []) byTopic[t.name] = t;
  return { byTopic, glossary: raw.glossary || {}, revision: raw.revision, source: p };
}

// Load every authored unit, not just the one being built: the glossary and the
// topic -> term index must be complete even when writing a single unit.
for (const u of spec.units) {
  const d = loadDeep(u.unit);
  deepByUnit[u.unit] = d.byTopic;
  if (d.revision) revisionByUnit[u.unit] = d.revision;
  if (d.source) deepSources.push(d.source);
  for (const [term, body] of Object.entries(d.glossary)) {
    if (!glossary[term]) glossary[term] = body;
  }

  // A revision sheet may also live in its own file, so it can be authored or
  // rewritten without touching the topic content.
  const revPath = path.join(CONTENT_DIR, `${spec.code.toLowerCase()}-u${u.unit}-revision.json`);
  if (fs.existsSync(revPath)) {
    revisionByUnit[u.unit] = JSON.parse(fs.readFileSync(revPath, 'utf8')).revision;
  }
}

/**
 * Enrichment layer: content/<code>-u<n>-enrich.json holds the parts that are
 * expensive to author but cheap to merge — annotated code, written-out model
 * answers, advantages/limitations, memory tricks, modern context. Kept separate
 * from the base file so the base stays readable.
 */
function loadEnrich(unitNo) {
  // A unit may have several enrich files; later ones merge over earlier ones.
  const dir = CONTENT_DIR;
  if (!fs.existsSync(dir)) return {};
  const prefix = `${spec.code.toLowerCase()}-u${unitNo}-enrich`;
  const files = fs
    .readdirSync(dir)
    .filter((f) => f.startsWith(prefix) && f.endsWith('.json'))
    .sort();
  const merged = {};
  for (const f of files) {
    const topics = JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')).topics || {};
    for (const [name, extra] of Object.entries(topics)) {
      merged[name] = { ...(merged[name] || {}), ...extra };
    }
  }
  return merged;
}

// Merge enrichment into each topic's deep content, shallow per key so a base
// definition is never clobbered by an absent enrich key.
for (const u of spec.units) {
  const enrich = loadEnrich(u.unit);
  for (const [name, extra] of Object.entries(enrich)) {
    const base = deepByUnit[u.unit][name];
    if (!base) continue;
    for (const [k, v] of Object.entries(extra)) {
      if (k === 'examAnswer' && base.examAnswer) {
        base.examAnswer = { ...base.examAnswer, ...v };
      } else {
        base[k] = v;
      }
    }
  }
}

const deep = { byTopic: deepByUnit[UNIT_ARG || spec.units[0].unit] || {}, source: deepSources.join(', ') };
const deepTopics = deep.byTopic;

/**
 * Some syllabus topics ship no diagram in the analyst spec (the skim-only ones).
 * A note with no picture looks unfinished, so supply drawings for them here.
 * Keyed by topic name; unit-numbered in the file for clarity.
 */
const extraDiagrams = {};
{
  const p = path.join(CONTENT_DIR, `${spec.code.toLowerCase()}-diagrams-extra.json`);
  if (fs.existsSync(p)) {
    for (const t of JSON.parse(fs.readFileSync(p, 'utf8')).topics || []) {
      extraDiagrams[t.name] = t.diagram;
    }
  }
}

// Attach a fallback drawing to any topic that lacks one.
for (const u of spec.units) {
  for (const t of u.topics) {
    if (!t.diagram && extraDiagrams[t.name]) t.diagram = extraDiagrams[t.name];
  }
}

const TERM_INDEX = {};
for (const [term] of Object.entries(glossary)) {
  TERM_INDEX[term] = safe(term);
}
// A topic points at the glossary term defined for it, if one declares that topic.
for (const t of spec.units.flatMap((u) => u.topics)) {
  for (const [term, body] of Object.entries(glossary)) {
    if (body.topics && body.topics.includes(t.name)) {
      TERM_INDEX[t.name] = TERM_INDEX[t.name] || TERM_INDEX[term];
    }
  }
}
const termFor = (topicName) => TERM_INDEX[topicName] || null;

function emitGlossary() {
  const entries = Object.entries(glossary);
  if (!entries.length) return 0;
  const dir = 'Glossary';
  for (const [term, body] of entries) {
    const L = [];
    L.push(fm({
      title: `${term}`,
      course: spec.code,
      kind: 'term',
      tags: ['study', 'glossary', spec.code.toLowerCase()],
    }).trimEnd());
    L.push('', `# ${term}`, '');
    L.push(`Up: [[${COURSE}]] · Glossary: [[Glossary]]`, '');
    L.push('## Definition', '', body.definition, '');
    if (body.whyItMatters) L.push('## Why it matters in this course', '', body.whyItMatters, '');
    if (body.confusions) {
      L.push('## Do not confuse it with', '');
      for (const c of body.confusions) L.push(`- ${c}`);
      L.push('');
    }
    if (body.topics && body.topics.length) {
      L.push('## Used in', '');
      for (const t of body.topics) {
        const u = spec.units.find((uu) => uu.topics.some((tt) => tt.name === t));
        const idx = u ? u.topics.findIndex((tt) => tt.name === t) : -1;
        L.push(idx >= 0 ? `- [[${pad(idx + 1)} ${safe(t)}]]` : `- ${t}`);
      }
      L.push('');
    }
    write(path.join(dir, `${safe(term)}.md`), L.join('\n'));
  }
  const idxLines = [];
  idxLines.push(fm({ title: 'Glossary', course: spec.code, tags: ['study', 'glossary'] }).trimEnd());
  idxLines.push('', `# Glossary — ${spec.title}`, '', `Up: [[${COURSE}]]`, '');
  idxLines.push('Every term the paper expects you to use precisely. Learn the definition, not the vibe.', '');
  const rows = entries.map(([t, b]) => [`[[${safe(t)}]]`, b.definition.split('. ')[0].replace(/\.$/, '') + '.']);
  idxLines.push(mdTable(['Term', 'One-line meaning'], rows));
  idxLines.push('');
  write('Glossary/Glossary.md', idxLines.join('\n'));
  return entries.length;
}

const written = [];

function write(relPath, content) {
  const full = path.join(COURSE_DIR, relPath);
  fs.mkdirSync(path.dirname(full), { recursive: true });
  fs.writeFileSync(full, content, 'utf8');
  written.push(full);
}

function fm(fields) {
  const lines = ['---'];
  for (const [k, v] of Object.entries(fields)) {
    if (v === undefined || v === null) continue;
    if (Array.isArray(v)) lines.push(`${k}: [${v.join(', ')}]`);
    else lines.push(`${k}: ${v}`);
  }
  lines.push('---', '');
  return lines.join('\n');
}

/** Write a diagram as an Excalidraw plugin drawing and return its embed link. */
function emitDiagram(drawingName, diagram) {
  if (!diagram) return null;
  const rel = path.join('Diagrams', `${drawingName}.excalidraw.md`);
  const s = scene(diagram, { title: diagram.title });
  const body = [
    '---',
    'excalidraw-plugin: parsed',
    'tags: [excalidraw]',
    '',
    '---',
    '==⚠  Switch to EXCALIDRAW VIEW in the MORE OPTIONS menu of this document. ⚠== You can decompress Drawing data with the command palette: \'Decompress current Excalidraw file\'. For more info check in plugin settings under \'Saving\'',
    '',
    '## Drawing',
    '```json',
    JSON.stringify(s, null, '\t'),
    '```',
    '%%',
    '',
  ].join('\n');
  write(rel, body);
  return `![[${drawingName}.excalidraw]]`;
}

function link(fromDir, targetRel) {
  return `[[${targetRel.replace(/\\/g, '/').replace(/\.md$/, '').split('/').pop()}]]`;
}

const EXAM_SHAPE = `
| Part | Questions | Marks each | Attempted | Marks |
|---|---|---|---|---|
| A — MCQ | ${spec.blueprint.partA.count} | ${spec.blueprint.partA.marksEach} | all | ${spec.blueprint.partA.count * spec.blueprint.partA.marksEach} |
| B — long answers | ${spec.blueprint.partB.count} | ${spec.blueprint.partB.marksEach} | ${spec.blueprint.partB.answerAny} | ${spec.blueprint.partB.count * spec.blueprint.partB.marksEach} |
| C — long answers | ${spec.blueprint.partC.count} | ${spec.blueprint.partC.marksEach} | ${spec.blueprint.partC.answerAny} | ${spec.blueprint.partC.count * spec.blueprint.partC.marksEach} |
| **Total** | | | | **${spec.blueprint.total}** |
`.trim();

/* ------------------------------------------------------------------ course MOC */

function buildCourseMoc(units) {
  const lines = [];
  lines.push(fm({
    title: COURSE,
    code: spec.code,
    course: spec.title,
    semester: spec.semester,
    credits: spec.credits,
    exam: `${spec.examDate} ${spec.examSession}`,
    total: spec.blueprint.total,
    tags: ['study', 'course', `sem${spec.semester}`, spec.code.toLowerCase()],
  }).trimEnd());

  lines.push('', `# ${spec.title}`, '');
  lines.push(`> ${spec.oneLiner}`, '');
  lines.push(`**Exam:** ${spec.examDate} · ${spec.examSession}  `);
  lines.push(`**Credits:** ${spec.credits} · **Contact hours:** ${spec.hours}`);
  lines.push('', '## The paper, exactly', '', EXAM_SHAPE, '');
  lines.push(`> ${spec.pyqNote}`, '');
  lines.push('## Where the marks live', '');
  lines.push('| Unit | Topics | Marks claim |');
  lines.push('|---|---|---|');
  for (const c of spec.safeCombo) lines.push(`| U${c.unit} | ${c.topics.join(', ')} | ${c.claim} |`);
  lines.push('');
  lines.push('## Units', '');
  for (const u of units) {
    const must = u.topics.filter((t) => t.priority === 'must').length;
    lines.push(`- [[${unitMocName(u)}]] — ${u.topics.length} topics, ${must} must-know · ${u.hours} h`);
  }
  lines.push('', '## How to study', '');
  lines.push('1. Read the unit map first. It tells you what to skip.');
  lines.push('2. One topic per sitting: read the note, say the analogy out loud, redraw the diagram from memory.');
  lines.push('3. Close the note, answer the question files from memory, then check.');
  lines.push('4. The night before, read only the `must` notes and the fact sheet.');
  lines.push('');
  return lines.join('\n');
}

function unitMocName(u) {
  return `Unit ${u.unit} - ${safe(u.name)}`;
}

function topicFileName(u, t, index) {
  return path.join(unitMocName(u), `${pad(index + 1)} ${safe(t.name)}.md`);
}

function relToUnit(u, child) {
  return path.join(unitMocName(u), child);
}

/* ------------------------------------------------------------------- unit map */

function buildUnitMap(u, topics, questions) {
  const must = topics.filter((t) => t.priority === 'must');
  const should = topics.filter((t) => t.priority === 'should');
  const skim = topics.filter((t) => t.priority === 'skip');
  const mustMinutes = must.reduce((a, t) => a + t.minutes, 0);

  const L = [];
  L.push(fm({
    title: unitMocName(u),
    course: spec.code,
    unit: u.unit,
    hours: u.hours,
    total_topics: topics.length,
    must_topics: must.length,
    must_minutes: mustMinutes,
    tags: ['study', 'unit', spec.code.toLowerCase()],
  }).trimEnd());

  L.push('', `# Unit ${u.unit} — ${u.name}`, '');
  L.push(`> ${u.hours} contact hours · ${topics.length} topics · ${must.length} must-know · about ${mustMinutes} min of must-know reading.`, '');
  L.push(`Up: [[${COURSE}]]`, '');
  if (revisionByUnit[u.unit]) {
    L.push(`> **Night before:** [[${unitMocName(u)} - Revision Sheet]] — the whole unit on one page.`, '');
  }
  L.push('## Read in this order', '');
  L.push('| # | Topic | Priority | Min | Exam shape |');
  L.push('|---|---|---|---|---|');
  topics.forEach((t, i) => {
    L.push(`| ${i + 1} | [[${pad(i + 1)} ${safe(t.name)}]] | ${PRIORITY_LABEL[t.priority]} | ${t.minutes} | ${(t.why || '').replace(/\|/g, '/')} |`);
  });
  L.push('');

  if (skim.length) {
    L.push('## Safe to skim', '', skim.map((t) => `- ${t.name}`).join('\n'), '');
  }

  L.push('## Questions for this unit', '');
  if (!questions.length) {
    L.push('_No unit-specific question bank entries. This unit is examined through Part A breadth only._');
  } else {
    const byKind = { mcq: [], partB: [], partC: [] };
    for (const q of questions) byKind[q.kind].push(q);
    L.push('| Kind | File | Marks |');
    L.push('|---|---|---|');
    for (const q of questions) L.push(`| ${q.kind === 'mcq' ? 'MCQ' : q.kind === 'partB' ? 'Part B' : 'Part C'} | [[${q.fileBase}]] | ${q.marks} |`);
    L.push('');
    L.push(`Totals: ${byKind.mcq.length} MCQ · ${byKind.partB.length} Part B · ${byKind.partC.length} Part C.`);
  }
  L.push('');
  return L.join('\n');
}

/* --------------------------------------------------------------- topic note */


/* -------------------------------------------------------------- question note */

function buildQuestionNote(u, q, diagramEmbed, topicEmbed) {
  const isMcq = q.kind === 'mcq';
  const L = [];
  L.push(fm({
    title: q.title,
    course: spec.code,
    unit: u.unit,
    kind: q.kind,
    marks: q.marks,
    topic: q.topicName,
    tags: ['study', 'question', q.kind, spec.code.toLowerCase(), `u${u.unit}`],
  }).trimEnd());

  L.push('', `# ${q.title}`, '');
  L.push(`> **${isMcq ? '1 mark · Part A' : `${q.marks} marks · ${q.kind === 'partC' ? 'Part C' : 'Part B'}`}** · ${q.topicName}`, '');
  L.push(`Up: [[${unitMocName(u)}]] · Topic: [[${topicEmbed}]]`, '');

  if (diagramEmbed) {
    L.push('## Picture', '', diagramEmbed, '');
  }

  L.push('## Question', '');
  L.push(`> ${q.question}`, '');

  if (isMcq) {
    L.push('## Options', '');
    q.options.forEach((o, i) => L.push(`- [ ] ${String.fromCharCode(65 + i)}. ${o}`));
    L.push('');
    L.push('## Answer', '');
    L.push(`**${String.fromCharCode(65 + q.correct)}. ${q.options[q.correct]}**`, '');
    L.push(q.explanation, '');
  } else {
    L.push('## What the marker wants', '');
    L.push(q.keyPoints.map((k) => `- ${k}`).join('\n'), '');
    L.push('## Model answer', '');
    q.modelAnswer.forEach((p, i) => L.push(`${i + 1}. ${p}`));
    L.push('');
    L.push('## Answer shape', '');
    if (q.kind === 'partC') {
      L.push('| Marks | What it must contain |', '|---|---|');
      L.push('| 1–2 | Define the term precisely, one clause that removes ambiguity |');
      L.push('| 3–5 | Mechanism: the parts, in order, with a labelled diagram |');
      L.push('| 6–9 | Working: formula or trace, numbers substituted |');
      L.push('| 10–12 | A concrete named instance from the course |');
      L.push('| 13–15 | Trade-off, limitation or consequence, linked back |');
    } else {
      L.push('Claim · structure · working · example — four to six ordered points that map to the 8 marks.');
    }
    L.push('');
  }
  return L.join('\n');
}

/* ------------------------------------------------------------------- assembly */

/** Short, human title for a question file. */
function questionTitle(kind, n, question) {
  const head = `${kind} ${pad(n)}`;
  const words = question
    .replace(/[^A-Za-z0-9\s-]/g, ' ')
    .trim()
    .split(/\s+/)
    .slice(0, 9);
  // Drop a dangling connective so the filename reads as a phrase, not a cut.
  const DROP = new Set(['and', 'or', 'the', 'a', 'an', 'of', 'to', 'in', 'for', 'with', 'on', 'that']);
  while (words.length > 3 && DROP.has(words[words.length - 1].toLowerCase())) words.pop();
  return `${head} ${words.join(' ')}`;
}

/**
 * Pick the topic a question most plausibly tests. A unit-specific Part B/Part C
 * names several topics; score by the syllabus topic names appearing in the
 * question text, falling back to the first must-know topic.
 */
function bestTopicIndex(topics, q) {
  const hay = (q.question + ' ' + (q.keyPoints || []).join(' ')).toLowerCase();
  let best = -1;
  let bestScore = 0;
  topics.forEach((t, i) => {
    const clean = t.name.toLowerCase().replace(/[:()]/g, ' ');
    const words = clean.split(/\s+/).filter((w) => w.length > 4);
    const score = words.reduce((a, w) => a + (hay.includes(w) ? 1 : 0), 0);
    if (score > bestScore) {
      bestScore = score;
      best = i;
    }
  });
  if (best >= 0) return best;
  const must = topics.findIndex((t) => t.priority === 'must');
  return must >= 0 ? must : 0;
}

function collectQuestions(u) {
  const out = [];
  const mcq = spec.mcqs.filter((m) => m.unit === u.unit);
  const pb = spec.partB.filter((q) => q.unit === u.unit);
  const pc = spec.partC.filter((q) => q.unit === u.unit);

  mcq.forEach((m, i) => out.push({
    kind: 'mcq',
    marks: 1,
    title: questionTitle('MCQ', i + 1, m.question),
    fileBase: questionTitle('MCQ', i + 1, m.question),
    topicName: m.topic,
    prompt: m.question.slice(0, 70) + (m.question.length > 70 ? '…' : ''),
    question: m.question,
    options: m.options,
    correct: m.correct,
    explanation: m.explanation,
  }));
  pb.forEach((q, i) => out.push({
    kind: 'partB',
    marks: q.marks,
    title: questionTitle('Part B', i + 1, q.question),
    fileBase: questionTitle('Part B', i + 1, q.question),
    topicName: 'Multiple',
    prompt: q.question.slice(0, 70) + (q.question.length > 70 ? '…' : ''),
    question: q.question,
    modelAnswer: q.modelAnswer,
    keyPoints: q.keyPoints,
  }));
  pc.forEach((q, i) => out.push({
    kind: 'partC',
    marks: q.marks,
    title: questionTitle('Part C', i + 1, q.question),
    fileBase: questionTitle('Part C', i + 1, q.question),
    topicName: 'Multiple',
    prompt: q.question.slice(0, 70) + (q.question.length > 70 ? '…' : ''),
    question: q.question,
    modelAnswer: q.modelAnswer,
    keyPoints: q.keyPoints,
  }));
  return out;
}

function buildUnit(u) {
  const topics = u.topics;
  const questions = collectQuestions(u);

  const unitDir = unitMocName(u);
  const deepByTopic = deepByUnit[u.unit] || {};

  // Topic notes, each with its diagram.
  const topicFileBase = [];
  topics.forEach((t, i) => {
    const drawingName = `U${u.unit} ${pad(i + 1)} ${safe(t.name)}`;
    const embed = emitDiagram(drawingName, t.diagram);
    const qs = questions.filter((q) => q.topicName === t.name);
    const rel = topicFileName(u, t, i);
    const nextLink = i + 1 < topics.length ? `[[${pad(i + 2)} ${safe(topics[i + 1].name)}]]` : `back to [[${unitMocName(u)}]]`;
    write(
      rel,
      buildTopicNote({
        course: spec.code,
        courseTitle: spec.title,
        spec,
        unit: u,
        topic: t,
        index: i,
        diagramEmbed: embed,
        deep: deepByTopic[t.name],
        questionLinks: qs.map((q) => ({ ...q, fileBase: `Questions/${q.fileBase}` })),
        unitMocName: unitMocName(u),
        nextLink,
        term: termFor(t.name),
        index: i,
        total: topics.length,
      }),
    );
    topicFileBase.push({ t, base: `${pad(i + 1)} ${safe(t.name)}`, index: i });
  });

  // Question notes: one file each. The drawing is the diagram of the topic the
  // question actually tests; a question spanning several topics embeds the
  // best-matching topic's diagram rather than pointing at a drawing that does
  // not exist.
  for (const q of questions) {
    const topicIndex = bestTopicIndex(topics, q);
    const topic = topics[topicIndex];
    const embed = `![[U${u.unit} ${pad(topicIndex + 1)} ${safe(topic.name)}.excalidraw]]`;
    const topicEmbed = `${pad(topicIndex + 1)} ${safe(topic.name)}`;
    write(relToUnit(u, path.join('Questions', `${q.fileBase}.md`)), buildQuestionNote(u, q, embed, topicEmbed));
  }

  write(relToUnit(u, `${unitMocName(u)}.md`), buildUnitMap(u, topics, questions));

  // Revision sheet: the whole unit on one page, for the night before.
  const revision = revisionByUnit[u.unit];
  if (revision) {
    const base = `${unitMocName(u)} - Revision Sheet`;
    const L = [];
    L.push(
      [
        '---',
        `title: "Unit ${u.unit} Revision Sheet"`,
        `course: ${spec.code}`,
        `unit: ${u.unit}`,
        'kind: revision',
        `tags: [study, revision, ${spec.code.toLowerCase()}, u${u.unit}]`,
        '---',
        '',
      ].join('\n'),
    );
    L.push(`# Unit ${u.unit} — Complete Revision Sheet`, '');
    L.push(`> One page for the night before the exam. Everything else in this unit exists to build this.`, '');
    L.push(`Up: [[${unitMocName(u)}]]`, '');
    L.push(buildUnitRevisionSheet(u, revision, topics));
    L.push('---', '');
    if (revision.covered) L.push(`**Coverage:** ${revision.covered}`, '');
    write(relToUnit(u, `${base}.md`), L.join('\n'));
  }

  return topics.length;
}

const units = ALL ? spec.units : spec.units.filter((u) => String(u.unit) === String(UNIT_ARG));
if (!units.length) {
  console.error(`no unit matched --unit ${UNIT_ARG}`);
  process.exit(2);
}

console.log(`deep content: ${Object.keys(deepTopics).length} topics, ${Object.keys(glossary).length} glossary terms (${deep.source || 'none'})`);
const nTerms = emitGlossary();

const built = [];
for (const u of units) {
  const n = buildUnit(u);
  built.push(`U${u.unit}: ${n} topics, ${collectQuestions(u).length} question files`);
}

const mocPath = path.join(VAULT, `${COURSE}.md`);
if (!fs.existsSync(mocPath)) {
  fs.mkdirSync(VAULT, { recursive: true });
  fs.writeFileSync(mocPath, buildCourseMoc(spec.units), 'utf8');
  written.push(mocPath);
}

console.log('wrote ' + written.length + ' files' + (nTerms ? `, ${nTerms} glossary terms` : ''));
built.forEach((b) => console.log('  ' + b));
