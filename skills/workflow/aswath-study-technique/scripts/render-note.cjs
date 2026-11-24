'use strict';

/**
 * Deep, exam-ready note rendering.
 *
 * A topic note must let a student (a) understand the idea from scratch and
 * (b) write a full answer under exam pressure. Those are different jobs, so the
 * note carries both:
 *
 *   UNDERSTAND                          ANSWER
 *   1 What it is (definition)           7 Model answer, written out
 *   2 The scenario that forces it       8 Terminology to use
 *   3 See the mechanism (diagram)       9 Exam traps
 *   4 How it works (ordered steps)     10 Memory trick
 *   5 The code, annotated              11 How it is examined
 *   6 Worked example / advantages      12 Active recall
 *
 * Sections are numbered dynamically, so a missing piece never leaves a gap.
 * Content comes from content/<code>-u<n>.json; anything absent falls back to the
 * analyst text so no section is ever empty.
 */

const LABEL = { must: 'MUST LEARN', should: 'LEARN IF TIME', skip: 'SKIM ONLY' };
const TAG = { must: 'must', should: 'should', skip: 'skim' };

function mdTable(headers, rows) {
  const out = [`| ${headers.join(' | ')} |`, `|${headers.map(() => '---').join('|')}|`];
  for (const r of rows) out.push(`| ${r.map((c) => String(c).replace(/\|/g, '/')).join(' | ')} |`);
  return out.join('\n');
}

