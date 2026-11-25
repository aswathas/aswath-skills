'use strict';

const THEME = {
  bg: '#ffffff',
  ink: '#1e1e1e',
  muted: '#64748b',
  line: '#475569',
  accent: '#2563eb',
  accentFill: '#dbeafe',
  warn: '#b91c1c',
  warnFill: '#fee2e2',
  good: '#15803d',
  goodFill: '#dcfce7',
};

const FONT_HAND = 1;
const FONT_NORMAL = 2;
const FONT_CODE = 3;

let seq = 0;
const id = (p) => `${p}-${(++seq).toString(36)}`;

function base(type, x, y, w, h, extra = {}) {
  return {
    id: id(type),
    type,
    x,
    y,
    width: w,
    height: h,
    angle: 0,
    strokeColor: THEME.ink,
    backgroundColor: 'transparent',
    fillStyle: 'solid',
    strokeWidth: 2,
    strokeStyle: 'solid',
    roughness: 1,
    opacity: 100,
    groupIds: [],
    frameId: null,
    roundness: type === 'rectangle' ? { type: 3 } : null,
    seed: Math.floor(Math.random() * 100000) + 1,
    version: 1,
    versionNonce: Math.floor(Math.random() * 1000000) + 1,
    isDeleted: false,
    boundElements: null,
    updated: Date.now(),
    link: null,
    locked: false,
    ...extra,
  };
}

function textAt(str, x, y, opts = {}) {
  const fontSize = opts.fontSize ?? 16;
  const lineHeight = 1.25;
  const lines = String(str).split('\n');
  const longest = lines.reduce((a, b) => (b.length > a.length ? b : a), '');
  const width = Math.max(40, Math.round(longest.length * fontSize * 0.56));
  const height = Math.round(lines.length * fontSize * lineHeight);
  return base('text', Math.round(x), Math.round(y), width, height, {
    strokeColor: opts.color ?? THEME.ink,
    text: String(str),
    originalText: String(str),
    fontSize,
    fontFamily: opts.font ?? FONT_HAND,
    textAlign: opts.align ?? 'center',
    verticalAlign: 'top',
    containerId: null,
    lineHeight,
    autoResize: true,
    backgroundColor: 'transparent',
    roundness: null,
  });
}

function centerText(str, boxX, boxY, boxW, boxH, opts = {}) {
  const fontSize = opts.fontSize ?? 16;
  const lines = String(str).split('\n');
  const est = Math.max(40, Math.round(Math.max(...lines.map((l) => l.length)) * fontSize * 0.56));
  const h = Math.round(lines.length * fontSize * 1.25);
  const x = opts.align === 'left' ? boxX + 18 : boxX + boxW / 2 - est / 2;
  const y = boxY + boxH / 2 - h / 2;
  const el = textAt(str, x, y, { ...opts, align: opts.align ?? 'center' });
  el.width = Math.max(est, 40);
  return el;
}

function box(x, y, w, h, opts = {}) {
  const kind = opts.kind ?? 'plain';
  return base('rectangle', x, y, w, h, {
    strokeColor: THEME.ink,
    backgroundColor: 'transparent',
    fillStyle: 'solid',
    roundness: { type: 3 },
    strokeWidth: kind === 'core' ? 3 : 2,
    strokeColor: kind === 'core' ? THEME.accent : kind === 'warn' ? THEME.warn : THEME.ink,
    backgroundColor: kind === 'core' ? THEME.accentFill : kind === 'warn' ? THEME.warnFill : 'transparent',
    ...(opts.extra ?? {}),
  });
}

function arrow(x1, y1, x2, y2) {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const len = Math.hypot(dx, dy) || 1;
  const mid = { x: Math.round(dx / 2), y: Math.round(dy / 2) };
  return base('arrow', x1, y1, Math.abs(dx), Math.abs(dy), {
    strokeColor: THEME.line,
    strokeWidth: 2,
    roundness: { type: 2 },
    points: [[0, 0], [mid.x, mid.y], [dx, dy]],
    lastCommittedPoint: null,
    startBinding: null,
    endBinding: null,
    startArrowhead: null,
    endArrowhead: 'arrow',
  });
}

