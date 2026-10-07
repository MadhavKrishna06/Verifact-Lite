/**
 * VERIFACT-Lite presentation, Texas Tech University visual identity.
 *
 * Palette and typefaces follow TTU's published web brand guidance:
 *   Scarlet #E90802, Black #000000, White #FFFFFF,
 *   Light Gray #EDEDED, Dark Gray #333333, Medium Gray #757575.
 *   Neue Plak (primary, not licensed here) -> Tahoma, TTU's listed tertiary face,
 *   with Arial for body text.
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

const THEME = {
  name: "Texas Tech",
  headFontFace: "Tahoma",
  bodyFontFace: "Arial",
  colors: {
    dk1: "000000", // black
    lt1: "FFFFFF", // white
    dk2: "333333", // dark gray
    lt2: "EDEDED", // light gray
    accent1: "E90802", // TTU scarlet
    accent2: "757575", // medium gray
    accent3: "333333",
    accent4: "EDEDED",
    accent5: "000000",
    accent6: "E90802",
    hlink: "E90802",
    folHlink: "757575",
  },
};

const SCARLET = "E90802";
const BLACK = "000000";
const WHITE = "FFFFFF";
const DGRAY = "333333";
const MGRAY = "757575";
const LGRAY = "EDEDED";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.author = "VERIFACT-Lite";
pres.company = "Texas Tech University";
pres.title = "VERIFACT-Lite";
pres.subject = "Reimplementation of VeriFact (EMNLP 2025)";

const C = pres.SchemeColor;

/* ---------------------------------------------------------------- layouts */

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: BLACK },
});

pres.defineSlideMaster({
  title: "SECTION",
  background: { color: SCARLET },
});

pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: WHITE },
  slideNumber: { x: 12.5, y: 6.82, w: 0.5, h: 0.32, fontSize: 10, color: MGRAY, align: "right" },
});

pres.defineSlideMaster({
  title: "CONTENT_DARK",
  background: { color: BLACK },
  slideNumber: { x: 12.5, y: 6.82, w: 0.5, h: 0.32, fontSize: 10, color: MGRAY, align: "right" },
});

/* ---------------------------------------------------------------- helpers */

/** Eyebrow label above a content title. */
function eyebrow(slide, text, dark) {
  slide.addText(text.toUpperCase(), {
    isTextBox: true,
    objectName: "eyebrow",
    x: 0.6,
    y: 0.14,
    w: 12.1,
    h: 0.28,
    fontSize: 11,
    bold: true,
    charSpacing: 2,
    color: dark ? SCARLET : SCARLET,
    fontFace: "Arial",
    margin: 0,
  });
}

/** Slide title, drawn directly (custom placeholders do not inherit styling). */
function title(slide, text, dark) {
  slide.addText(text, {
    isTextBox: true,
    objectName: "title",
    x: 0.6,
    y: 0.46,
    w: 12.1,
    h: 0.72,
    fontSize: 30,
    bold: true,
    color: dark ? WHITE : BLACK,
    valign: "middle",
    margin: 0,
  });
}

/** Footnote line along the bottom margin. */
function note(slide, text) {
  slide.addText(text, {
    isTextBox: true,
    objectName: "note",
    x: 0.6,
    y: 6.84,
    w: 11.6,
    h: 0.3,
    fontSize: 10,
    color: MGRAY,
    fontFace: "Arial",
    valign: "middle",
    margin: 0,
  });
}

/** Cover slide text blocks. */
function coverEyebrow(slide, text) {
  slide.addText(text.toUpperCase(), { isTextBox: true, objectName: "cover-eyebrow", x: 0.75, y: 1.5, w: 11.8, h: 0.34, fontSize: 13, bold: true, charSpacing: 2, color: SCARLET, fontFace: "Arial", margin: 0 });
}
function coverTitle(slide, text) {
  slide.addText(text, { isTextBox: true, objectName: "cover-title", x: 0.75, y: 1.95, w: 11.8, h: 1.35, fontSize: 54, bold: true, color: WHITE, margin: 0 });
}
function coverBody(slide, text) {
  slide.addText(text, { isTextBox: true, objectName: "cover-body", x: 0.75, y: 3.45, w: 9.9, h: 1.3, fontSize: 17, color: LGRAY, fontFace: "Arial", lineSpacingMultiple: 1.3, margin: 0 });
}
function sectionEyebrow(slide, text) {
  slide.addText(text.toUpperCase(), { isTextBox: true, objectName: "sec-eyebrow", x: 0.75, y: 2.9, w: 11.8, h: 0.34, fontSize: 13, bold: true, charSpacing: 2, color: WHITE, fontFace: "Arial", margin: 0 });
}
function sectionTitleText(slide, text) {
  slide.addText(text, { isTextBox: true, objectName: "sec-title", x: 0.75, y: 3.3, w: 11.8, h: 1.0, fontSize: 42, bold: true, color: WHITE, margin: 0 });
}

/** A bordered card with an optional scarlet numeral badge. */
function card(slide, o) {
  const fill = o.fill || WHITE;
  slide.addShape(pres.ShapeType.roundRect, {
    objectName: o.name,
    x: o.x,
    y: o.y,
    w: o.w,
    h: o.h,
    rectRadius: 0.06,
    fill: { color: fill },
    line: { color: o.line || LGRAY, width: o.lineWidth || 1 },
  });
  let ty = o.y + 0.22;
  if (o.badge) {
    slide.addShape(pres.ShapeType.ellipse, {
      objectName: o.name + "-badge",
      x: o.x + 0.26,
      y: ty,
      w: 0.46,
      h: 0.46,
      fill: { color: o.badgeFill || SCARLET },
      line: { color: o.badgeFill || SCARLET, width: 1 },
    });
    slide.addText(o.badge, {
      isTextBox: true,
      objectName: o.name + "-badge-text",
      x: o.x + 0.26,
      y: ty,
      w: 0.46,
      h: 0.46,
      fontSize: 15,
      bold: true,
      color: WHITE,
      align: "center",
      valign: "middle",
      margin: 0,
    });
    ty += 0.62;
  }
  if (o.heading) {
    slide.addText(o.heading, {
      isTextBox: true,
      objectName: o.name + "-h",
      x: o.x + 0.26,
      y: ty,
      w: o.w - 0.52,
      h: 0.34,
      fontSize: o.headingSize || 15,
      bold: true,
      color: o.headingColor || (fill === BLACK ? WHITE : BLACK),
      margin: 0,
    });
    ty += 0.42;
  }
  if (o.body) {
    slide.addText(o.body, {
      isTextBox: true,
      objectName: o.name + "-b",
      x: o.x + 0.26,
      y: ty,
      w: o.w - 0.52,
      h: o.y + o.h - ty - 0.2,
      fontSize: o.bodySize || 13,
      color: o.bodyColor || (fill === BLACK ? LGRAY : DGRAY),
      fontFace: "Arial",
      lineSpacingMultiple: 1.2,
      margin: 0,
      valign: "top",
    });
  }
}

