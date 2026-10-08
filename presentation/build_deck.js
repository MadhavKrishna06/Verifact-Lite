/**
 * VERIFACT-Lite presentation.
 *
 * Minimal, professional styling: white slides, a single accent colour, hairline
 * rules instead of filled panels. The Texas Tech identity is present only as a
 * hint — TTU scarlet #E90802 for the section label and for emphasis, with
 * Tahoma (TTU's listed tertiary face) for headings and Arial for body text.
 *
 * Everything sits on one grid: a 0.6" margin each side, a 12.1" content width,
 * and 0.3" gutters, so two-, three- and four-column rows share edges.
 *
 * Every number in this deck is measured by the repository; none is estimated.
 *   node presentation/build_deck.js
 */

const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(path.join(
  "C:",
  "Users",
  "MADHAV",
  "AppData",
  "Roaming",
  "Claude",
  "local-agent-mode-sessions",
  "skills-plugin",
  "0657de4b-ad51-46af-9c5f-44475feaa128",
  "11795ba8-6e61-4cbe-80c3-d7ed46414a61",
  "skills",
  "pptx",
  "scripts",
  "apply_theme.js"
));

const OUT = path.join(__dirname, "VERIFACT-Lite-TTU.pptx");

/* ----------------------------------------------------------------- palette */

const ACCENT = "E90802"; // TTU scarlet, used sparingly
const INK = "1A1A1A"; // headings
const BODY = "444444"; // body copy
const MUTED = "767676"; // labels, captions, footnotes
const HAIR = "DCDCDC"; // borders and rules
const PANEL = "F4F4F4"; // the one fill tone
const WHITE = "FFFFFF";

const THEME = {
  name: "VERIFACT-Lite",
  headFontFace: "Tahoma",
  bodyFontFace: "Arial",
  colors: {
    dk1: INK,
    lt1: WHITE,
    dk2: BODY,
    lt2: PANEL,
    accent1: ACCENT,
    accent2: MUTED,
    accent3: BODY,
    accent4: PANEL,
    accent5: INK,
    accent6: ACCENT,
    hlink: ACCENT,
    folHlink: MUTED,
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "VERIFACT-Lite";
pres.company = "Texas Tech University";
pres.title = "VERIFACT-Lite";
pres.subject = "Reimplementation of VeriFact (EMNLP 2025)";

/* ------------------------------------------------------------------- grid */

const M = 0.6; // left and right margin
const W = 12.1; // content width
const GUT = 0.3; // gutter between columns
const TOP = 1.75; // first content row

/** Geometry for column `i` of `cols`, optionally spanning `span` columns. */
function col(i, cols, span) {
  const w = (W - GUT * (cols - 1)) / cols;
  const n = span || 1;
  return { x: M + i * (w + GUT), w: w * n + GUT * (n - 1) };
}

/* ---------------------------------------------------------------- layouts */

pres.defineSlideMaster({ title: "COVER", background: { color: WHITE } });

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: WHITE },
  slideNumber: { x: 12.4, y: 6.92, w: 0.4, h: 0.28, fontSize: 9, color: MUTED, align: "right" },
});

/* ---------------------------------------------------------------- helpers */

/** Small scarlet section label above the title. */
function eyebrow(slide, text) {
  slide.addText(text.toUpperCase(), {
    isTextBox: true,
    objectName: "eyebrow",
    x: M,
    y: 0.38,
    w: W,
    h: 0.26,
    fontSize: 10,
    bold: true,
    charSpacing: 2,
    color: ACCENT,
    fontFace: "Arial",
    valign: "middle",
    margin: 0,
  });
}

/** Slide title. */
function title(slide, text) {
  slide.addText(text, {
    isTextBox: true,
    objectName: "title",
    x: M,
    y: 0.68,
    w: W,
    h: 0.6,
    fontSize: 27,
    bold: true,
    color: INK,
    valign: "middle",
    margin: 0,
  });
}

/** Descriptor line under the title, closed by a hairline rule. */
function subtitle(slide, text) {
  slide.addText(text, {
    isTextBox: true,
    objectName: "subtitle",
    x: M,
    y: 1.3,
    w: W,
    h: 0.28,
    fontSize: 13.5,
    color: MUTED,
    fontFace: "Arial",
    valign: "middle",
    margin: 0,
  });
  slide.addShape(pres.ShapeType.rect, {
    objectName: "head-rule",
    x: M,
    y: 1.64,
    w: W,
    h: 0.012,
    fill: { color: HAIR },
    line: { color: HAIR, width: 0.25 },
  });
}

/** Footnote along the bottom margin. */
function note(slide, text) {
  slide.addText(text, {
    isTextBox: true,
    objectName: "note",
    x: M,
    y: 6.88,
    w: 11.6,
    h: 0.3,
    fontSize: 9.5,
    color: MUTED,
    fontFace: "Arial",
    valign: "middle",
    margin: 0,
  });
}

/**
 * A card: hairline border, white or panel fill. `accent: true` marks the one
 * that matters — a scarlet heading and a scarlet left edge, nothing more.
 */
function card(slide, o) {
  const fill = o.panel ? PANEL : WHITE;
  slide.addShape(pres.ShapeType.rect, {
    objectName: o.name,
    x: o.x,
    y: o.y,
    w: o.w,
    h: o.h,
    fill: { color: fill },
    line: { color: o.panel ? PANEL : HAIR, width: 0.75 },
  });
  if (o.accent) {
    slide.addShape(pres.ShapeType.rect, {
      objectName: o.name + "-edge",
      x: o.x,
      y: o.y,
      w: 0.032,
      h: o.h,
      fill: { color: ACCENT },
      line: { color: ACCENT, width: 0.25 },
    });
  }
  const px = o.x + 0.28;
  const pw = o.w - 0.56;
  let ty = o.y + 0.22;
  if (o.badge) {
    slide.addText(o.badge, {
      isTextBox: true,
      objectName: o.name + "-badge",
      x: px,
      y: ty,
      w: pw,
      h: 0.32,
      fontSize: 16,
      bold: true,
      color: o.accent ? ACCENT : MUTED,
      margin: 0,
    });
    ty += 0.42;
  }
  if (o.heading) {
    slide.addText(o.heading, {
      isTextBox: true,
      objectName: o.name + "-h",
      x: px,
      y: ty,
      w: pw,
      h: 0.32,
      fontSize: o.headingSize || 14.5,
      bold: true,
      color: o.headingColor || (o.accent ? ACCENT : INK),
      margin: 0,
    });
    ty += 0.44;
  }
  if (o.body) {
    slide.addText(o.body, {
      isTextBox: true,
      objectName: o.name + "-b",
      x: px,
      y: ty,
      w: pw,
      h: o.y + o.h - ty - 0.18,
      fontSize: o.bodySize || 12.5,
      color: BODY,
      fontFace: "Arial",
      lineSpacingMultiple: 1.25,
      margin: 0,
      valign: "top",
    });
  }
}