function buildTopicNote({
  course,
  unit,
  topic,
  diagramEmbed,
  deep,
  questionLinks,
  unitMocName,
  nextLink,
  term,
  index,
  total,
}) {
  const L = [];
  const d = deep || {};
  let n = 0;
  const head = (title) => {
    n += 1;
    L.push(`## ${n}. ${title}`, '');
  };

  L.push(
    [
      '---',
      `title: "${topic.name}"`,
      `course: ${course}`,
      `unit: ${unit.unit}`,
      `priority: ${topic.priority}`,
      `minutes: ${topic.minutes}`,
      `tags: [study, ${TAG[topic.priority]}, ${course.toLowerCase()}, u${unit.unit}]`,
      '---',
      '',
    ].join('\n'),
  );

  L.push(`# ${topic.name}`, '');
  L.push(
    `> **${LABEL[topic.priority]}** · ${topic.minutes} min · Unit ${unit.unit} — ${unit.name}${total ? ` · topic ${index + 1} of ${total}` : ''}`,
    '',
  );
  L.push(`Up: [[${unitMocName}]]${term ? ` · Key term: [[${term}]]` : ''}`, '');

  if (topic.why) {
    L.push(`**Why it is on the paper:** ${topic.why}`, '');
  }

  // 1 What it is
  if (d.definition || (topic.principles && topic.principles[0])) {
    head('What it is');
    if (d.definition) {
      L.push(`**Definition.** ${d.definition}`, '');
      L.push('> Open every answer with this. It is usually worth the first 1–2 marks.', '');
    } else {
      L.push(topic.principles[0], '');
    }
  }

  // 2 The problem / scenario
  if (d.problem || d.scenario) {
    head('Why it exists — the problem that forced it');
    if (d.problem) L.push(d.problem, '');
    if (d.scenario) {
      L.push('**Situation.**', '');
      L.push(d.scenario, '');
    }
  }

  // 3 Diagram
  if (diagramEmbed) {
    head('See the mechanism');
    L.push(diagramEmbed, '');
    if (topic.diagram && topic.diagram.caption) L.push(`*${topic.diagram.caption}*`, '');
  }

  // 4 Mechanism
  if (d.mechanism || (topic.principles && topic.principles.length > 1)) {
    head('How it works — step by step');
    if (d.mechanism) d.mechanism.forEach((m, i) => L.push(`${i + 1}. ${m}`));
    else topic.principles.slice(1).forEach((p) => L.push(`- ${p}`));
    L.push('');
    L.push(
      '> In the exam this ordered list **is** the answer body. Name the parts in order and you earn the mechanism marks.',
      '',
    );
  }

  // 5 Code, annotated
  if (d.code && d.code.length) {
    head('The code, annotated');
    for (const c of d.code) {
      if (c.title) L.push(`**${c.title}**`, '');
      L.push('```' + (c.lang || 'solidity'), c.snippet, '```', '');
      if (c.breakdown && c.breakdown.length) {
        L.push(mdTable(['Code', 'Meaning'], c.breakdown), '');
      }
      if (c.note) L.push(`*${c.note}*`, '');
    }
  }

  // 6 Worked example
  if (topic.example) {
    head('Worked example');
    L.push('```text', topic.example, '```', '');
    L.push('> Redo this with the note closed. Reproducing the numbers is what converts reading into marks.', '');
  }

  // Advantages / limitations — the trade-off pair a marker looks for
  if ((d.advantages && d.advantages.length) || (d.limitations && d.limitations.length)) {
    head('Advantages and limitations');
    if (d.advantages && d.advantages.length) {
      L.push('**Advantages**', '');
      d.advantages.forEach((a) => L.push(`- ${a}`));
      L.push('');
    }
    if (d.limitations && d.limitations.length) {
      L.push('**Limitations / trade-offs**', '');
      d.limitations.forEach((x) => L.push(`- ${x}`));
      L.push('');
    }
    L.push('> Every benefit here is paid for somewhere. Naming the cost is what separates a 6 from a 12.', '');
  }

  // 7 Model answer
  if (d.examAnswer) {
    head('Model answer — write this');
    L.push(`**Likely question.** ${d.examAnswer.question}`, '');
    if (d.examAnswer.full) {
      L.push(d.examAnswer.full, '');
      L.push(
        `> Full written answer. The numbered structure is exactly what a marker ticks: definition, components in order, consequence.`,
        '',
      );
    }
    if (d.examAnswer.points) {
      L.push('**Point structure**', '');
      d.examAnswer.points.forEach((p, i) => L.push(`${i + 1}. ${p}`));
      L.push('');
    }
  }

  // 8 Terminology
  if (d.terminology) {
    head('Terminology to use precisely');
    L.push(mdTable(['Term', 'Meaning'], d.terminology), '');
  }

  // 9 Traps
  if (d.traps) {
    head('Exam traps');
    d.traps.forEach((t) => L.push(`- ⚠️ ${t}`));
    L.push('');
  }

  // 10 Memory trick
  if (d.memoryTrick) {
    head('Memory trick');
    L.push(`> 🧠 ${d.memoryTrick}`, '');
  }

  // 11 How examined
  head('How it is examined');
  L.push(`> ${topic.why || 'Part A breadth.'}`, '');
  if (d.modernNote) {
    L.push(`**Modern context.** ${d.modernNote}`, '');
  }

  // 12 Recall
  head('Active recall');
  L.push('Answer with the note closed. If you cannot answer one, that section is not learned yet.', '');
  if (d.recall) {
    d.recall.forEach(([q, a], i) => {
      L.push(`${i + 1}. **${q}**`);
      L.push(`    <details><summary>Answer</summary>${a}</details>`);
      L.push('');
    });
  } else {
    (topic.principles || []).forEach((p, i) => L.push(`${i + 1}. Restate and explain: ${p}`));
    L.push('');
  }

  if (questionLinks && questionLinks.length) {
    head('Practice from the question bank');
    for (const q of questionLinks) L.push(`- [[${q.fileBase}]] — ${q.prompt}`);
    L.push('');
  }

  L.push('---', '', `Next: ${nextLink}`, '');
  return L.join('\n');
}

/** The unit revision sheet: mental map, top questions, 5-minute drill. */
function buildUnitRevisionSheet(u, d, questionFileBases) {
  const L = [];
  const topics = u.topics;

  L.push('## The whole unit in one mental map', '');
  if (d.mentalMap && d.mentalMap.length) {
    L.push('| # | Block | What it answers |', '|---|---|---|');
    d.mentalMap.forEach((b, i) => L.push(`| ${i + 1} | **${b.label}** | ${b.sub} |`));
  } else {
    L.push('| # | Topic | Exam shape |', '|---|---|---|');
    topics.forEach((t, i) => L.push(`| ${i + 1} | ${t.name} | ${t.why || ''} |`));
  }
  L.push('');

  if (d.topExamQuestions && d.topExamQuestions.length) {
    L.push('## Prepare these first', '');
    L.push('Highest probability questions for this unit, in order.', '');
    d.topExamQuestions.forEach((q, i) => L.push(`${i + 1}. ${q}`));
    L.push('');
  }

  if (d.drill && d.drill.length) {
    L.push('## 5-minute final memory drill', '');
    L.push('Cover the right column and answer out loud. Timed, the night before.', '');
    L.push(mdTable(['Question', 'Answer in one line'], d.drill), '');
  }

  return L.join('\n');
}

module.exports = { buildTopicNote, buildUnitRevisionSheet, mdTable };