/** Big-number callout tile. */
function stat(slide, o) {
  slide.addShape(pres.ShapeType.roundRect, {
    objectName: o.name,
    x: o.x,
    y: o.y,
    w: o.w,
    h: o.h,
    rectRadius: 0.06,
    fill: { color: o.fill || LGRAY },
    line: { color: o.line || o.fill || LGRAY, width: 1 },
  });
  slide.addText(o.label.toUpperCase(), {
    isTextBox: true,
    objectName: o.name + "-l",
    x: o.x + 0.22,
    y: o.y + 0.18,
    w: o.w - 0.44,
    h: 0.26,
    fontSize: 10,
    bold: true,
    charSpacing: 1,
    color: o.labelColor || MGRAY,
    fontFace: "Arial",
    margin: 0,
  });
  slide.addText(o.value, {
    isTextBox: true,
    objectName: o.name + "-v",
    x: o.x + 0.22,
    y: o.y + 0.46,
    w: o.w - 0.44,
    h: 0.58,
    fontSize: o.valueSize || 30,
    bold: true,
    color: o.valueColor || BLACK,
    margin: 0,
  });
  if (o.foot) {
    slide.addText(o.foot, {
      isTextBox: true,
      objectName: o.name + "-f",
      x: o.x + 0.22,
      y: o.y + o.h - 0.42,
      w: o.w - 0.44,
      h: 0.3,
      fontSize: 11,
      bold: true,
      color: o.footColor || DGRAY,
      fontFace: "Arial",
      margin: 0,
    });
  }
}