/** Figure tile: a rule, a label, a number. No box. */
function stat(slide, o) {
  slide.addShape(pres.ShapeType.rect, {
    objectName: o.name + "-rule",
    x: o.x,
    y: o.y,
    w: o.w,
    h: 0.028,
    fill: { color: o.emph ? ACCENT : HAIR },
    line: { color: o.emph ? ACCENT : HAIR, width: 0.25 },
  });
  slide.addText(o.label.toUpperCase(), {
    isTextBox: true,
    objectName: o.name + "-l",
    x: o.x,
    y: o.y + 0.16,
    w: o.w,
    h: 0.24,
    fontSize: 9.5,
    bold: true,
    charSpacing: 1,
    color: MUTED,
    fontFace: "Arial",
    margin: 0,
  });
  slide.addText(o.value, {
    isTextBox: true,
    objectName: o.name + "-v",
    x: o.x,
    y: o.y + 0.42,
    w: o.w,
    h: 0.5,
    fontSize: o.valueSize || 26,
    bold: true,
    color: o.emph ? ACCENT : INK,
    margin: 0,
  });
  if (o.foot) {
    slide.addText(o.foot, {
      isTextBox: true,
      objectName: o.name + "-f",
      x: o.x,
      y: o.y + 0.95,
      w: o.w,
      h: 0.46,
      fontSize: 10.5,
      color: MUTED,
      fontFace: "Arial",
      lineSpacingMultiple: 1.1,
      margin: 0,
    });
  }
}

/** Table: one tinted header row, hairline grid, no zebra striping. */
function table(slide, o) {
  const head = o.head.map((h, i) => ({
    text: h,
    options: {
      bold: true,
      color: INK,
      fill: { color: PANEL },
      align: i === 0 ? "left" : o.align || "right",
      fontFace: "Arial",
    },
  }));
  const rows = [head].concat(
    o.rows.map((r) =>
      r.map((cell, ci) => {
        const isObj = typeof cell === "object" && cell !== null;
        const text = isObj ? cell.text : cell;
        const emph = isObj && cell.emph;
        return {
          text: String(text),
          options: {
            color: emph ? ACCENT : BODY,
            bold: !!emph,
            fill: { color: WHITE },
            align: ci === 0 ? "left" : o.align || "right",
            fontFace: "Arial",
          },
        };
      })
    )
  );
  slide.addTable(rows, {
    objectName: o.name,
    x: o.x,
    y: o.y,
    w: o.w,
    colW: o.colW,
    rowH: o.rowH || 0.32,
    fontSize: o.fontSize || 11.5,
    border: { type: "solid", color: HAIR, pt: 0.5 },
    valign: "middle",
    margin: [0.04, 0.12, 0.04, 0.12],
  });
}

const CHART_BASE = {
  showTitle: false,
  showLegend: true,
  legendPos: "b",
  legendFontFace: "+mn-lt",
  legendFontSize: 10.5,
  legendColor: MUTED,
  catAxisLabelColor: BODY,
  catAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 10.5,
  valAxisLabelColor: MUTED,
  valAxisLabelFontFace: "+mn-lt",
  valAxisLabelFontSize: 9.5,
  valGridLine: { color: "EFEFEF", size: 1 },
  catGridLine: { style: "none" },
  dataLabelFontFace: "+mn-lt",
  dataLabelFontSize: 10,
  dataLabelColor: BODY,
};

/* ----------------------------------------------------------------- slides
 * 15 slides, paced for a 15-minute talk (~15:00 of content).
 * Per-slide timings are the first line of each slide's speaker notes.
 *
 * Flow (problem -> paper -> reproduction -> our contribution -> next steps):
 *    1      title
 *    2      the problem
 *    3      the solution: VeriFact
 *    4      how VeriFact works
 *    5-9    recreating the results, 1..5
 *   10-12   our contribution, 1..3
 *   13      comparison with the paper
 *   14      future plans and next steps
 *   15      takeaways
 *   16      backup, not presented
 *
 * One backup slide follows for the question period; it is not part of the
 * 15 minutes and can be deleted without touching the talk.
 *
 * Numbers come from three runs over the SAME 12 generated answers:
 *   laptop-3B   Qwen2.5-3B primary, Qwen2.5-3B + Llama-3.2-3B judges
 *   judges-7B   Qwen2.5-3B primary, Qwen2.5-7B + Llama-3.1-8B judges   (Colab T4)
 *   full-7B     Qwen2.5-7B primary, Qwen2.5-7B + Llama-3.1-8B judges   (Colab T4)
 * -------------------------------------------------------------------------- */

/* 1 — title  [0:20] */
pres.addSection({ title: "Talk" });
let s = pres.addSlide({ masterName: "COVER", sectionTitle: "Talk" });
s.addText("Paper reimplementation  ·  Neural Networks".toUpperCase(), {
  isTextBox: true,
  objectName: "cover-eyebrow",
  x: M,
  y: 2.05,
  w: W,
  h: 0.3,
  fontSize: 11,
  bold: true,
  charSpacing: 2,
  color: ACCENT,
  fontFace: "Arial",
  margin: 0,
});
s.addText("VERIFACT-Lite", {
  isTextBox: true,
  objectName: "cover-title",
  x: M,
  y: 2.45,
  w: W,
  h: 1.0,
  fontSize: 50,
  bold: true,
  color: INK,
  margin: 0,
});
s.addShape(pres.ShapeType.rect, {
  objectName: "cover-rule",
  x: M + 0.03,
  y: 3.58,
  w: 1.9,
  h: 0.05,
  fill: { color: ACCENT },
  line: { color: ACCENT, width: 0.25 },
});
s.addText(
  "Reproducing a context-preserving fact-verification pipeline with open-source, locally hosted models",
  {
    isTextBox: true,
    objectName: "cover-body",
    x: M,
    y: 3.88,
    w: 11.2,
    h: 0.4,
    fontSize: 16,
    color: BODY,
    fontFace: "Arial",
    margin: 0,
  }
);
s.addText("By", {
  isTextBox: true,
  objectName: "cover-by-label",
  x: M,
  y: 4.42,
  w: 11.2,
  h: 0.26,
  fontSize: 10,
  bold: true,
  charSpacing: 2,
  color: MUTED,
  fontFace: "Arial",
  margin: 0,
});
s.addText(
  "Madhav Krishna Arumulla  ·  Sanskar Jadhav  ·  Sri Charan Komati Reddy  ·  Gourav Verma  ·  Trinath Reddy Vundela",
  {
    isTextBox: true,
    objectName: "cover-by",
    x: M,
    y: 4.7,
    w: 11.6,
    h: 0.32,
    fontSize: 13,
    bold: true,
    color: INK,
    fontFace: "Arial",
    margin: 0,
  }
);
// Chips are laid out left to right from one width estimate, so the row stays
// aligned whatever the labels say.
let chipX = M;
[
  "Qwen2.5-3B to Llama-3.1-8B",
  "Q4_K_M, 4 GB GPU and a T4",
  "Wikipedia evidence",
  "12 questions, 86 reference facts",
].forEach((t, i, all) => {
  const w = t.length * 0.093 + 0.46;
  const last = i === all.length - 1;
  s.addShape(pres.ShapeType.roundRect, {
    objectName: "chip" + i,
    x: chipX,
    y: 5.35,
    w,
    h: 0.4,
    rectRadius: 0.2,
    fill: { color: WHITE },
    line: { color: last ? ACCENT : HAIR, width: 0.75 },
  });
  s.addText(t, {
    isTextBox: true,
    objectName: "chip-t" + i,
    x: chipX,
    y: 5.35,
    w,
    h: 0.4,
    fontSize: 11,
    color: last ? ACCENT : BODY,
    align: "center",
    valign: "middle",
    fontFace: "Arial",
    margin: 0,
  });
  chipX += w + 0.22;
});
s.addText("Liu, Zhang, Munir, Gu & Wang — EMNLP 2025  ·  Not a reproduction of the paper's reported results", {
  isTextBox: true,
  objectName: "cover-foot",
  x: M,
  y: 6.35,
  w: W,
  h: 0.3,
  fontSize: 10.5,
  color: MUTED,
  fontFace: "Arial",
  margin: 0,
});
s.addNotes(
  "[0:20] One sentence: we rebuilt the paper's mechanism on local hardware, measured it against its own baseline, then re-ran the whole thing with larger judges to find out which conclusions were real. Move on quickly."
);