const BOX = { w: 320, h: 96, subFont: 13 };

function node(boxEl, label, sub, kind) {
  const els = [boxEl];
  if (sub) {
    els.push(
      centerText(label, boxEl.x, boxEl.y + 12, boxEl.width, 34, { fontSize: 18, font: FONT_NORMAL }),
      centerText(sub, boxEl.x, boxEl.y + 48, boxEl.width, 28, { fontSize: BOX.subFont, color: THEME.muted, font: FONT_NORMAL }),
    );
  } else {
    els.push(centerText(label, boxEl.x, boxEl.y, boxEl.width, boxEl.height, { fontSize: 18, font: FONT_NORMAL }));
  }
  return els;
}

function titleEl(title, x, y) {
  return textAt(title, x, y, { fontSize: 24, align: 'left', font: FONT_NORMAL });
}

function captionEl(caption, x, y) {
  return textAt(caption, x, y, { fontSize: 14, align: 'left', color: THEME.muted, font: FONT_NORMAL });
}

/** Vertical chain. Reads top to bottom, which survives narrow preview panes. */
function layoutFlow(d) {
  const els = [];
  const x = 120;
  const y0 = 96;
  const gap = 62;
  let y = y0;
  const positions = [];
  for (const n of d.nodes) {
    const b = box(x, y, BOX.w, BOX.h, { kind: n.kind });
    els.push(...node(b, n.label, n.sub, n.kind));
    positions.push({ x, y, w: BOX.w, h: BOX.h });
    y += BOX.h + gap;
  }
  const edges = d.edges ?? d.nodes.slice(1).map((_, i) => [i, i + 1]);
  for (const e of edges) {
    const [a, b] = e;
    if (positions[a] && positions[b]) {
      els.push(arrow(positions[a].x + BOX.w / 2, positions[a].y + BOX.h, positions[b].x + BOX.w / 2, positions[b].y));
    }
  }
  return { els, width: x + BOX.w + 120, height: y + 60 };
}

/** Layered stack, widest boxes, down arrows between layers. */
function layoutStack(d) {
  const els = [];
  const w = 560;
  const h = 92;
  const x = 60;
  const gap = 54;
  let y = 96;
  const pos = [];
  for (const n of d.nodes) {
    const b = box(x, y, w, h, { kind: n.kind });
    els.push(...node(b, n.label, n.sub, n.kind));
    pos.push({ y });
    y += h + gap;
  }
  for (let i = 0; i + 1 < pos.length; i++) {
    els.push(arrow(x + w / 2, pos[i].y + h, x + w / 2, pos[i + 1].y));
  }
  return { els, width: x + w + 60, height: y + 40 };
}

/** Two columns, row-aligned. Left column and right column mirror each other. */
function layoutCompare(d) {
  const els = [];
  const w = 460;
  const h = 88;
  const lx = 60;
  const rx = 640;
  const rowGap = 34;
  const rows = Math.ceil(d.nodes.length / 2);
  for (let r = 0; r < rows; r++) {
    const y = 96 + r * (h + rowGap);
    const left = d.nodes[r];
    const right = d.nodes[r + rows];
    if (left) {
      const b = box(lx, y, w, h, { kind: left.kind });
      els.push(...node(b, left.label, left.sub, left.kind));
    }
    if (right) {
      const b = box(rx, y, w, h, { kind: right.kind });
      els.push(...node(b, right.label, right.sub, right.kind));
    }
    if (left && right) {
      els.push(arrow(lx + w + 6, y + h / 2, rx - 6, y + h / 2));
    }
  }
  return { els, width: rx + w + 60, height: 96 + rows * (h + rowGap) + 20 };
}

/** Grid of pairs; used for property -> mechanism mappings. */
function layoutMatrix(d) {
  const els = [];
  const w = 460;
  const h = 84;
  const cols = [60, 640];
  const rows = Math.ceil(d.nodes.length / 2);
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < 2; c++) {
      const n = d.nodes[r * 2 + c];
      if (!n) continue;
      const b = box(cols[c], 96 + r * (h + 30), w, h, { kind: n.kind });
      els.push(...node(b, n.label, n.sub, n.kind));
    }
  }
  return { els, width: cols[1] + w + 60, height: 96 + rows * (h + 30) + 10 };
}