/** Table with the TTU header band. */
function table(slide, o) {
  const head = o.head.map((h, i) => ({
    text: h,
    options: {
      bold: true,
      color: WHITE,
      fill: { color: BLACK },
      align: i === 0 ? "left" : o.align || "right",
      fontFace: "Arial",
    },
  }));
  const rows = [head].concat(
    o.rows.map((r, ri) =>
      r.map((cell, ci) => {
        const isObj = typeof cell === "object" && cell !== null;
        const text = isObj ? cell.text : cell;
        const emph = isObj && cell.emph;
        return {
          text: String(text),
          options: {
            color: emph ? SCARLET : DGRAY,
            bold: !!emph,
            fill: { color: ri % 2 === 1 ? LGRAY : WHITE },
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
    fontSize: o.fontSize || 12,
    border: { type: "solid", color: "DDDDDD", pt: 0.5 },
    valign: "middle",
    margin: [0.04, 0.1, 0.04, 0.1],
  });
}

const CHART_BASE = {
  showTitle: false,
  showLegend: true,
  legendPos: "b",
  legendFontFace: "+mn-lt",
  legendFontSize: 11,
  legendColor: DGRAY,
  catAxisLabelColor: DGRAY,
  catAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11,
  valAxisLabelColor: MGRAY,
  valAxisLabelFontFace: "+mn-lt",
  valAxisLabelFontSize: 10,
  valGridLine: { color: LGRAY, size: 1 },
  catGridLine: { style: "none" },
  dataLabelFontFace: "+mn-lt",
  dataLabelFontSize: 10,
  dataLabelColor: DGRAY,
};

/* ----------------------------------------------------------------- slides */

/* 1 — title */
pres.addSection({ title: "Context" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Context" });
coverEyebrow(s, "Paper reimplementation");
coverTitle(s, "VERIFACT-Lite");
coverBody(s, "A resource-constrained reimplementation of the core VeriFact methodology using open-source, locally hosted models");
[
  ["Qwen2.5-3B + Llama-3.2-3B", 0.75],
  ["Q4_K_M on one 4 GB GPU", 3.95],
  ["Wikipedia evidence", 6.75],
  ["$0 total cost", 9.1],
].forEach(([t, x], i) => {
  s.addShape(pres.ShapeType.roundRect, {
    objectName: "chip" + i,
    x,
    y: 5.25,
    w: t.length * 0.105 + 0.5,
    h: 0.46,
    rectRadius: 0.23,
    fill: { color: i === 3 ? SCARLET : DGRAY },
    line: { color: i === 3 ? SCARLET : DGRAY, width: 1 },
  });
  s.addText(t, {
    isTextBox: true,
    objectName: "chip-t" + i,
    x,
    y: 5.25,
    w: t.length * 0.105 + 0.5,
    h: 0.46,
    fontSize: 12,
    bold: true,
    color: WHITE,
    align: "center",
    valign: "middle",
    fontFace: "Arial",
    margin: 0,
  });
});
s.addText("Liu, Zhang, Munir, Gu & Wang — EMNLP 2025  ·  Not a reproduction of the paper's reported results", {
  isTextBox: true,
  objectName: "cover-foot",
  x: 0.75,
  y: 6.45,
  w: 11.8,
  h: 0.3,
  fontSize: 11,
  color: MGRAY,
  fontFace: "Arial",
  margin: 0,
});
s.addNotes(
  "One line of framing: we rebuilt the paper's mechanism on hardware that costs nothing to run, and measured it honestly against its own baseline. We did not reproduce the paper's numbers and never claim to."
);

/* 2 — the paper */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
eyebrow(s, "The source");
title(s, "VeriFact, EMNLP 2025", false);
card(s, {
  name: "c1",
  x: 0.6,
  y: 1.35,
  w: 6.0,
  h: 2.1,
  badge: "1",
  heading: "A fact-extraction repair stage",
  body:
    "Detects incomplete facts and missing relational facts inside an existing decompose-decontextualize-verify pipeline, then refines them before verification.",
});
card(s, {
  name: "c2",
  x: 6.95,
  y: 1.35,
  w: 5.75,
  h: 2.1,
  badge: "2",
  heading: "FactRBench",
  body:
    "1,096 real-world prompts with reference fact sets, so recall can be measured. Prior benchmarks scored precision only.",
});
stat(s, { name: "s1", x: 0.6, y: 3.75, w: 3.85, h: 1.45, label: "Fewer incomplete facts", value: "19.2%", foot: "vs best comparison method", valueColor: SCARLET });
stat(s, { name: "s2", x: 4.7, y: 3.75, w: 3.85, h: 1.45, label: "Fewer missing facts", value: "37%", foot: "1.22 → 0.76 per response", valueColor: SCARLET });
stat(s, { name: "s3", x: 8.8, y: 3.75, w: 3.9, h: 1.45, label: "Refined facts changing label", value: "24.9%", foot: "verdict depends on context", valueColor: SCARLET });
note(s, "Scope note: we reimplement contribution 1. Contribution 2 needs four frontier LLMs and human-written Reddit answers.");
s.addNotes(
  "Two contributions. We rebuild the first. The second needs 1,096 prompts annotated by four frontier models plus curated human answers, which is out of reach at zero cost."
);

/* 3 — the problem */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Context" });
eyebrow(s, "The problem");
title(s, "Atomic facts lose the context that makes them true", false);
s.addShape(pres.ShapeType.roundRect, {
  objectName: "quote-box",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  h: 1.0,
  rectRadius: 0.06,
  fill: { color: LGRAY },
  line: { color: LGRAY, width: 1 },
});
s.addText(
  [
    { text: "Model answer:  ", options: { bold: true, color: MGRAY, fontSize: 12 } },
    {
      text: '"If the demand for gold as jewelry were to disappear, the price of gold could drop by 20–50% or more, ',
      options: { color: BLACK, fontSize: 15 },
    },
    { text: "making", options: { color: SCARLET, bold: true, fontSize: 15 } },
    { text: ' it more competitive with other materials like copper and silver."', options: { color: BLACK, fontSize: 15 } },
  ],
  {
    isTextBox: true,
    objectName: "quote-text",
    x: 0.85,
    y: 1.42,
    w: 11.6,
    h: 0.78,
    fontFace: "Arial",
    lineSpacingMultiple: 1.15,
    margin: 0,
    valign: "middle",
  }
);
card(s, {
  name: "safe",
  x: 0.6,
  y: 2.55,
  w: 6.0,
  h: 3.0,
  heading: "Extracted by SAFE",
  headingColor: DGRAY,
  body: "",
});
s.addText(
  [
    { text: "There is a demand for gold as jewelry.", options: { bullet: true, breakLine: true } },
    { text: "The price of gold could drop by 20–50% or more.", options: { bullet: true, breakLine: true } },
    { text: "condition dropped", options: { color: SCARLET, bold: true, breakLine: true, fontSize: 11 } },
    { text: "Copper and silver are competitive with gold in price.", options: { bullet: true, breakLine: true } },
    { text: "stated unconditionally; the causal link in “making” is never extracted", options: { color: SCARLET, bold: true, fontSize: 11 } },
  ],
  {
    isTextBox: true,
    objectName: "safe-list",
    x: 0.86,
    y: 3.1,
    w: 5.5,
    h: 2.3,
    fontSize: 13,
    color: DGRAY,
    fontFace: "Arial",
    paraSpaceAfter: 5,
    margin: 0,
  }
);
card(s, {
  name: "vf",
  x: 6.95,
  y: 2.55,
  w: 5.75,
  h: 3.0,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "Extracted by VeriFact",
  headingColor: SCARLET,
  body: "",
});
s.addText(
  [
    { text: "There is a demand for gold as jewelry.", options: { bullet: true, breakLine: true } },
    { text: "If the demand for gold as jewelry disappeared, the price of gold could drop by 20–50% or more.", options: { bullet: true, breakLine: true } },
    { text: "A 20–50% drop in the price of gold could make copper and silver competitive with gold.", options: { bullet: true, breakLine: true } },
    { text: "condition preserved, causal relation recovered as its own fact", options: { color: SCARLET, bold: true, fontSize: 11 } },
  ],
  {
    isTextBox: true,
    objectName: "vf-list",
    x: 7.21,
    y: 3.1,
    w: 5.25,
    h: 2.3,
    fontSize: 13,
    color: DGRAY,
    fontFace: "Arial",
    paraSpaceAfter: 5,
    margin: 0,
  }
);
note(s, "Human annotation of 451 SAFE facts: 12.68% incomplete, 1.24 missing facts per response, 51% of them omitted conditions.");
s.addNotes(
  "This single example is the paper's whole thesis. Verifying the stripped claim gives a meaningless verdict, because it is not what the answer said."
);

/* 4 — section divider: methodology */
pres.addSection({ title: "Methodology" });
s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Methodology" });
sectionEyebrow(s, "Part one");
sectionTitleText(s, "Methodology");
s.addNotes("Four steps in the paper, and how each was rebuilt locally.");

/* 5 — paper method */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
eyebrow(s, "How the paper works");
title(s, "Four steps, three judges, union of detections", false);
const steps = [
  ["1", "Decompose", "SAFE's extractor splits each sentence into atomic facts, then resolves vague references.", LGRAY],
  ["2", "Detect", "Judges flag incomplete facts by subtype, and missing temporal or contingency relations.", SCARLET],
  ["3", "Refine", "Self-reflection rewrites each flagged fact and writes one new fact per missing relation.", SCARLET],
  ["4", "Verify", "Google Search via Serper, cross-encoder reranking, then Supported / Contradicted / Undecided.", LGRAY],
];
steps.forEach(([n, h, b, accent], i) => {
  card(s, {
    name: "step" + n,
    x: 0.6 + i * 3.08,
    y: 1.3,
    w: 2.88,
    h: 2.5,
    badge: n,
    badgeFill: accent === SCARLET ? SCARLET : MGRAY,
    heading: h,
    body: b,
    line: accent === SCARLET ? SCARLET : LGRAY,
    bodySize: 12,
  });
});
card(s, {
  name: "ensemble",
  x: 0.6,
  y: 4.1,
  w: 8.3,
  h: 2.4,
  fill: BLACK,
  line: BLACK,
  heading: "The detection ensemble",
  headingColor: SCARLET,
  body:
    "GPT-4o + Llama 3.3-70B + Qwen 2.5-32B. Positive detections are unioned, not voted: one LLM agrees with human annotators at only κ = 0.33, so the paper trades precision for recall and lets refinement absorb false positives.",
  bodyColor: LGRAY,
});
stat(s, { name: "r1", x: 9.25, y: 4.1, w: 1.65, h: 2.4, label: "Recall", value: "0.89", foot: "incomplete", fill: DGRAY, labelColor: LGRAY, valueColor: WHITE, footColor: LGRAY, valueSize: 26 });
stat(s, { name: "r2", x: 11.05, y: 4.1, w: 1.65, h: 2.4, label: "Recall", value: "0.85", foot: "missing", fill: DGRAY, labelColor: LGRAY, valueColor: WHITE, footColor: LGRAY, valueSize: 26 });
note(s, "These 3 judges are the detection ensemble — not the 12 models the paper separately benchmarks.");
s.addNotes("Common question: the twelve models in the paper's Table 3 are systems under evaluation. We reimplement the judges, not that benchmark.");

/* 6 — scope */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
eyebrow(s, "Scope");
title(s, "Reproduce the mechanism, not the scale", false);
card(s, { name: "in", x: 0.6, y: 1.3, w: 6.0, h: 3.6, heading: "In scope", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "Full four-step pipeline, end to end", options: { bullet: true, breakLine: true } },
    { text: "All four incompleteness subtypes", options: { bullet: true, breakLine: true } },
    { text: "Word mapping, from Algorithm 1", options: { bullet: true, breakLine: true } },
    { text: "PDTB temporal and contingency detection", options: { bullet: true, breakLine: true } },
    { text: "Multi-judge ensemble, union of positives", options: { bullet: true, breakLine: true } },
    { text: "Precision, recall and F1 on reference facts", options: { bullet: true, breakLine: true } },
    { text: "Ablation of each refinement mechanism", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "in-list", x: 0.86, y: 1.85, w: 5.5, h: 2.8, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 6, margin: 0 }
);
card(s, { name: "out", x: 6.95, y: 1.3, w: 5.75, h: 3.6, heading: "Out of scope", headingColor: MGRAY, body: "" });
s.addText(
  [
    { text: "GPT-4o, Llama 3.3-70B, Qwen 2.5-32B", options: { bullet: true, breakLine: true } },
    { text: "FactRBench, 1,096 prompts", options: { bullet: true, breakLine: true } },
    { text: "Benchmarking the 12 frontier models", options: { bullet: true, breakLine: true } },
    { text: "FactScore, FactCheck-GPT, VERIFY baselines", options: { bullet: true, breakLine: true } },
    { text: "Human annotation of extraction quality", options: { bullet: true, breakLine: true } },
    { text: "Any numeric result of the paper", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "out-list", x: 7.21, y: 1.85, w: 5.25, h: 2.8, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 6, margin: 0 }
);
[
  ["Hardware", "GTX 1650, 4 GB"],
  ["API keys", "None"],
  ["Total cost", "$0"],
  ["Unit tests", "59 passing"],
].forEach(([l, v], i) => {
  stat(s, { name: "sc" + i, x: 0.6 + i * 3.08, y: 5.15, w: 2.88, h: 1.3, label: l, value: v, valueSize: 22, valueColor: i === 2 ? SCARLET : BLACK });
});
s.addNotes("Say this plainly: nothing here claims the paper's numbers. It claims the mechanism was rebuilt and measured against its own baseline under identical conditions.");

/* 7 — component mapping */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
eyebrow(s, "Component substitutions");
title(s, "Every paid component replaced by a free local one", false);
table(s, {
  name: "map",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [3.3, 4.4, 4.4],
  rowH: 0.36,
  fontSize: 12,
  align: "left",
  head: ["Component", "Paper", "VERIFACT-Lite"],
  rows: [
    ["Judge 1", "GPT-4o (paid API)", "Qwen2.5-3B-Instruct, Q4_K_M"],
    ["Judge 2", "Llama 3.3-70B", "Llama-3.2-3B-Instruct, Q4_K_M"],
    ["Judge 3", "Qwen 2.5-32B", "not used — two judges"],
    ["Extract / refine / verify", "Llama 3.3-70B-Instruct", "Qwen2.5-3B-Instruct"],
    ["Detection rule", "union of 3 judges", "union of 2 judges; majority also run"],
    ["Evidence source", "Google Search via Serper", "Wikipedia API, cached for replay"],
    ["Evidence ranking", "cross-encoder reranker", "BM25 over retrieved paragraphs"],
    ["Benchmark", "FactRBench, 1,096 prompts", "mini benchmark, 12 prompts"],
    ["Reference facts", "4 frontier LLMs + human answers", "86 facts, written and verified by hand"],
    ["Serving", "vLLM, multi-GPU", "Ollama / llama.cpp, one 4 GB GPU"],
  ],
});
note(s, "All model names live in config.yaml; none is hard-coded. Backends: ollama, llama_cpp_server, llama_cpp_python.");
s.addNotes("Reference facts were written from authoritative sources and deliberately not derived from the answer under evaluation, which would inflate recall.");

/* 8 — experimental design */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Methodology" });
eyebrow(s, "Experimental design", true);
title(s, "The answer is generated once and shared", true);
s.addShape(pres.ShapeType.roundRect, {
  objectName: "gen-box",
  x: 2.6,
  y: 1.35,
  w: 8.1,
  h: 0.62,
  rectRadius: 0.31,
  fill: { color: SCARLET },
  line: { color: SCARLET, width: 1 },
});
s.addText("Question → local LLM generates the answer ONCE → outputs/answers.json", {
  isTextBox: true,
  objectName: "gen-text",
  x: 2.6,
  y: 1.35,
  w: 8.1,
  h: 0.62,
  fontSize: 14,
  bold: true,
  color: WHITE,
  align: "center",
  valign: "middle",
  fontFace: "Arial",
  margin: 0,
});
card(s, {
  name: "base",
  x: 1.45,
  y: 2.3,
  w: 5.0,
  h: 2.5,
  fill: DGRAY,
  line: DGRAY,
  heading: "Baseline — variant A",
  headingColor: WHITE,
  body: "SAFE-style extraction\n↓\nRetrieval and verification",
  bodyColor: LGRAY,
  bodySize: 14,
});
card(s, {
  name: "vfl",
  x: 6.9,
  y: 2.3,
  w: 5.0,
  h: 2.5,
  fill: DGRAY,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "VERIFACT-Lite — variant D",
  headingColor: SCARLET,
  body:
    "The same extraction, same facts\n↓  detect incomplete + missing relations\n↓  refine and add facts\n↓  the same retrieval and verification",
  bodyColor: LGRAY,
  bodySize: 14,
});
[
  ["Determinism", "Every LLM call cached as hash(model + prompt + params)"],
  ["Evidence", "Wikipedia pages cached on disk, replayable offline"],
  ["Ablation", "A, B, C and D scored on one identical answer set"],
].forEach(([h, b], i) => {
  card(s, { name: "det" + i, x: 0.6 + i * 4.08, y: 5.05, w: 3.88, h: 1.35, fill: DGRAY, line: DGRAY, heading: h, headingColor: SCARLET, headingSize: 13, body: b, bodyColor: LGRAY, bodySize: 12 });
});
note(s, "The two pipelines differ in exactly one thing: whether the refinement stage runs.");
s.addNotes("The most important methodological point. If baseline and VeriFact saw different answers, any precision difference would be meaningless.");

/* 9 — word mapping */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
eyebrow(s, "Step 2B — the paper's Algorithm 1");
title(s, "Word mapping finds what the facts never covered", false);
s.addText(
  [
    { text: "For each fact, take its longest common substring with the response.", options: { bullet: { type: "number" }, breakLine: true } },
    { text: "Mark those response characters as covered.", options: { bullet: { type: "number" }, breakLine: true } },
    { text: "Collect the contiguous runs that stayed uncovered.", options: { bullet: { type: "number" }, breakLine: true } },
    { text: "Send those spans to the judges as missing-relation candidates.", options: { bullet: { type: "number" } } },
  ],
  { isTextBox: true, objectName: "algo", x: 0.6, y: 1.3, w: 6.0, h: 1.5, fontSize: 14, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 6, margin: 0 }
);
card(s, {
  name: "impl",
  x: 0.6,
  y: 2.95,
  w: 6.0,
  h: 2.0,
  fill: LGRAY,
  line: LGRAY,
  heading: "Implementation",
  body:
    "Normalization for case, whitespace and line breaks is index-preserving — one character in, one character out — so span offsets still point into the original answer. Mapping runs per sentence, as the official repo does.",
  bodySize: 12,
});
s.addShape(pres.ShapeType.roundRect, {
  objectName: "cov-box",
  x: 6.95,
  y: 1.3,
  w: 5.75,
  h: 1.95,
  rectRadius: 0.06,
  fill: { color: BLACK },
  line: { color: BLACK, width: 1 },
});
s.addText(
  [
    { text: "If the demand for gold as jewelry were to disappear, ", options: { color: MGRAY } },
    { text: "making it more competitive with other materials like ", options: { color: SCARLET, bold: true } },
    { text: "copper and silver.", options: { color: MGRAY } },
  ],
  { isTextBox: true, objectName: "cov-text", x: 7.21, y: 1.5, w: 5.25, h: 1.25, fontSize: 13, fontFace: "Arial", lineSpacingMultiple: 1.2, margin: 0 }
);
s.addText("grey = matched by some fact   ·   scarlet = uncovered span", {
  isTextBox: true,
  objectName: "cov-key",
  x: 7.21,
  y: 2.82,
  w: 5.25,
  h: 0.26,
  fontSize: 10,
  color: MGRAY,
  fontFace: "Arial",
  margin: 0,
});
card(s, {
  name: "twoq",
  x: 6.95,
  y: 3.4,
  w: 5.75,
  h: 1.55,
  heading: "Then two judge questions",
  body:
    "1. Does the span express a temporal or contingency relation?\n2. Does any single existing fact already capture it?",
  bodySize: 12,
});
stat(s, { name: "wm1", x: 0.6, y: 5.2, w: 3.9, h: 1.25, label: "Character coverage", value: "0.55–0.59", valueSize: 24 });
stat(s, { name: "wm2", x: 4.7, y: 5.2, w: 3.9, h: 1.25, label: "Candidate spans found", value: "73", valueSize: 24 });
stat(s, { name: "wm3", x: 8.8, y: 5.2, w: 3.9, h: 1.25, label: "Fact added only when", value: "relation ∧ ¬covered", valueSize: 16, valueColor: SCARLET });
note(s, "Kept lexical, as in the paper. A semantic variant is listed as future work rather than silently substituted.");
s.addNotes("Offsets matter: normalization must not shift indices, or every reported span would point at the wrong text.");

/* 10 — benchmark */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Methodology" });
eyebrow(s, "The mini benchmark");
title(s, "12 questions chosen to contain the failure modes", false);
[
  ["Question design", "Each prompt invites conditions, comparisons, event order or cause and effect. Gold and jewelry, aluminium vs silver, Chernobyl, Panama Canal, Concorde, sea ice."],
  ["Reference facts", "86 facts, 3–8 per question, written by hand from authoritative sources and not derived from the answer being evaluated. Sources recorded in the JSONL."],
  ["Answers", "One paragraph per question from Qwen2.5-3B at temperature 0.7, generated once. Every evaluation call runs at temperature 0.0–0.2."],
].forEach(([h, b], i) => {
  card(s, { name: "bm" + i, x: 0.6 + i * 4.08, y: 1.3, w: 3.88, h: 2.35, heading: h, body: b, bodySize: 12 });
});
[
  ["Precision", "Supported facts ÷ all extracted facts. Undecided is reported separately and never counted as support."],
  ["Recall", "Reference facts entailed by the answer ÷ all reference facts. Lexical gate, then local-LLM entailment."],
  ["Incomplete rate", "Measured by one designated judge, while refinement is driven by the union — facts are not scored by the ensemble that selected them."],
].forEach(([h, b], i) => {
  card(s, { name: "met" + i, x: 0.6 + i * 4.08, y: 3.9, w: 3.88, h: 2.5, fill: BLACK, line: BLACK, heading: h, headingColor: SCARLET, body: b, bodyColor: LGRAY, bodySize: 12 });
});
note(s, "A 12-question benchmark cannot support the paper's conclusions; it can show whether the mechanism behaves as described.");
s.addNotes("Recall is defined on the answer, not the fact set. That is why it cannot move between variants — state this before anyone asks.");

/* 11 — section divider: results */
pres.addSection({ title: "Results" });
s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Results" });
sectionEyebrow(s, "Part two");
sectionTitleText(s, "Measured results");
s.addNotes("Everything from here is measured by the repository on the 12-question benchmark.");

/* 12 — headline results */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
eyebrow(s, "Baseline vs VERIFACT-Lite");
title(s, "Extraction improves. Precision falls.", false);
stat(s, { name: "h1", x: 0.6, y: 1.3, w: 2.88, h: 1.5, label: "Incomplete fact rate", value: "0.105 → 0.091", valueSize: 20, foot: "−12.8%", footColor: SCARLET });
stat(s, { name: "h2", x: 3.68, y: 1.3, w: 2.88, h: 1.5, label: "Missing relational facts", value: "51 → 0", valueSize: 20, foot: "all recovered", footColor: SCARLET });
stat(s, { name: "h3", x: 6.76, y: 1.3, w: 2.88, h: 1.5, label: "Precision", value: "0.420 → 0.343", valueSize: 20, foot: "−0.077", footColor: SCARLET });
stat(s, { name: "h4", x: 9.84, y: 1.3, w: 2.88, h: 1.5, label: "Recall · F1", value: "0.408 · 0.372", valueSize: 20, foot: "recall fixed by design" });
s.addChart(
  pres.ChartType.bar,
  [
    { name: "Baseline", labels: ["Precision", "Recall", "F1"], values: [0.42, 0.4077, 0.4138] },
    { name: "VERIFACT-Lite", labels: ["Precision", "Recall", "F1"], values: [0.3426, 0.4077, 0.3723] },
  ],
  Object.assign({}, CHART_BASE, {
    objectName: "chart-prf",
    x: 0.6,
    y: 3.0,
    w: 6.0,
    h: 3.4,
    barDir: "col",
    barGapWidthPct: 60,
    chartColors: [MGRAY, SCARLET],
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.000",
    valAxisMaxVal: 0.55,
    valAxisMinVal: 0,
  })
);
card(s, {
  name: "where",
  x: 6.95,
  y: 3.0,
  w: 5.75,
  h: 3.4,
  fill: BLACK,
  line: BLACK,
  heading: "Where the precision went",
  headingColor: SCARLET,
  body:
    "Supported 109 → 108.  Contradicted 3 → 3.  Undecided 146 → 185.\n\nRefined claims carry their condition or comparison target, so one Wikipedia sentence has to support more — and often none does.\n\nOf the claims the verifier could decide, 97.3% were supported both before and after.",
  bodyColor: LGRAY,
  bodySize: 13,
});
note(s, "Same answers, same retrieval, same verifier — only refinement differs. 163 facts refined, 51 added.");
s.addNotes("Lead honestly: the mechanism does what the paper says to the fact set, and measured precision goes down. The next two slides explain why that is the expected direction.");

/* 13 — ablation */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
eyebrow(s, "Ablation");
title(s, "Each mechanism moves the metric it targets", false);
table(s, {
  name: "abl",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [3.7, 1.9, 1.6, 1.7, 1.6, 1.6],
  rowH: 0.42,
  fontSize: 13,
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
  ["C isolates relation recovery", "All 51 missing relations become facts. The incomplete rate ticks up to 0.113 because the new facts are judged too."],
  ["The effects are additive", "D inherits B's lower incomplete rate and C's zero missing relations — and both precision costs."],
].forEach(([h, b], i) => {
  card(s, { name: "abl" + i, x: 0.6 + i * 4.08, y: 3.6, w: 3.88, h: 1.9, fill: LGRAY, line: LGRAY, heading: h, headingSize: 14, body: b, bodySize: 12 });
});
note(s, "All four variants scored on one identical answer set, union ensemble, as in the paper.");
s.addNotes("C raising the incomplete rate is worth explaining: added relational facts are measured too, and a 3B model writing a relation sentence often produces something the judge then calls dependent.");

/* 14 — judge ablation */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
eyebrow(s, "Judge ablation");
title(s, "Union collapses onto the permissive judge", false);
table(s, {
  name: "judges",
  x: 0.6,
  y: 1.35,
  w: 6.0,
  colW: [2.1, 1.3, 1.3, 1.3],
  rowH: 0.4,
  fontSize: 12,
  head: ["Judge", "Incompl.", "Relations", "Precision"],
  rows: [
    ["Qwen2.5-3B", "20", "2", "0.955"],
    ["Llama-3.2-3B", "34", "71", { text: "0.200", emph: true }],
    ["Majority of both", "19", "2", "1.000"],
  ],
});
s.addText(
  "Precision is measured against the majority decision. Llama flags almost everything, so the union of two judges is just Llama's opinion — the paper's recall-first rule needs three judges to behave as intended.",
  { isTextBox: true, objectName: "judge-note", x: 0.6, y: 3.15, w: 6.0, h: 1.1, fontSize: 12, color: DGRAY, fontFace: "Arial", lineSpacingMultiple: 1.2, margin: 0 }
);
table(s, {
  name: "rules",
  x: 6.95,
  y: 1.35,
  w: 5.75,
  colW: [1.95, 1.3, 1.25, 1.25],
  rowH: 0.4,
  fontSize: 12,
  head: ["Rule", "Incompl.", "Precision", "F1"],
  rows: [
    ["Baseline", "0.105", "0.4200", "0.4138"],
    ["Union (paper)", "0.091", "0.3426", "0.3723"],
    ["Majority", { text: "0.042", emph: true }, { text: "0.4071", emph: true }, { text: "0.4074", emph: true }],
  ],
});
card(s, {
  name: "finding",
  x: 6.95,
  y: 3.15,
  w: 5.75,
  h: 1.85,
  fill: BLACK,
  line: BLACK,
  heading: "The clearest finding",
  headingColor: SCARLET,
  body:
    "Majority vote cuts the incomplete rate by 60% (0.105 → 0.042) and costs almost no precision (−0.013). Union cuts it 12.8% and costs 0.077.",
  bodyColor: LGRAY,
  bodySize: 13,
});
s.addChart(
  pres.ChartType.bar,
  [{ name: "Incomplete fact rate", labels: ["Baseline", "Union", "Majority"], values: [0.105, 0.091, 0.042] }],
  Object.assign({}, CHART_BASE, {
    objectName: "chart-rule",
    x: 0.6,
    y: 4.45,
    w: 6.0,
    h: 2.0,
    barDir: "bar",
    showLegend: false,
    chartColors: [SCARLET],
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelFormatCode: "0.000",
    valAxisMinVal: 0,
    valAxisMaxVal: 0.12,
  })
);
note(s, "Both tables use identical judge decisions — only the rule that turns votes into a refinement decision differs.");
s.addNotes("This is the result worth defending, and it is ours rather than the paper's. With two weak judges a majority rule recovers most of the benefit at a fraction of the cost.");

/* 15 — verdict changes */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Results" });
eyebrow(s, "The research question", true);
title(s, "Does fixing a claim change its verdict?", true);
s.addShape(pres.ShapeType.roundRect, {
  objectName: "big",
  x: 0.6,
  y: 1.35,
  w: 3.5,
  h: 2.6,
  rectRadius: 0.06,
  fill: { color: SCARLET },
  line: { color: SCARLET, width: 1 },
});
s.addText("39.3%", {
  isTextBox: true,
  objectName: "big-v",
  x: 0.6,
  y: 1.7,
  w: 3.5,
  h: 1.1,
  fontSize: 60,
  bold: true,
  color: WHITE,
  align: "center",
  margin: 0,
});
s.addText("of refined facts changed label\n70 of 178", {
  isTextBox: true,
  objectName: "big-l",
  x: 0.6,
  y: 2.85,
  w: 3.5,
  h: 0.9,
  fontSize: 14,
  color: WHITE,
  align: "center",
  fontFace: "Arial",
  lineSpacingMultiple: 1.2,
  margin: 0,
});
table(s, {
  name: "trans",
  x: 4.45,
  y: 1.35,
  w: 8.25,
  colW: [3.4, 1.15, 3.7],
  rowH: 0.37,
  fontSize: 12,
  align: "left",
  head: ["Transition", "Count", "Meaning"],
  rows: [
    ["SUPPORTED → UNDECIDED", "37", "was over-credited"],
    ["UNDECIDED → SUPPORTED", "29", "context made it checkable"],
    ["UNDECIDED → CONTRADICTED", "2", "error exposed"],
    ["CONTRADICTED → SUPPORTED", "1", "was mis-blamed"],
    ["CONTRADICTED → UNDECIDED", "1", "was mis-blamed"],
    ["unchanged", "108", "verdict stable"],
  ],
});
card(s, {
  name: "cmp-paper",
  x: 0.6,
  y: 4.3,
  w: 12.1,
  h: 1.9,
  fill: DGRAY,
  line: DGRAY,
  heading: "Against the paper",
  headingColor: SCARLET,
  body:
    "The paper reports 24.9% of refined facts changing label, with supported falling and contradicted rising, and concludes that ignoring incomplete facts overestimates model factuality.\nWe measure 39.3%, with supported falling into undecided rather than into contradicted — the same conclusion, reached with 3B models and Wikipedia.",
  bodyColor: LGRAY,
  bodySize: 13,
});
note(s, "37 claims the baseline called SUPPORTED could not survive having their own context restored.");
s.addNotes("This slide justifies the paper. A quarter to two fifths of verdicts are decided by whether the claim kept its context.");

/* 16 — qualitative */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
eyebrow(s, "Qualitative");
title(s, "What a 3B refiner actually produces", false);
card(s, { name: "good", x: 0.6, y: 1.3, w: 6.0, h: 3.5, line: SCARLET, lineWidth: 1.5, heading: "Works — Q10, ozone layer", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "omitted_condition_or_source", options: { color: MGRAY, fontSize: 11, breakLine: true } },
    { text: "before   “These substances are in the atmosphere.”", options: { breakLine: true } },
    { text: "after     “The substances are in the atmosphere since the Montreal Protocol was signed.”", options: { breakLine: true } },
    { text: "UNDECIDED → SUPPORTED", options: { color: SCARLET, bold: true, fontSize: 12, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "missing_comparison", options: { color: MGRAY, fontSize: 11, breakLine: true } },
    { text: "before   “The decrease is in the concentration of substances.”", options: { breakLine: true } },
    { text: "after     “… compared to before the Montreal Protocol.”", options: { breakLine: true } },
    { text: "UNDECIDED → SUPPORTED", options: { color: SCARLET, bold: true, fontSize: 12 } },
  ],
  { isTextBox: true, objectName: "good-t", x: 0.86, y: 1.85, w: 5.5, h: 2.8, fontSize: 12, color: DGRAY, fontFace: "Arial", lineSpacingMultiple: 1.15, margin: 0 }
);
card(s, { name: "bad", x: 6.95, y: 1.3, w: 5.75, h: 3.5, heading: "Fails — Q01, the paper's own example", headingColor: DGRAY, body: "" });
s.addText(
  [
    { text: "the refiner flipped the meaning", options: { color: MGRAY, fontSize: 11, breakLine: true } },
    { text: "before   “There was demand for gold as jewelry.”", options: { breakLine: true } },
    { text: "after     “There was no demand for gold as jewelry.”", options: { breakLine: true } },
    { text: "The hypothetical from the question was pasted into a fact stating the opposite.", options: { color: SCARLET, fontSize: 12, breakLine: true } },
    { text: " ", options: { fontSize: 6, breakLine: true } },
    { text: "condition attached to the wrong claim", options: { color: MGRAY, fontSize: 11, breakLine: true } },
    { text: "“Gold has unique properties of malleability if there was no demand for gold as jewelry.”", options: { breakLine: true } },
    { text: "SUPPORTED → UNDECIDED", options: { color: SCARLET, bold: true, fontSize: 12 } },
  ],
  { isTextBox: true, objectName: "bad-t", x: 7.21, y: 1.85, w: 5.25, h: 2.8, fontSize: 12, color: DGRAY, fontFace: "Arial", lineSpacingMultiple: 1.15, margin: 0 }
);
card(s, {
  name: "added",
  x: 0.6,
  y: 5.05,
  w: 12.1,
  h: 1.35,
  fill: BLACK,
  line: BLACK,
  heading: "Added relational fact — Q04, Chernobyl, temporal",
  headingColor: SCARLET,
  headingSize: 13,
  body:
    "“The experiment just before the explosion caused the reactor to exceed its design limits, resulting in the explosion of hydrogen gas in the pressure vessel.”  The span that produced it was never covered by any extracted fact.",
  bodyColor: LGRAY,
  bodySize: 12,
});
note(s, "6 examples auto-selected into outputs/examples/presentation_examples.json, ranked by label changes and error type.");
s.addNotes("Showing a failure is deliberate. The refiner has no guard against changing meaning, which is exactly why a stronger model is improvement number one.");

/* 17 — section divider: comparison */
pres.addSection({ title: "Comparison" });
s = pres.addSlide({ masterName: "SECTION", sectionTitle: "Comparison" });
sectionEyebrow(s, "Part three");
sectionTitleText(s, "Comparison and limits");
s.addNotes("How our numbers line up against the paper's, and what they cannot tell you.");

/* 18 — vs paper */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Comparison" });
eyebrow(s, "Comparison with the paper");
title(s, "Directions match. Magnitudes do not.", false);
table(s, {
  name: "vs",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [3.5, 3.4, 3.3, 1.9],
  rowH: 0.38,
  fontSize: 12,
  align: "left",
  head: ["Measure", "Paper", "VERIFACT-Lite", "Agreement"],
  rows: [
    ["Incomplete facts, baseline", "56.7% (SAFE)", "10.5%", "scale differs"],
    ["Incomplete facts, refined", "22.5%  (−19.2 pts)", "9.1% union · 4.2% majority", "same direction"],
    ["Missing relational facts", "1.22 → 0.76 (−37%)", "51 → 0 (−100%)", "same direction"],
    ["Refined facts changing label", "24.9%", { text: "39.3%", emph: true }, "same phenomenon"],
    ["Direction of that change", "supported ↓, contradicted ↑", "supported ↓, undecided ↑", "partial"],
    ["Precision", "82.8 (Qwen2.5-32B)", "34.3 union · 40.7 majority", "not comparable"],
    ["Recall", "44.1", "40.8", "coincidentally close"],
    ["F1", "57.5", "37.2 union · 40.7 majority", "not comparable"],
  ],
});
[
  ["Reproduced", "The mechanism detects both problem types, repairs them, and changing the facts changes the verdicts — the paper's central claim.", SCARLET],
  ["Not reproduced", "Absolute precision, recall and F1. Different models, different evidence, 12 prompts instead of 1,096, no human annotation.", MGRAY],
  ["Why our baseline looks cleaner", "10.5% vs 56.7% incomplete reflects a weaker 3B judge, not a better extractor. A judge that abstains finds fewer problems.", MGRAY],
].forEach(([h, b, col], i) => {
  card(s, { name: "vs" + i, x: 0.6 + i * 4.08, y: 4.75, w: 3.88, h: 1.65, heading: h, headingColor: col, headingSize: 14, body: b, bodySize: 12 });
});
note(s, "Every right-hand value is measured by this repository; none is copied from the paper or estimated.");
s.addNotes("If asked whether we reproduced the paper: the mechanism and the qualitative conclusions yes, the numbers no, and the deck says so in three places.");

/* 19 — limitations */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Comparison" });
eyebrow(s, "Limitations found by breaking our own result");
title(s, "What these numbers cannot tell you", false);
card(s, {
  name: "rubber",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  h: 1.75,
  fill: BLACK,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "A 3B verifier rubber-stamps unless you force it to quote",
  headingColor: SCARLET,
  body:
    "An earlier version reported precision 0.92 and zero contradictions across 258 facts. It called “Aluminium is the rarest metal in the Earth's crust” SUPPORTED with confidence 1.0. Requiring a verbatim quote from the evidence, and discarding verdicts whose quote cannot be found, moved precision to 0.42 and made contradictions appear. The honest number is the lower one.",
  bodyColor: LGRAY,
  bodySize: 12,
});
s.addText(
  [
    { text: "Undecided dominates — 146 of 258 baseline verdicts. Precision partly measures retrieval coverage.", options: { bullet: true, breakLine: true } },
    { text: "Recall cannot move between variants: it scores the answer, which is fixed.", options: { bullet: true, breakLine: true } },
    { text: "The incomplete rate is judged by a 3B model, far weaker than the paper's GPT-4o.", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "lim-l", x: 0.6, y: 3.3, w: 6.0, h: 2.1, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 8, margin: 0 }
);
s.addText(
  [
    { text: "12 questions, 86 reference facts. Trends only — no significance claim.", options: { bullet: true, breakLine: true } },
    { text: "No human annotation, so no ground truth for extraction quality.", options: { bullet: true, breakLine: true } },
    { text: "Retrieval was initially non-deterministic: Wikipedia rate-limited us and failures read as “no evidence”. Fixed with retries, backoff and an on-disk cache.", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "lim-r", x: 6.95, y: 3.3, w: 5.75, h: 2.1, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 8, margin: 0 }
);
note(s, "All of these are written up in the README under Deviations. 59 unit tests cover word mapping, parsing, metrics and refinement.");
s.addNotes("Owning the 0.92 mistake openly is stronger than hiding it: it shows the evaluation harness was itself tested.");

/* 20 — improvements, top */
pres.addSection({ title: "Future work" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Future work" });
eyebrow(s, "Future work — highest expected return");
title(s, "Where the headroom is", false);
table(s, {
  name: "imp",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [0.5, 3.6, 5.4, 2.6],
  rowH: 0.52,
  fontSize: 12,
  align: "left",
  head: ["#", "Change", "Why it should help here", "Metric"],
  rows: [
    ["1", "Stronger local judge — Qwen3, Llama 3.x, Gemma", "Our weakest link is a 3B judge that flags almost everything. Detection gates every later stage.", "precision ↑ recall ↑ F1 ↑"],
    ["2", "7B–14B at Q4/Q5 instead of 3B", "Still local. Better handling of conditions and comparanda, better refinement wording.", "precision ↑ F1 ↑"],
    ["3", "Third judge and self-consistency", "With two judges the union collapses onto the permissive one. A third breaks ties.", "detection precision ↑"],
    ["4", "Better retrieval — dense embeddings, reranking", "Most lost precision is Undecided, not Contradicted: the evidence simply is not there.", "undecided ↓ precision ↑"],
    ["5", "Iterative refinement, max 2 passes", "Refined facts are sometimes still flagged. One more cycle should converge them.", "incomplete rate ↓"],
    ["6", "Hybrid rule + LLM relation detection", "Cue words pre-screen spans. Implemented behind a flag, off by default.", "recall ↑ latency ↓"],
  ],
});
note(s, "Proposed directions, not validated results — none has been run in this reimplementation.");
s.addNotes("State the honesty caveat out loud. The ranking is reasoned from where our measured losses actually are.");

/* 21 — improvements, rest */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Future work" });
eyebrow(s, "Future work — the rest of the list");
title(s, "Measurement quality, then model economics", false);
card(s, { name: "meas", x: 0.6, y: 1.3, w: 6.0, h: 4.6, heading: "Make the measurement trustworthy", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "Verification ensemble — LLM verdict plus an NLI model", options: { bullet: true, breakLine: true } },
    { text: "Evidence-aware verification — name the span, then judge", options: { bullet: true, breakLine: true } },
    { text: "Adaptive evidence count, driven by uncertainty", options: { bullet: true, breakLine: true } },
    { text: "Semantic reference matching — embeddings plus entailment", options: { bullet: true, breakLine: true } },
    { text: "Better reference sets — several answers, human verification", options: { bullet: true, breakLine: true } },
    { text: "Calibration of the three label thresholds", options: { bullet: true, breakLine: true } },
    { text: "Semantic missing-span matching for paraphrases", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "meas-l", x: 0.86, y: 1.9, w: 5.5, h: 3.8, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 9, margin: 0 }
);
card(s, { name: "econ", x: 6.95, y: 1.3, w: 5.75, h: 4.6, heading: "Make it cheaper or sharper", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "Query diversification — keyword, entity, paraphrase, relation", options: { bullet: true, breakLine: true } },
    { text: "Knowledge-source diversification, routed by claim type", options: { bullet: true, breakLine: true } },
    { text: "Claim difficulty routing — small model, then large", options: { bullet: true, breakLine: true } },
    { text: "Confidence-weighted ensemble — selectable, untuned", options: { bullet: true, breakLine: true } },
    { text: "Fine-tuned detector on labelled claims", options: { bullet: true, breakLine: true } },
    { text: "Distillation from a large open teacher", options: { bullet: true, breakLine: true } },
    { text: "The remaining baselines: FactScore, FactCheck-GPT, VERIFY", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "econ-l", x: 7.21, y: 1.9, w: 5.25, h: 3.8, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 9, margin: 0 }
);
note(s, "Full list with expected metric effects in the repository README.");
s.addNotes("If time is short, skip this slide. It exists so the question “what else would you do” has a written answer.");

/* 22 — takeaways */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Future work" });
eyebrow(s, "Takeaways", true);
title(s, "Four things this reimplementation establishes", true);
[
  ["1", "The whole VeriFact pipeline runs on a 4 GB consumer GPU with two 3B quantized models, free Wikipedia evidence and no API key."],
  ["2", "Refinement changed the verdict on 39.3% of refined facts, against 24.9% in the paper. Factuality scores depend on whether claims keep their context."],
  ["3", "Precision falls after refinement, 0.420 → 0.343 — the paper's own finding. Unrefined atomic facts overstate factuality."],
  ["4", "With weak judges the union rule is dominated by the most permissive one. Majority vote cut the incomplete rate 60% for 0.013 precision."],
].forEach(([n, t], i) => {
  const y = 1.35 + i * 1.3;
  const last = i === 3;
  s.addShape(pres.ShapeType.roundRect, {
    objectName: "tk" + n,
    x: 0.6,
    y,
    w: 12.1,
    h: 1.12,
    rectRadius: 0.06,
    fill: { color: DGRAY },
    line: { color: last ? SCARLET : DGRAY, width: last ? 1.5 : 1 },
  });
  s.addShape(pres.ShapeType.ellipse, {
    objectName: "tk-b" + n,
    x: 0.85,
    y: y + 0.31,
    w: 0.5,
    h: 0.5,
    fill: { color: SCARLET },
    line: { color: SCARLET, width: 1 },
  });
  s.addText(n, {
    isTextBox: true,
    objectName: "tk-n" + n,
    x: 0.85,
    y: y + 0.31,
    w: 0.5,
    h: 0.5,
    fontSize: 16,
    bold: true,
    color: WHITE,
    align: "center",
    valign: "middle",
    margin: 0,
  });
  s.addText(t, {
    isTextBox: true,
    objectName: "tk-t" + n,
    x: 1.55,
    y: y + 0.16,
    w: 10.9,
    h: 0.8,
    fontSize: 14,
    color: LGRAY,
    fontFace: "Arial",
    lineSpacingMultiple: 1.15,
    valign: "middle",
    margin: 0,
  });
});
note(s, "Repository: config-driven, cached, 59 tests  ·  run_baseline · run_verifact · run_ablation · compare · demo.py · Streamlit app");
s.addNotes("Close on point 4: it is the one result that is ours rather than the paper's, it is measured, and it points directly at the first item of future work.");

/* ------------------------------------------------------------------ write */

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote " + OUT);
})();