/* 2 — the problem  [1:15] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "The problem");
title(s, "Atomic facts lose the context that makes them true");
subtitle(s, "The challenge of context-free fact verification");
card(s, { name: "quote", x: M, y: TOP, w: W, h: 0.8, panel: true });
s.addText(
  [
    { text: "Model answer:  ", options: { bold: true, color: MUTED, fontSize: 11.5 } },
    {
      text: '"If the demand for gold as jewelry were to disappear, the price of gold could drop by 20–50% or more, ',
      options: { color: INK, fontSize: 14 },
    },
    { text: "making", options: { color: ACCENT, bold: true, fontSize: 14 } },
    { text: ' it more competitive with other materials like copper and silver."', options: { color: INK, fontSize: 14 } },
  ],
  {
    isTextBox: true,
    objectName: "quote-text",
    x: M + 0.28,
    y: TOP + 0.08,
    w: W - 0.56,
    h: 0.64,
    fontFace: "Arial",
    lineSpacingMultiple: 1.12,
    margin: 0,
    valign: "middle",
  }
);
const c2a = col(0, 2);
const c2b = col(1, 2);
card(s, { name: "safe", x: c2a.x, y: 2.75, w: c2a.w, h: 2.45, heading: "Extracted by SAFE" });
s.addText(
  [
    { text: "There is a demand for gold as jewelry.", options: { bullet: true, breakLine: true } },
    { text: "The price of gold could drop by 20–50% or more.", options: { bullet: true, breakLine: true } },
    { text: "condition dropped", options: { color: ACCENT, bold: true, breakLine: true, fontSize: 10.5 } },
    { text: "Copper and silver are competitive with gold in price.", options: { bullet: true, breakLine: true } },
    { text: "stated unconditionally; the causal link in “making” is never extracted", options: { color: ACCENT, bold: true, fontSize: 10.5 } },
  ],
  { isTextBox: true, objectName: "safe-list", x: c2a.x + 0.28, y: 3.26, w: c2a.w - 0.56, h: 1.82, fontSize: 12.5, color: BODY, fontFace: "Arial", paraSpaceAfter: 4, margin: 0 }
);
card(s, { name: "vf", x: c2b.x, y: 2.75, w: c2b.w, h: 2.45, accent: true, heading: "Extracted by VeriFact" });
s.addText(
  [
    { text: "There is a demand for gold as jewelry.", options: { bullet: true, breakLine: true } },
    { text: "If the demand for gold as jewelry disappeared, the price of gold could drop by 20–50% or more.", options: { bullet: true, breakLine: true } },
    { text: "A 20–50% drop in the price of gold could make copper and silver competitive with gold.", options: { bullet: true, breakLine: true } },
    { text: "condition preserved, causal relation recovered as its own fact", options: { color: ACCENT, bold: true, fontSize: 10.5 } },
  ],
  { isTextBox: true, objectName: "vf-list", x: c2b.x + 0.28, y: 3.26, w: c2b.w - 0.56, h: 1.82, fontSize: 12.5, color: BODY, fontFace: "Arial", paraSpaceAfter: 4, margin: 0 }
);
[
  ["Incomplete facts in SAFE", "12.68%", "451 facts, human-annotated"],
  ["Missing facts per response", "1.24", "relations never extracted"],
  ["Of those, omitted conditions", "51%", "the gold case above"],
].forEach(([l, v, f], i) => {
  const c = col(i, 3);
  stat(s, { name: "p" + i, x: c.x, y: 5.45, w: c.w, label: l, value: v, foot: f, valueSize: 24 });
});
note(s, "VeriFact: Liu, Zhang, Munir, Gu & Wang, EMNLP 2025, pp. 17908–17925  ·  github.com/launchnlp/VeriFact");
s.addNotes(
  "[1:15] This example is the whole paper. Verifying the stripped claim gives a meaningless verdict, because it is not what the answer said. Read the two fact lists side by side, then point at the three numbers: measured on human annotation, not anecdote."
);

/* 3 — the solution  [0:45] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "The solution");
title(s, "VeriFact — repair the facts before verifying them");
subtitle(s, "Preserving context instead of accepting what decomposition left behind");
[
  [
    "What VeriFact is",
    "A factuality framework that inserts two steps between decomposition and verification: detect broken facts, then repair them. The extractor and the verifier are inherited unchanged.",
  ],
  [
    "The two defects it targets",
    "Incomplete facts — an ambiguous reference, a dropped condition, a missing comparison target. And missing facts — an inter-sentence temporal or causal relation that no atomic fact carries.",
  ],
  [
    "The trade it makes",
    "Detection recalls 0.89 of incomplete and 0.85 of missing facts. One LLM agrees with human annotators at only κ = 0.33, so detections are unioned, not voted, and refinement absorbs the false positives.",
  ],
].forEach(([h, b], i) => {
  const c = col(i, 3);
  card(s, { name: "sol" + i, x: c.x, y: TOP, w: c.w, h: 2.35, heading: h, body: b });
});
s.addText("What the paper reports on FACTRBENCH", {
  isTextBox: true,
  objectName: "pr-h",
  x: M,
  y: 4.35,
  w: W,
  h: 0.3,
  fontSize: 12.5,
  bold: true,
  color: INK,
  fontFace: "Arial",
  margin: 0,
});
[
  ["Incomplete facts", "56.7% → 22.5%", "SAFE, after refinement", false],
  ["Missing facts / response", "1.22 → 0.76", "−37%", false],
  ["Verdict changes", "24.9%", "supported ↓, contradicted ↑", true],
  ["Best F1 reported", "57.5", "Qwen 2.5-32B", false],
].forEach(([l, v, f, e], i) => {
  const c = col(i, 4);
  stat(s, { name: "pr" + i, x: c.x, y: 4.78, w: c.w, label: l, value: v, foot: f, emph: e, valueSize: 20 });
});
note(s, "These are the paper's numbers, on 1,096 prompts with GPT-4o, Llama 3.3-70B and Qwen 2.5-32B. We do not attempt to match them.");
s.addNotes(
  "[0:45] Three sentences on what the framework is, then the bottom strip: this is what the paper claims. Say explicitly that the bottom row is the paper's, not ours — the rest of the talk is about which of these behaviours survive at this scale."
);

/* 4 — how it works  [1:15] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "How VeriFact works");
title(s, "Four steps, three judges, union of detections");
subtitle(s, "Steps 2 and 3 are the paper's contribution; steps 1 and 4 are inherited");
[
  ["1", "Decompose", "SAFE's extractor splits each sentence into atomic facts, then resolves vague references.", false],
  ["2", "Detect", "Judges flag incomplete facts by subtype, and missing temporal or contingency relations.", true],
  ["3", "Refine", "Self-reflection rewrites each flagged fact and writes one new fact per missing relation.", true],
  ["4", "Verify", "Google Search via Serper, cross-encoder reranking, then Supported / Contradicted / Undecided.", false],
].forEach(([n, h, b, accent], i) => {
  const c = col(i, 4);
  card(s, { name: "step" + n, x: c.x, y: TOP, w: c.w, h: 2.3, badge: n, heading: h, body: b, accent, bodySize: 12 });
});
const c4a = col(0, 2);
const c4b = col(1, 2);
card(s, {
  name: "detect",
  x: c4a.x,
  y: 4.35,
  w: c4a.w,
  h: 1.95,
  panel: true,
  heading: "Detecting incomplete facts",
  body:
    "Each fact is judged against the response it came from, and labelled with one of four subtypes: ambiguous concept or pronoun, missing comparison, omitted condition or source, other.",
});
card(s, {
  name: "relate",
  x: c4b.x,
  y: 4.35,
  w: c4b.w,
  h: 1.95,
  panel: true,
  accent: true,
  heading: "Detecting missing relations",
  body:
    "Word mapping marks every response character covered by some fact. Each uncovered span is then asked two questions: does it express a temporal or contingency relation, and is it already captured by a single existing fact?",
});
note(s, "The three detection judges are GPT-4o + Llama 3.3-70B + Qwen 2.5-32B — not the 12 models the paper separately benchmarks.");
s.addNotes(
  "[1:15] Walk the four boxes left to right in about thirty seconds. Spend the rest on the two bottom cards: these are the two mechanisms we reimplemented. The union rule matters later — we test whether it is the right choice."
);

/* 5 — recreating 1/5: setting up  [0:55] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Recreating the results  ·  1 of 5");
title(s, "Setting up the experiment");
subtitle(s, "Every remote or paid component replaced by a local one");
table(s, {
  name: "map",
  x: M,
  y: TOP,
  w: W,
  colW: [3.3, 4.4, 4.4],
  rowH: 0.4,
  fontSize: 12.5,
  align: "left",
  head: ["Component", "Paper", "VERIFACT-Lite"],
  rows: [
    ["Judges", "GPT-4o + Llama 3.3-70B + Qwen 2.5-32B", "Qwen2.5-3B + Llama-3.2-3B, and 7–8B"],
    ["Extract / refine / verify", "Llama 3.3-70B-Instruct", "Qwen2.5-3B, and Qwen2.5-7B"],
    ["Evidence source", "Google Search via Serper (paid)", "Wikipedia API, cached for replay"],
    ["Evidence ranking", "cross-encoder reranker", "BM25 over retrieved paragraphs"],
    ["Benchmark", "FACTRBENCH, 1,096 prompts", "mini benchmark, 12 prompts"],
    ["Reference facts", "4 frontier LLMs + human answers", "86 facts, written and verified by hand"],
    ["Serving", "vLLM, multi-GPU", "Ollama on a 4 GB GTX 1650 and a Colab T4"],
  ],
});
[
  ["Questions", "12", "written for the failure modes", false],
  ["Reference facts", "86", "hand-written, sources recorded", false],
  ["Unit tests", "59", "detection, mapping and scoring", false],
  ["Total cost", "$0", "4 GB laptop GPU and a Colab T4", true],
].forEach(([l, v, f, e], i) => {
  const c = col(i, 4);
  stat(s, { name: "sc" + i, x: c.x, y: 5.1, w: c.w, label: l, value: v, foot: f, emph: e, valueSize: 24 });
});
note(s, "Reference facts are written from authoritative sources and deliberately not derived from the answer being evaluated. All model names live in config.yaml; none is hard-coded.");
s.addNotes(
  "[0:55] Do not read the table. Say: every paid or large component has a local stand-in, and the detection logic itself is unchanged. Then the bottom strip — twelve questions written to contain conditions, comparisons and event order, and an answer key written by hand before any run."
);

/* 6 — recreating 2/5: the baseline  [0:50] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Recreating the results  ·  2 of 5");
title(s, "Generating the baseline");
subtitle(s, "One answer set, scored two ways, so only refinement differs");
s.addShape(pres.ShapeType.roundRect, {
  objectName: "gen-box",
  x: 2.6,
  y: TOP,
  w: 8.1,
  h: 0.5,
  rectRadius: 0.25,
  fill: { color: WHITE },
  line: { color: ACCENT, width: 1 },
});
s.addText("Question → local LLM generates the answer ONCE → reused by every run", {
  isTextBox: true,
  objectName: "gen-text",
  x: 2.6,
  y: TOP,
  w: 8.1,
  h: 0.5,
  fontSize: 13,
  bold: true,
  color: ACCENT,
  align: "center",
  valign: "middle",
  fontFace: "Arial",
  margin: 0,
});
const c6a = col(0, 2);
const c6b = col(1, 2);
card(s, {
  name: "base",
  x: c6a.x,
  y: 2.5,
  w: c6a.w,
  h: 1.5,
  heading: "Baseline — variant A",
  body: "SAFE-style extraction  →  retrieval and verification",
  bodySize: 13,
});
card(s, {
  name: "vfl",
  x: c6b.x,
  y: 2.5,
  w: c6b.w,
  h: 1.5,
  accent: true,
  heading: "VERIFACT-Lite — variant D",
  body: "The same facts  →  detect  →  refine and add  →  the same retrieval and verification",
  bodySize: 13,
});
[
  ["Precision", "Supported facts ÷ all extracted facts. Undecided is reported separately and never counted as support."],
  ["Recall", "Reference facts entailed by the answer ÷ all 86 reference facts. It scores the answer, so refinement cannot move it."],
  ["Incomplete rate", "Measured by one designated judge while refinement is driven by the ensemble — facts are never scored by the rule that selected them."],
].forEach(([h, b], i) => {
  const c = col(i, 3);
  card(s, { name: "met" + i, x: c.x, y: 4.2, w: c.w, h: 2.1, panel: true, heading: h, body: b, bodySize: 12 });
});
note(s, "Verification is grounded: a SUPPORTED or CONTRADICTED verdict without a verbatim quote from the evidence is downgraded to UNDECIDED.");
s.addNotes(
  "[0:50] The key methodological point: the answer is generated once, so baseline and VERIFACT-Lite differ only in whether refinement runs. Read the recall definition out loud — it explains why recall never moves between variants."
);

/* 7 — recreating 3/5: headline results  [1:30] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Recreating the results  ·  3 of 5");
title(s, "Extraction improves. Precision falls.");
subtitle(s, "Baseline against VERIFACT-Lite, laptop run, Qwen2.5-3B judges");
[
  ["Incomplete fact rate", "0.105 → 0.091", "−12.8%", false],
  ["Missing relational facts", "51 → 0", "all recovered", false],
  ["Precision", "0.420 → 0.343", "−0.077", true],
  ["Recall · F1", "0.408 · 0.372", "recall fixed by design", false],
].forEach(([l, v, f, e], i) => {
  const c = col(i, 4);
  stat(s, { name: "h" + i, x: c.x, y: TOP, w: c.w, label: l, value: v, foot: f, emph: e, valueSize: 19 });
});
const c7a = col(0, 2);
const c7b = col(1, 2);
s.addChart(
  pres.ChartType.bar,
  [
    { name: "Baseline", labels: ["Precision", "Recall", "F1"], values: [0.42, 0.4077, 0.4138] },
    { name: "VERIFACT-Lite", labels: ["Precision", "Recall", "F1"], values: [0.3426, 0.4077, 0.3723] },
  ],
  Object.assign({}, CHART_BASE, {
    objectName: "chart-prf",
    x: c7a.x - 0.28,
    y: 3.35,
    w: c7a.w + 0.28,
    h: 3.1,
    barDir: "col",
    barGapWidthPct: 60,
    chartColors: ["B4B4B4", ACCENT],
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.000",
    valAxisMinVal: 0,
    valAxisMaxVal: 0.55,
  })
);
card(s, {
  name: "where",
  x: c7b.x,
  y: 3.35,
  w: c7b.w,
  h: 3.1,
  panel: true,
  accent: true,
  heading: "Where the precision went",
  body:
    "Supported 109 → 108.  Contradicted 3 → 3.  Undecided 146 → 185.\n\nRefined claims carry their condition or comparison target, so one Wikipedia sentence has to support more — and often none does.\n\nOf the claims the verifier could decide, 97.3% were supported both before and after.",
  bodySize: 12.5,
});
note(s, "Same answers, same retrieval, same verifier — only refinement differs. 163 facts refined, 51 added.");
s.addNotes(
  "[1:30] The main reproduction slide. The mechanism does what the paper says to the fact set, and measured precision goes down. Flag that contradicted did not move at all — that becomes the tell two slides from now."
);

/* 8 — recreating 4/5: ablation  [0:45] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Recreating the results  ·  4 of 5");
title(s, "Each mechanism moves the metric it targets");
subtitle(s, "Ablation over the two halves of the contribution, laptop run");
table(s, {
  name: "abl",
  x: M,
  y: TOP,
  w: W,
  colW: [3.7, 1.9, 1.6, 1.7, 1.6, 1.6],
  rowH: 0.46,
  fontSize: 12.5,
  head: ["System", "Incomplete", "Missing", "Precision", "Recall", "F1"],
  rows: [
    ["A  Baseline", "0.105", "51", "0.4200", "0.4077", "0.4138"],
    ["B  + incomplete refine", "0.078", "51", "0.3680", "0.4077", "0.3868"],
    ["C  + missing relation", "0.113", "0", "0.3839", "0.4077", "0.3954"],
    ["D  Full VERIFACT-Lite", { text: "0.091", emph: true }, { text: "0", emph: true }, "0.3426", "0.4077", "0.3723"],
  ],
});
[
  ["B isolates the refiner", "Incomplete rate drops 0.105 → 0.078, the largest single gain, and precision falls with it."],
  ["C isolates relation recovery", "All 51 missing relations become facts. The incomplete rate ticks up because the new facts are judged too."],
  ["The effects are additive", "D inherits B's lower incomplete rate and C's zero missing relations — and both precision costs."],
].forEach(([h, b], i) => {
  const c = col(i, 3);
  card(s, { name: "abl" + i, x: c.x, y: 4.3, w: c.w, h: 1.95, panel: true, heading: h, headingSize: 13.5, body: b, bodySize: 12 });
});
note(s, "All four variants scored on one identical answer set, union ensemble, as in the paper.");
s.addNotes(
  "[0:45] Walk the table once, then read the three card headings only. Each half of the contribution moves its own metric, and the two compose."
);

/* 9 — recreating 5/5: verdict changes  [1:15] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Recreating the results  ·  5 of 5");
title(s, "Does fixing a claim change its verdict?");
subtitle(s, "The paper's research question, asked of our own pipeline");
card(s, { name: "big", x: M, y: TOP, w: 3.2, h: 2.1, panel: true });
s.addText("39–46%", {
  isTextBox: true,
  objectName: "big-v",
  x: M + 0.28,
  y: TOP + 0.42,
  w: 2.7,
  h: 0.8,
  fontSize: 38,
  bold: true,
  color: ACCENT,
  margin: 0,
});
s.addText("of refined facts changed label across all three runs", {
  isTextBox: true,
  objectName: "big-l",
  x: M + 0.28,
  y: TOP + 1.3,
  w: 2.7,
  h: 0.6,
  fontSize: 12.5,
  color: BODY,
  fontFace: "Arial",
  lineSpacingMultiple: 1.2,
  margin: 0,
});
table(s, {
  name: "trans",
  x: 4.1,
  y: TOP,
  w: 8.6,
  colW: [3.5, 1.2, 1.2, 2.7],
  rowH: 0.42,
  fontSize: 12,
  align: "left",
  head: ["Transition", "3B", "7–8B", "Meaning"],
  rows: [
    ["SUPPORTED → UNDECIDED", "37", "—", "was over-credited"],
    ["UNDECIDED → SUPPORTED", "29", "—", "context made it checkable"],
    ["Contradicted, before → after", "3 → 3", { text: "3 → 8", emph: true }, "errors finally surfaced"],
    ["Verdict-change rate", "39.3%", { text: "45.6%", emph: true }, "paper reports 24.9%"],
  ],
});
card(s, {
  name: "cmp-paper",
  x: M,
  y: 4.15,
  w: W,
  h: 2.15,
  panel: true,
  accent: true,
  heading: "The paper's full signature only appears with stronger judges",
  body:
    "The paper reports supported falling AND contradicted rising after refinement, concluding that ignoring incomplete facts overestimates factuality.\n\nWith 3B judges we reproduced only the first half: contradicted never moved off 3. With 7–8B judges it rises to 8 — refinement exposes errors that the stripped claims had hidden. Same conclusion as the paper, now with both halves of the evidence.",
  bodySize: 12.5,
});
note(s, "Every refined fact is verified twice, as its original claim and as its refined claim, through the same evidence pipeline.");
s.addNotes(
  "[1:15] This slide justifies the paper and explains the precision drop. A quarter to nearly half of verdicts are decided by whether the claim kept its context. Dwell on the contradicted row — it is the result we could not get until the judges were bigger, which is the next section."
);

/* 10 — contribution 1/3: scaling the judges  [1:00] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Our contribution  ·  1 of 3");
title(s, "Re-running the whole study with stronger judges");
subtitle(s, "Testing which conclusions were findings and which were small-model artifacts");
[
  [
    "One configuration proves little",
    "Everything above was measured by 3B judges. A single run cannot tell a property of the method from a property of the measuring model.",
  ],
  [
    "What a T4 makes possible",
    "A Colab T4 holds 7–8B judges at Q4_K_M. The repository is config-driven, so re-running the entire study needed nothing but two model identifiers.",
  ],
  [
    "What makes run A controlled",
    "Extraction replays from cache, so A's baseline fact set is byte-identical to the laptop's: 21.50 facts per answer, precision 0.4200. Only the judges changed.",
  ],
].forEach(([h, b], i) => {
  const c = col(i, 3);
  card(s, { name: "sc" + i, x: c.x, y: TOP, w: c.w, h: 2.0, heading: h, body: b, bodySize: 12 });
});
table(s, {
  name: "configs",
  x: M,
  y: 3.95,
  w: W,
  colW: [2.4, 3.1, 3.4, 1.9, 1.3],
  rowH: 0.44,
  fontSize: 12,
  align: "left",
  head: ["Run", "Primary model", "Judges", "Hardware", "Controlled"],
  rows: [
    ["laptop-3B", "Qwen2.5-3B", "Qwen2.5-3B + Llama-3.2-3B", "GTX 1650, 4 GB", "reference"],
    ["judges-7B  (A)", "Qwen2.5-3B (unchanged)", "Qwen2.5-7B + Llama-3.1-8B", "Colab T4, 16 GB", { text: "yes", emph: true }],
    ["full-7B  (B)", "Qwen2.5-7B", "Qwen2.5-7B + Llama-3.1-8B", "Colab T4, 16 GB", "no"],
  ],
});
card(s, {
  name: "bnote",
  x: M,
  y: 5.85,
  w: W,
  h: 0.7,
  panel: true,
  body:
    "Run B changed the extractor, the incompleteness judge, the verifier and the recall entailment model at once, so its columns are read only against its own baseline — never against A's.",
  bodySize: 12,
});
note(s, "Same 12 questions, same 12 generated answers, verified identical by hash across all three runs.");
s.addNotes(
  "[1:00] Frame this as the contribution: the paper ran one configuration, we ran three and asked which results were real. Be explicit that A is the controlled comparison and B is not — that distinction is why the next two slides can say anything at all."
);

/* 11 — contribution 2/3: the judge is the instrument  [1:30] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Our contribution  ·  2 of 3");
title(s, "The metrics measure the judge as much as the system");
subtitle(s, "Identical input, identical pipeline, one model swapped");
table(s, {
  name: "instrument",
  x: M,
  y: TOP,
  w: W,
  colW: [5.3, 2.3, 2.3, 2.2],
  rowH: 0.46,
  fontSize: 12.5,
  align: "left",
  head: ["Measured on identical input", "3B judge", "7B judge", "Paper"],
  rows: [
    ["Incomplete rate — the same baseline facts", "0.105", { text: "0.438", emph: true }, "0.567"],
    ["Recall — the same answers, same 86 reference facts", "0.4077", { text: "0.2812", emph: true }, "—"],
    ["Coverage behind that recall", "35 / 86", { text: "24 / 86", emph: true }, "—"],
  ],
});
const c11 = col(0, 5, 3);
card(s, {
  name: "insight",
  x: c11.x,
  y: 3.9,
  w: c11.w,
  h: 1.75,
  panel: true,
  accent: true,
  heading: "Nothing about the system changed in these rows",
  body:
    "Same 12 answers, same extracted facts, same reference facts, same lexical gate. Only the model doing the judging changed. A stronger judge finds four times as many incomplete facts and credits the answer with a third fewer reference facts.",
  bodySize: 12.5,
});
stat(s, { name: "i1", x: col(3, 5).x, y: 3.9, w: col(3, 5).w, label: "Incomplete", value: "4.2×", foot: "more found", emph: true, valueSize: 28 });
stat(s, { name: "i2", x: col(4, 5).x, y: 3.9, w: col(4, 5).w, label: "Recall", value: "−31%", foot: "same answers", emph: true, valueSize: 28 });
card(s, {
  name: "consequence",
  x: M,
  y: 5.8,
  w: W,
  h: 0.75,
  panel: true,
  body:
    "Our baseline looked cleaner than SAFE's 56.7% because our judge was weaker, not because our extractor was better. With a 7B judge the figure moves to 0.438 — two thirds of the way to the paper's.",
  bodySize: 12.5,
});
note(s, "Run A on a Colab T4: judges upgraded to Qwen2.5-7B + Llama-3.1-8B, everything else replayed from cache.");
s.addNotes(
  "[1:30] The strongest finding of the project, and it is a methodological one. Any factuality score of this kind is a property of the judge as much as of the system under test. Say plainly: this is why we do not compare our absolute numbers with the paper's."
);

/* 12 — contribution 3/3: union vs majority  [1:15] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Our contribution  ·  3 of 3");
title(s, "One finding held, one was a small-model artifact");
subtitle(s, "Testing the paper's union rule against a majority vote, at every model size");
const c12a = col(0, 2);
const c12b = col(1, 2);
table(s, {
  name: "rules",
  x: c12a.x,
  y: TOP,
  w: c12a.w,
  colW: [1.4, 1.15, 1.3, 1.15, 0.9],
  rowH: 0.4,
  fontSize: 11.5,
  head: ["Run", "Rule", "Incomplete", "Precision", "F1"],
  rows: [
    ["laptop-3B", "union", "0.091", "0.3426", "0.372"],
    ["laptop-3B", "majority", { text: "0.042", emph: true }, { text: "0.4071", emph: true }, "0.407"],
    ["judges-7B", "union", "0.411", "0.3018", "0.347"],
    ["judges-7B", "majority", "0.393", { text: "0.4106", emph: true }, "0.409"],
    ["full-7B", "union", "0.286", "0.4802", "0.355"],
    ["full-7B", "majority", "0.287", { text: "0.4985", emph: true }, "0.360"],
  ],
});
card(s, {
  name: "held",
  x: c12b.x,
  y: TOP,
  w: c12b.w,
  h: 1.3,
  accent: true,
  heading: "Held — majority beats union on precision",
  headingSize: 13.5,
  body: "In all three configurations, at every model size. The paper's recall-first union rule costs precision it does not need to.",
  bodySize: 12,
});
card(s, {
  name: "broke",
  x: c12b.x,
  y: 3.2,
  w: c12b.w,
  h: 1.3,
  heading: "Broke — the 60% incomplete-rate gap",
  headingSize: 13.5,
  body: "A 3B artifact. With 7–8B judges the two rules are within 4% (0.393 vs 0.411); with a 7B extractor they are identical.",
  bodySize: 12,
});
table(s, {
  name: "judges",
  x: M,
  y: 4.85,
  w: W,
  colW: [3.1, 2.3, 2.3, 2.2, 2.2],
  rowH: 0.34,
  fontSize: 11.5,
  align: "left",
  head: ["Facts flagged", "Qwen", "Llama", "Ensemble", "Reading"],
  rows: [
    ["3B — incompleteness", "20", "34", "34", "ensemble = Llama"],
    ["7–8B — incompleteness", "32", "27", { text: "33", emph: true }, "exceeds both judges"],
    ["3B — relations", "2", "51", "51", "ensemble = Llama"],
    ["7–8B — relations", "15", "54", "54", "ensemble = Llama"],
  ],
});
note(s, "Relation detection: the ensemble equalled Llama exactly in all three runs — 51/51, 54/54, 21/21. Qwen never found a relation Llama missed.");
s.addNotes(
  "[1:15] Two claims, opposite fates. Majority beating union survives everywhere. The dramatic incomplete-rate gap was a 3B artifact and we say so. Then the bottom table: for relations the union really is one judge's opinion at every size, but for incompleteness bigger judges finally complement each other — 33 exceeds both 32 and 27, which is the behaviour the union rule assumes."
);

/* 13 — comparison with the paper  [0:55] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Comparison with the paper");
title(s, "Directions match. Magnitudes do not.");
subtitle(s, "What a small-scale reimplementation can and cannot claim");
table(s, {
  name: "vs",
  x: M,
  y: TOP,
  w: W,
  colW: [3.3, 3.0, 3.9, 1.9],
  rowH: 0.36,
  fontSize: 11.5,
  align: "left",
  head: ["Measure", "Paper", "VERIFACT-Lite", "Agreement"],
  rows: [
    ["Incomplete facts, baseline", "56.7% (SAFE)", "10.5% at 3B · 43.8% at 7B", "closes with scale"],
    ["Incomplete facts, refined", "22.5%  (−19.2 pts)", "9.1% at 3B · 41.1% at 7B", "same direction"],
    ["Missing relational facts", "1.22 → 0.76 (−37%)", "51 → 0 (−100%)", "same direction"],
    ["Refined facts changing label", "24.9%", { text: "39.3% · 45.6% · 34.7%", emph: true }, "same phenomenon"],
    ["Direction of that change", "supported ↓, contradicted ↑", "both, once judges are 7–8B", { text: "reproduced", emph: true }],
    ["Precision", "82.8 (Qwen2.5-32B)", "30.2 – 49.9 across runs", "not comparable"],
    ["Recall", "44.1", "40.8 at 3B · 28.1 at 7B", "judge-dependent"],
    ["F1", "57.5", "34.7 – 40.9 across runs", "not comparable"],
  ],
});
[
  ["Reproduced", "Both problem types detected and repaired; verdicts change after refinement.", true],
  ["Not reproduced", "Absolute precision, recall and F1 — different models, different evidence, 12 prompts.", false],
  ["Now explained", "Our low baseline incomplete rate was the judge, not the extractor.", false],
].forEach(([h, b, a], i) => {
  const c = col(i, 3);
  card(s, { name: "vs" + i, x: c.x, y: 5.35, w: c.w, h: 1.2, panel: true, accent: a, heading: h, headingSize: 13.5, body: b, bodySize: 11.5 });
});
note(s, "Every VERIFACT-Lite value is measured by this repository; none is copied from the paper or estimated.");
s.addNotes(
  "[0:55] Point at the Agreement column, not the numbers. The claim is that the mechanism behaves as described; the claim is explicitly not that the numbers match."
);

/* 14 — future plans  [0:55] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Future plans & next steps");
title(s, "Every limitation points at a next step");
subtitle(s, "Two were tested; the rest are proposals, labelled as such");
card(s, {
  name: "rubber",
  x: M,
  y: TOP,
  w: W,
  h: 1.3,
  panel: true,
  accent: true,
  heading: "Found by breaking our own result: a 3B verifier rubber-stamps unless forced to quote",
  headingSize: 13.5,
  body:
    "An earlier version reported precision 0.92 and zero contradictions across 258 facts, calling “Aluminium is the rarest metal in the Earth's crust” SUPPORTED with confidence 1.0. Requiring a verbatim quote from the evidence moved precision to 0.42 and made contradictions appear.",
  bodySize: 12,
});
table(s, {
  name: "fixes",
  x: M,
  y: 3.3,
  w: W,
  colW: [4.6, 4.5, 3.0],
  rowH: 0.44,
  fontSize: 12,
  align: "left",
  head: ["Limitation", "What would fix it", "Status"],
  rows: [
    ["Judges are 3B; metrics track the judge", "Stronger local judge (7–14B)", { text: "tested — 4.2× more found", emph: true }],
    ["Union is dominated by the permissive judge", "Majority vote, or a third judge", { text: "tested — majority wins", emph: true }],
    ["Undecided dominates — 146 of 258 verdicts", "Dense retrieval, query expansion, reranking", "not yet run"],
    ["Refined facts are sometimes still flagged", "Iterative refinement, maximum two passes", "not yet run"],
    ["12 questions, 86 facts, no human annotation", "Larger benchmark, human-verified references", "not yet run"],
    ["Recall is itself judge-dependent (0.41 vs 0.28)", "Fixed entailment model across all runs", "not yet run"],
  ],
});
note(s, "Full ranked list in the appendix. Nothing in the 'not yet run' rows is claimed as a result.");
s.addNotes(
  "[0:55] Open by owning the 0.92 mistake — it shows the harness was itself tested. Then the table: the top two rows started as proposals on the first version of this talk and are now experiments with results. The rest are still proposals, and are labelled as such."
);

/* 15 — takeaways  [0:40] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Takeaways");
title(s, "Four things this reimplementation establishes");
subtitle(s, "Measured by the repository, on 12 questions and three model configurations");
[
  ["1", "The whole VeriFact pipeline runs on a 4 GB consumer GPU with quantized 3B models and Wikipedia evidence, and scales to 7–8B on a Colab T4."],
  ["2", "Refinement changed the verdict on 39–46% of refined facts across three model configurations, against 24.9% in the paper. The phenomenon is robust to model size."],
  ["3", "These metrics measure the judge as much as the system: identical facts score 0.105 incomplete at 3B and 0.438 at 7B; identical answers score 0.41 recall at 3B and 0.28 at 7B."],
  ["4", "Majority vote beat the paper's union rule on precision in every configuration — but the large incomplete-rate advantage we first reported was a 3B artifact, and we say so."],
].forEach(([n, t], i) => {
  const y = 1.92 + i * 1.24;
  const last = i === 3;
  s.addShape(pres.ShapeType.rect, {
    objectName: "tk-rule" + n,
    x: M,
    y,
    w: W,
    h: 0.018,
    fill: { color: last ? ACCENT : HAIR },
    line: { color: last ? ACCENT : HAIR, width: 0.25 },
  });
  s.addText(n, {
    isTextBox: true,
    objectName: "tk-n" + n,
    x: M,
    y: y + 0.2,
    w: 0.5,
    h: 0.5,
    fontSize: 20,
    bold: true,
    color: last ? ACCENT : MUTED,
    margin: 0,
  });
  s.addText(t, {
    isTextBox: true,
    objectName: "tk-t" + n,
    x: M + 0.75,
    y: y + 0.2,
    w: W - 0.75,
    h: 0.78,
    fontSize: 13,
    color: BODY,
    fontFace: "Arial",
    lineSpacingMultiple: 1.2,
    valign: "top",
    margin: 0,
  });
});
note(s, "Config-driven, fully cached, 59 unit tests  ·  all three runs reproduce from one command without a GPU");
s.addNotes(
  "[0:40] Close on points 3 and 4. Point 3 is the finding that generalises beyond this paper. Point 4 is where we corrected ourselves between versions of this talk, which is the honest thing to show. Leave the slide up for the questions."
);

/* --------------------------------------------------------------- backup
 * One slide, not presented. It answers the four questions the talk
 * invites; the detail behind it is in README.md and colab/RESULTS.md.
 * ---------------------------------------------------------------------- */