/** Ring: boxes on an ellipse, arrows following the order. */
function layoutCycle(d) {
  const els = [];
  const n = d.nodes.length;
  const w = 270;
  const h = 86;
  const cx = 520;
  const cy = 400;
  const rx = 300;
  const ry = 240;
  const pos = [];
  for (let i = 0; i < n; i++) {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    pos.push({ x: Math.round(cx + rx * Math.cos(a) - w / 2), y: Math.round(cy + ry * Math.sin(a) - h / 2) });
  }
  for (let i = 0; i < n; i++) {
    const b = box(pos[i].x, pos[i].y, w, h, { kind: d.nodes[i].kind });
    els.push(...node(b, d.nodes[i].label, d.nodes[i].sub, d.nodes[i].kind));
  }
  for (let i = 0; i < n; i++) {
    const a = pos[i];
    const b = pos[(i + 1) % n];
    const ax = a.x + w / 2;
    const ay = a.y + h / 2;
    const bx = b.x + w / 2;
    const by = b.y + h / 2;
    const ux = (bx - ax) / (Math.hypot(bx - ax, by - ay) || 1);
    const uy = (by - ay) / (Math.hypot(bx - ax, by - ay) || 1);
    els.push(arrow(Math.round(ax + ux * w * 0.42), Math.round(ay + uy * h * 0.62), Math.round(bx - ux * w * 0.42), Math.round(by - uy * h * 0.62)));
  }
  return { els, width: 1060, height: 760 };
}

/** Parent -> single child fan, then child -> leaves. For "one idea, many consequences". */
function layoutTree(d) {
  const els = [];
  const w = 300;
  const h = 84;
  const root = d.nodes[0];
  const rootX = 400;
  const rootY = 96;
  const b = box(rootX, rootY, w, h, { kind: root.kind ?? 'core' });
  els.push(...node(b, root.label, root.sub, root.kind));
  const kids = d.nodes.slice(1);
  const colW = 320;
  const totalW = Math.max(kids.length * colW, 700);
  // Keep the first child box inside the canvas: a wide fan centred on the root
  // would otherwise start at a negative x and get clipped off the left edge.
  const startX = Math.max(rootX + w / 2 - totalW / 2 + colW / 2, PAD + w / 2);
  kids.forEach((k, i) => {
    const kx = Math.round(startX + i * colW - w / 2);
    const ky = rootY + 210;
    const kb = box(kx, ky, w, h, { kind: k.kind });
    els.push(...node(kb, k.label, k.sub, k.kind));
    els.push(arrow(rootX + w / 2, rootY + h, kx + w / 2, ky));
  });
  return { els, width: Math.max(1060, startX + colW * kids.length), height: rootY + 210 + h + 60 };
}

function layout(d) {
  switch (d.kind) {
    case 'stack':
      return layoutStack(d);
    case 'compare':
      return layoutCompare(d);
    case 'matrix':
      return layoutMatrix(d);
    case 'cycle':
      return layoutCycle(d);
    case 'tree':
      return layoutTree(d);
    default:
      return layoutFlow(d);
  }
}

const PAD = 40;

/** Build a complete Excalidraw scene (legacy .excalidraw JSON) from a compact diagram spec. */
function scene(diagram, meta = {}) {
  seq = 0;
  const { els, width, height } = layout(diagram);
  const head = [];
  if (diagram.title) head.push(titleEl(diagram.title, PAD, 26));
  const shift = diagram.title ? 0 : 0;
  const all = head.length ? [...head, ...els.map((e) => ({ ...e, y: e.y + shift }))] : els;
  const bottom = Math.max(...all.map((e) => e.y + e.height), 0) + 40;
  if (diagram.caption) all.push(captionEl(diagram.caption, PAD, bottom));
  return {
    type: 'excalidraw',
    version: 2,
    source: 'aswath-study-technique',
    elements: all,
    files: {},
    appState: { gridSize: null, viewBackgroundColor: '#ffffff' },
    meta,
  };
}

module.exports = { scene, THEME };