pres.addSection({ title: "Backup" });

/* 16 — backup for the question period */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Backup" });
eyebrow(s, "Backup — not presented");
title(s, "Detail behind the four most likely questions");
subtitle(s, "Word mapping, the uncontrolled run, what the refiner writes, and the engineering hazards");
const cK1 = col(0, 2);
const cK2 = col(1, 2);
card(s, {
  name: "bk-wm",
  x: cK1.x,
  y: TOP,
  w: cK1.w,
  h: 2.3,
  heading: "How missing relations are found — Algorithm 1",
  headingSize: 13.5,
  body: [
    "Take each fact's longest common substring with the response, mark those characters covered, collect the runs that stayed uncovered, and send them to the judges. Normalization is index-preserving, so offsets still point into the original answer.",
    "Coverage 0.55–0.59.  73 candidate spans.  A fact is added only when the span expresses a temporal or contingency relation AND no single existing fact already captures it.",
  ].join("\n"),
  bodySize: 10.5,
});
card(s, {
  name: "bk-b",
  x: cK2.x,
  y: TOP,
  w: cK2.w,
  h: 2.3,
  panel: true,
  heading: "Run B — the whole pipeline at 7B, extractor included",
  headingSize: 13.5,
  body: [
    "Baseline 15.92 facts per answer against 21.50, incomplete rate 0.319, precision 0.5050. Refinement then costs −0.025 precision, against −0.118 in run A.",
    "A stronger extractor writes fewer, coarser, self-contained facts, so there is less to repair — the trade the paper notes for VERIFY (18.5 facts per response against VeriFact's 32.3).",
    "B changed four things at once, so it reads only against its own baseline.",
  ].join("\n"),
  bodySize: 10.5,
});
card(s, {
  name: "bk-q",
  x: cK1.x,
  y: 4.25,
  w: cK1.w,
  h: 2.3,
  panel: true,
  accent: true,
  heading: "What the 3B refiner actually writes",
  headingSize: 13.5,
  body: [
    "Works — Q10:  “These substances are in the atmosphere.” becomes “… since the Montreal Protocol was signed.”   UNDECIDED → SUPPORTED.",
    "Fails — Q01:  “There was demand for gold as jewelry.” becomes “There was NO demand …”. The hypothetical from the question was pasted into a fact stating the opposite.",
    "Added relation — Q04:  “The experiment just before the explosion caused the reactor to exceed its design limits …”",
  ].join("\n"),
  bodySize: 10.5,
});
card(s, {
  name: "bk-haz",
  x: cK2.x,
  y: 4.25,
  w: cK2.w,
  h: 2.3,
  heading: "Engineering hazards behind these numbers",
  headingSize: 13.5,
  body: [
    "GPU:  two 3B Q4_K_M judges do not fit in 4 GB, so the pipeline drives one judge over the whole fact list, then releases its weights — otherwise every call pays a ~20 s model load.",
    "Retrieval:  Wikipedia rate-limits unauthenticated clients and failures are not cached, so without retries a 429 silently becomes “no evidence”. Fixed with retries and backoff.",
    "Replay:  every LLM call is cached under hash(model + prompt + parameters).",
  ].join("\n"),
  bodySize: 10.5,
});
note(s, "Full write-up in README.md and colab/RESULTS.md. All three runs reproduce from one command with no GPU.");
s.addNotes("Backup. Not part of the 15 minutes.");

/* ------------------------------------------------------------------ write */

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote " + OUT);
})();
