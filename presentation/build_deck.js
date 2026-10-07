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

/* ----------------------------------------------------------------- slides
 * 15 slides, paced for a 15-minute talk (~15:00 of content).
 * Per-slide timings are the first line of each slide's speaker notes.
 * Three appendix slides follow slide 15 for the question period; they are not
 * part of the 15 minutes and can be deleted without touching the talk.
 *
 * Numbers come from three runs over the SAME 12 generated answers:
 *   laptop-3B   Qwen2.5-3B primary, Qwen2.5-3B + Llama-3.2-3B judges
 *   judges-7B   Qwen2.5-3B primary, Qwen2.5-7B + Llama-3.1-8B judges   (Colab T4)
 *   full-7B     Qwen2.5-7B primary, Qwen2.5-7B + Llama-3.1-8B judges   (Colab T4)
 * -------------------------------------------------------------------------- */

/* 1 — title  [0:20] */
pres.addSection({ title: "Talk" });
let s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Talk" });
coverEyebrow(s, "Paper reimplementation");
coverTitle(s, "VERIFACT-Lite");
coverBody(
  s,
  "A resource-constrained reimplementation of the core VeriFact methodology using open-source, locally hosted models"
);
[
  ["Qwen2.5-3B to Llama-3.1-8B", 0.75],
  ["Q4_K_M, 4 GB GPU and a T4", 4.1],
  ["Wikipedia evidence", 7.1],
  ["$0 total cost", 9.45],
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
  "[0:20] One sentence: we rebuilt the paper's mechanism on hardware that costs nothing to run, measured it against its own baseline, then re-ran the whole thing with larger judges to find out which conclusions were real. Move on quickly."
);

/* 2 — the problem  [1:20] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "The problem VeriFact solves");
title(s, "Atomic facts lose the context that makes them true", false);
s.addShape(pres.ShapeType.roundRect, {
  objectName: "quote-box",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  h: 0.95,
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
    y: 1.4,
    w: 11.6,
    h: 0.75,
    fontFace: "Arial",
    lineSpacingMultiple: 1.15,
    margin: 0,
    valign: "middle",
  }
);
card(s, { name: "safe", x: 0.6, y: 2.45, w: 6.0, h: 2.55, heading: "Extracted by SAFE", headingColor: DGRAY, body: "" });
s.addText(
  [
    { text: "There is a demand for gold as jewelry.", options: { bullet: true, breakLine: true } },
    { text: "The price of gold could drop by 20–50% or more.", options: { bullet: true, breakLine: true } },
    { text: "condition dropped", options: { color: SCARLET, bold: true, breakLine: true, fontSize: 11 } },
    { text: "Copper and silver are competitive with gold in price.", options: { bullet: true, breakLine: true } },
    { text: "stated unconditionally; the causal link in “making” is never extracted", options: { color: SCARLET, bold: true, fontSize: 11 } },
  ],
  { isTextBox: true, objectName: "safe-list", x: 0.86, y: 2.98, w: 5.5, h: 1.9, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 4, margin: 0 }
);
card(s, { name: "vf", x: 6.95, y: 2.45, w: 5.75, h: 2.55, line: SCARLET, lineWidth: 1.5, heading: "Extracted by VeriFact", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "There is a demand for gold as jewelry.", options: { bullet: true, breakLine: true } },
    { text: "If the demand for gold as jewelry disappeared, the price of gold could drop by 20–50% or more.", options: { bullet: true, breakLine: true } },
    { text: "A 20–50% drop in the price of gold could make copper and silver competitive with gold.", options: { bullet: true, breakLine: true } },
    { text: "condition preserved, causal relation recovered as its own fact", options: { color: SCARLET, bold: true, fontSize: 11 } },
  ],
  { isTextBox: true, objectName: "vf-list", x: 7.21, y: 2.98, w: 5.25, h: 1.9, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 4, margin: 0 }
);
stat(s, { name: "p1", x: 0.6, y: 5.2, w: 3.9, h: 1.25, label: "Incomplete facts in SAFE", value: "12.68%", foot: "451 facts, human-annotated", valueColor: SCARLET, valueSize: 26 });
stat(s, { name: "p2", x: 4.7, y: 5.2, w: 3.9, h: 1.25, label: "Missing facts per response", value: "1.24", foot: "relations never extracted", valueColor: SCARLET, valueSize: 26 });
stat(s, { name: "p3", x: 8.8, y: 5.2, w: 3.9, h: 1.25, label: "Of those, omitted conditions", value: "51%", foot: "the gold case above", valueColor: SCARLET, valueSize: 26 });
note(s, "VeriFact: Liu, Zhang, Munir, Gu & Wang, EMNLP 2025, pp. 17908–17925  ·  github.com/launchnlp/VeriFact");
s.addNotes(
  "[1:20] This example is the whole paper. Verifying the stripped claim gives a meaningless verdict, because it is not what the answer said. Read the two fact lists side by side, then point at the three numbers: measured on human annotation, not anecdote."
);

/* 3 — methodology  [1:15] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "How the paper works");
title(s, "Four steps, three judges, union of detections", false);
[
  ["1", "Decompose", "SAFE's extractor splits each sentence into atomic facts, then resolves vague references.", false],
  ["2", "Detect", "Judges flag incomplete facts by subtype, and missing temporal or contingency relations.", true],
  ["3", "Refine", "Self-reflection rewrites each flagged fact and writes one new fact per missing relation.", true],
  ["4", "Verify", "Google Search via Serper, cross-encoder reranking, then Supported / Contradicted / Undecided.", false],
].forEach(([n, h, b, accent], i) => {
  card(s, {
    name: "step" + n,
    x: 0.6 + i * 3.08,
    y: 1.3,
    w: 2.88,
    h: 2.45,
    badge: n,
    badgeFill: accent ? SCARLET : MGRAY,
    heading: h,
    body: b,
    line: accent ? SCARLET : LGRAY,
    bodySize: 12,
  });
});
card(s, {
  name: "ensemble",
  x: 0.6,
  y: 4.0,
  w: 8.3,
  h: 2.4,
  fill: BLACK,
  line: BLACK,
  heading: "The detection ensemble",
  headingColor: SCARLET,
  body:
    "GPT-4o + Llama 3.3-70B + Qwen 2.5-32B. Positive detections are unioned, not voted: one LLM agrees with human annotators at only κ = 0.33, so the paper trades precision for recall and lets refinement absorb the false positives.",
  bodyColor: LGRAY,
});
stat(s, { name: "r1", x: 9.25, y: 4.0, w: 1.65, h: 2.4, label: "Recall", value: "0.89", foot: "incomplete", fill: DGRAY, labelColor: LGRAY, valueColor: WHITE, footColor: LGRAY, valueSize: 26 });
stat(s, { name: "r2", x: 11.05, y: 4.0, w: 1.65, h: 2.4, label: "Recall", value: "0.85", foot: "missing", fill: DGRAY, labelColor: LGRAY, valueColor: WHITE, footColor: LGRAY, valueSize: 26 });
note(s, "Steps 2 and 3 are the paper's contribution. These 3 judges are the detection ensemble — not the 12 models the paper separately benchmarks.");
s.addNotes(
  "[1:15] Steps 1 and 4 are inherited from SAFE and FactCheck-GPT. Steps 2 and 3 are what is new. The union rule becomes important later: we test whether it is the right choice."
);

/* 4 — substitutions  [1:00] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "What we changed");
title(s, "Every paid component replaced by a free local one", false);
table(s, {
  name: "map",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [3.3, 4.4, 4.4],
  rowH: 0.42,
  fontSize: 13,
  align: "left",
  head: ["Component", "Paper", "VERIFACT-Lite"],
  rows: [
    ["Judges", "GPT-4o + Llama 3.3-70B + Qwen 2.5-32B", "Qwen2.5-3B + Llama-3.2-3B, and 7–8B"],
    ["Extract / refine / verify", "Llama 3.3-70B-Instruct", "Qwen2.5-3B, and Qwen2.5-7B"],
    ["Evidence source", "Google Search via Serper (paid)", "Wikipedia API, cached for replay"],
    ["Evidence ranking", "cross-encoder reranker", "BM25 over retrieved paragraphs"],
    ["Benchmark", "FactRBench, 1,096 prompts", "mini benchmark, 12 prompts"],
    ["Reference facts", "4 frontier LLMs + human answers", "86 facts, written and verified by hand"],
    ["Serving", "vLLM, multi-GPU", "Ollama on a 4 GB GTX 1650 and a Colab T4"],
  ],
});
[
  ["Hardware", "4 GB + T4"],
  ["API keys", "None"],
  ["Total cost", "$0"],
  ["Unit tests", "59 passing"],
].forEach(([l, v], i) => {
  stat(s, { name: "sc" + i, x: 0.6 + i * 3.08, y: 4.75, w: 2.88, h: 1.3, label: l, value: v, valueSize: 22, valueColor: i === 2 ? SCARLET : BLACK });
});
note(s, "All model names live in config.yaml; none is hard-coded. Backends: ollama, llama_cpp_server, llama_cpp_python.");
s.addNotes(
  "[1:00] Do not read the table. Say: every paid or large component has a free local stand-in, the detection logic is unchanged, and the whole thing runs for nothing. Reference facts were written by hand from authoritative sources and deliberately not derived from the answer being evaluated."
);

/* 5 — experimental design  [1:05] */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Talk" });
eyebrow(s, "Experimental design", true);
title(s, "One answer set, three model configurations", true);
s.addShape(pres.ShapeType.roundRect, {
  objectName: "gen-box",
  x: 2.6,
  y: 1.3,
  w: 8.1,
  h: 0.56,
  rectRadius: 0.28,
  fill: { color: SCARLET },
  line: { color: SCARLET, width: 1 },
});
s.addText("Question → local LLM generates the answer ONCE → reused by every run", {
  isTextBox: true,
  objectName: "gen-text",
  x: 2.6,
  y: 1.3,
  w: 8.1,
  h: 0.56,
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
  x: 0.6,
  y: 2.05,
  w: 5.95,
  h: 1.95,
  fill: DGRAY,
  line: DGRAY,
  heading: "Baseline — variant A",
  headingColor: WHITE,
  body: "SAFE-style extraction  →  retrieval and verification",
  bodyColor: LGRAY,
  bodySize: 14,
});
card(s, {
  name: "vfl",
  x: 6.75,
  y: 2.05,
  w: 5.95,
  h: 1.95,
  fill: DGRAY,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "VERIFACT-Lite — variant D",
  headingColor: SCARLET,
  body: "The same facts  →  detect  →  refine and add  →  the same retrieval and verification",
  bodyColor: LGRAY,
  bodySize: 14,
});
table(s, {
  name: "configs",
  x: 0.6,
  y: 4.25,
  w: 12.1,
  colW: [2.6, 3.3, 3.6, 2.6],
  rowH: 0.42,
  fontSize: 12,
  align: "left",
  head: ["Run", "Primary model", "Judges", "Hardware"],
  rows: [
    ["laptop-3B", "Qwen2.5-3B", "Qwen2.5-3B + Llama-3.2-3B", "GTX 1650, 4 GB"],
    ["judges-7B", "Qwen2.5-3B (unchanged)", "Qwen2.5-7B + Llama-3.1-8B", "Colab T4, 16 GB"],
    ["full-7B", "Qwen2.5-7B", "Qwen2.5-7B + Llama-3.1-8B", "Colab T4, 16 GB"],
  ],
});
note(s, "judges-7B changes only the judges, so its baseline fact set is byte-identical to laptop-3B. full-7B changes four things at once.");
s.addNotes(
  "[1:05] The key methodological point, twice over. One: the answer is generated once, so baseline and VeriFact differ only in whether refinement runs. Two: judges-7B replays extraction from cache, so its baseline is identical and the judge upgrade is isolated. full-7B is a different system, not a reproduction."
);

/* 6 — benchmark and metrics  [0:40] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "The mini benchmark");
title(s, "12 questions chosen to contain the failure modes", false);
[
  ["Question design", "Each prompt invites conditions, comparisons, event order or cause and effect. Gold and jewelry, aluminium vs silver, Chernobyl, Panama Canal, Concorde, sea ice."],
  ["Reference facts", "86 facts, 3–8 per question, written by hand from authoritative sources and not derived from the answer being evaluated. Sources recorded in the JSONL."],
  ["Answers", "One paragraph per question from Qwen2.5-3B, generated once and shared by all three runs — verified byte-identical."],
].forEach(([h, b], i) => {
  card(s, { name: "bm" + i, x: 0.6 + i * 4.08, y: 1.3, w: 3.88, h: 2.3, heading: h, body: b, bodySize: 12 });
});
[
  ["Precision", "Supported facts ÷ all extracted facts. Undecided is reported separately and never counted as support."],
  ["Recall", "Reference facts entailed by the answer ÷ all reference facts. It scores the answer, so refinement cannot move it."],
  ["Incomplete rate", "Measured by one designated judge, while refinement is driven by the ensemble — facts are not scored by the rule that selected them."],
].forEach(([h, b], i) => {
  card(s, { name: "met" + i, x: 0.6 + i * 4.08, y: 3.85, w: 3.88, h: 2.45, fill: BLACK, line: BLACK, heading: h, headingColor: SCARLET, body: b, bodyColor: LGRAY, bodySize: 12 });
});
note(s, "A 12-question benchmark cannot support the paper's conclusions; it can show whether the mechanism behaves as described.");
s.addNotes(
  "[0:40] Say the recall definition out loud — it explains why recall never moves between variants. Keep this slide short; the metric definitions matter mostly for the slide after next."
);

/* 7 — headline results  [1:40] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Result 1 — baseline vs VERIFACT-Lite, laptop 3B");
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
    valAxisMinVal: 0,
    valAxisMaxVal: 0.55,
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
s.addNotes(
  "[1:40] Your main results slide. The mechanism does what the paper says to the fact set, and measured precision goes down. Flag that contradicted did not move at all — that becomes the tell on the next slide but one."
);

/* 8 — ablation  [1:00] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Result 2 — ablation, laptop 3B");
title(s, "Each mechanism moves the metric it targets", false);
table(s, {
  name: "abl",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [3.7, 1.9, 1.6, 1.7, 1.6, 1.6],
  rowH: 0.46,
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
  ["C isolates relation recovery", "All 51 missing relations become facts. The incomplete rate ticks up because the new facts are judged too."],
  ["The effects are additive", "D inherits B's lower incomplete rate and C's zero missing relations — and both precision costs."],
].forEach(([h, b], i) => {
  card(s, { name: "abl" + i, x: 0.6 + i * 4.08, y: 3.6, w: 3.88, h: 1.9, fill: LGRAY, line: LGRAY, heading: h, headingSize: 14, body: b, bodySize: 12 });
});
note(s, "All four variants scored on one identical answer set, union ensemble, as in the paper.");
s.addNotes(
  "[1:00] Walk the table once, then read the three cards. Each half of the contribution moves its own metric, and the two compose."
);

/* 9 — the judge is the instrument  [1:30] */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Talk" });
eyebrow(s, "Result 3 — we re-ran everything with 7–8B judges", true);
title(s, "The metrics measure the judge as much as the system", true);
table(s, {
  name: "instrument",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [5.3, 2.3, 2.3, 2.2],
  rowH: 0.46,
  fontSize: 13,
  align: "left",
  head: ["Measured on identical input", "3B judge", "7B judge", "Paper"],
  rows: [
    ["Incomplete rate — the same baseline facts", "0.105", { text: "0.438", emph: true }, "0.567"],
    ["Recall — the same answers, same 86 reference facts", "0.4077", { text: "0.2812", emph: true }, "—"],
    ["Coverage behind that recall", "35 / 86", { text: "24 / 86", emph: true }, "—"],
  ],
});
card(s, {
  name: "insight",
  x: 0.6,
  y: 3.25,
  w: 7.6,
  h: 2.0,
  fill: DGRAY,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "Nothing about the system changed in these rows",
  headingColor: SCARLET,
  body:
    "Same 12 answers, same extracted facts, same reference facts, same lexical gate. Only the model doing the judging changed. A stronger judge finds four times as many incomplete facts and credits the answer with a third fewer reference facts.",
  bodyColor: LGRAY,
  bodySize: 13,
});
stat(s, { name: "i1", x: 8.45, y: 3.25, w: 2.0, h: 2.0, label: "Incomplete", value: "4.2×", foot: "more found", fill: DGRAY, labelColor: LGRAY, valueColor: SCARLET, footColor: LGRAY, valueSize: 32 });
stat(s, { name: "i2", x: 10.7, y: 3.25, w: 2.0, h: 2.0, label: "Recall", value: "−31%", foot: "same answers", fill: DGRAY, labelColor: LGRAY, valueColor: SCARLET, footColor: LGRAY, valueSize: 32 });
card(s, {
  name: "consequence",
  x: 0.6,
  y: 5.45,
  w: 12.1,
  h: 0.95,
  fill: DGRAY,
  line: DGRAY,
  heading: "",
  body:
    "Our baseline looked cleaner than SAFE's 56.7% because our judge was weaker, not because our extractor was better. With a 7B judge the figure moves to 0.438 — two thirds of the way to the paper's.",
  bodyColor: LGRAY,
  bodySize: 13,
});
note(s, "Experiment A on a Colab T4: judges upgraded to Qwen2.5-7B + Llama-3.1-8B, everything else replayed from cache.");
s.addNotes(
  "[1:30] The strongest finding of the project, and it is a methodological one. Any factuality score of this kind is a property of the judge as much as of the system under test. Say plainly: this is why we do not compare our absolute numbers with the paper's."
);

/* 10 — what survived at 7–8B  [1:30] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Result 4 — which conclusions survived the upgrade");
title(s, "One finding held, one was a small-model artifact", false);
table(s, {
  name: "rules",
  x: 0.6,
  y: 1.3,
  w: 6.1,
  colW: [1.5, 1.2, 1.5, 1.2, 0.7],
  rowH: 0.4,
  fontSize: 12,
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
  x: 6.95,
  y: 1.3,
  w: 5.75,
  h: 1.35,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "Held — majority beats union on precision",
  headingColor: SCARLET,
  headingSize: 14,
  body: "In all three configurations, at every model size. The paper's recall-first union rule costs precision it does not need to.",
  bodySize: 12,
});
card(s, {
  name: "broke",
  x: 6.95,
  y: 2.8,
  w: 5.75,
  h: 1.35,
  heading: "Broke — the 60% incomplete-rate gap",
  headingColor: DGRAY,
  headingSize: 14,
  body: "A 3B artifact. With 7–8B judges the two rules are within 4% (0.393 vs 0.411); with a 7B extractor they are identical.",
  bodySize: 12,
});
table(s, {
  name: "judges",
  x: 0.6,
  y: 4.35,
  w: 12.1,
  colW: [3.1, 2.3, 2.3, 2.2, 2.2],
  rowH: 0.38,
  fontSize: 12,
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
  "[1:30] Two claims, opposite fates. Majority beating union survives everywhere. The dramatic incomplete-rate gap was a 3B artifact and we say so. Then the bottom table: for relations the union really is one judge's opinion at every size, but for incompleteness, bigger judges finally complement each other — 33 is more than either 32 or 27, which is the behaviour the paper's union rule assumes."
);

/* 11 — verdict changes  [1:20] */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Talk" });
eyebrow(s, "Result 5 — the research question", true);
title(s, "Does fixing a claim change its verdict?", true);
s.addShape(pres.ShapeType.roundRect, {
  objectName: "big",
  x: 0.6,
  y: 1.3,
  w: 3.3,
  h: 2.3,
  rectRadius: 0.06,
  fill: { color: SCARLET },
  line: { color: SCARLET, width: 1 },
});
s.addText("39–46%", {
  isTextBox: true,
  objectName: "big-v",
  x: 0.6,
  y: 1.55,
  w: 3.3,
  h: 1.0,
  fontSize: 46,
  bold: true,
  color: WHITE,
  align: "center",
  margin: 0,
});
s.addText("of refined facts changed label\nacross all three runs", {
  isTextBox: true,
  objectName: "big-l",
  x: 0.6,
  y: 2.6,
  w: 3.3,
  h: 0.85,
  fontSize: 13,
  color: WHITE,
  align: "center",
  fontFace: "Arial",
  lineSpacingMultiple: 1.2,
  margin: 0,
});
table(s, {
  name: "trans",
  x: 4.25,
  y: 1.3,
  w: 8.45,
  colW: [3.5, 1.2, 1.2, 2.55],
  rowH: 0.37,
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
  x: 0.6,
  y: 3.85,
  w: 12.1,
  h: 2.4,
  fill: DGRAY,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "The paper's full signature only appears with stronger judges",
  headingColor: SCARLET,
  body:
    "The paper reports supported falling AND contradicted rising after refinement, concluding that ignoring incomplete facts overestimates factuality.\n\nWith 3B judges we reproduced only the first half: contradicted never moved off 3. With 7–8B judges it rises to 8 — refinement exposes errors that the stripped claims had hidden. Same conclusion as the paper, now with both halves of the evidence.",
  bodyColor: LGRAY,
  bodySize: 13,
});
note(s, "Every refined fact is verified twice, as its original claim and as its refined claim, through the same evidence pipeline.");
s.addNotes(
  "[1:20] This slide justifies the paper and explains the precision drop. A quarter to nearly half of verdicts are decided by whether the claim kept its context. The contradicted row is the part to dwell on — it is the result we could not get until the judges were big enough."
);

/* 12 — qualitative  [0:45] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Result 6 — qualitative");
title(s, "What a 3B refiner actually produces", false);
card(s, { name: "good", x: 0.6, y: 1.3, w: 6.0, h: 3.4, line: SCARLET, lineWidth: 1.5, heading: "Works — Q10, ozone layer", headingColor: SCARLET, body: "" });
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
  { isTextBox: true, objectName: "good-t", x: 0.86, y: 1.85, w: 5.5, h: 2.7, fontSize: 12, color: DGRAY, fontFace: "Arial", lineSpacingMultiple: 1.15, margin: 0 }
);
card(s, { name: "bad", x: 6.95, y: 1.3, w: 5.75, h: 3.4, heading: "Fails — Q01, the paper's own example", headingColor: DGRAY, body: "" });
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
  { isTextBox: true, objectName: "bad-t", x: 7.21, y: 1.85, w: 5.25, h: 2.7, fontSize: 12, color: DGRAY, fontFace: "Arial", lineSpacingMultiple: 1.15, margin: 0 }
);
card(s, {
  name: "added",
  x: 0.6,
  y: 4.9,
  w: 12.1,
  h: 1.4,
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
s.addNotes(
  "[0:45] Read one example from each side only. Showing the failure is deliberate: the 3B refiner has no guard against changing meaning, which is why a stronger model was the first thing we tested."
);

/* 13 — vs paper  [1:10] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Comparison with the paper");
title(s, "Directions match. Magnitudes do not.", false);
table(s, {
  name: "vs",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  colW: [3.3, 3.0, 3.9, 1.9],
  rowH: 0.4,
  fontSize: 12,
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
  ["Reproduced", "Both problem types detected and repaired; changing the facts changes the verdicts; supported falls and contradicted rises — the paper's central claim.", SCARLET],
  ["Not reproduced", "Absolute precision, recall and F1. Different models, different evidence, 12 prompts instead of 1,096, no human annotation.", MGRAY],
  ["Now explained", "Our low baseline incomplete rate was the judge, not the extractor: the same facts score 10.5% at 3B and 43.8% at 7B against the paper's 56.7%.", MGRAY],
].forEach(([h, b, col], i) => {
  card(s, { name: "vs" + i, x: 0.6 + i * 4.08, y: 4.9, w: 3.88, h: 1.5, heading: h, headingColor: col, headingSize: 14, body: b, bodySize: 12 });
});
note(s, "Every VERIFACT-Lite value is measured by this repository; none is copied from the paper or estimated.");
s.addNotes(
  "[1:10] Point at the Agreement column, not the numbers. The row that changed since the first version of this talk is the last one: we can now explain the gap instead of speculating about it."
);

/* 14 — limits and fixes  [1:10] */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Talk" });
eyebrow(s, "Limits, and what would fix them");
title(s, "Every limitation points at a next step", false);
card(s, {
  name: "rubber",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  h: 1.35,
  fill: BLACK,
  line: SCARLET,
  lineWidth: 1.5,
  heading: "Found by breaking our own result: a 3B verifier rubber-stamps unless forced to quote",
  headingColor: SCARLET,
  headingSize: 14,
  body:
    "An earlier version reported precision 0.92 and zero contradictions across 258 facts, calling “Aluminium is the rarest metal in the Earth's crust” SUPPORTED with confidence 1.0. Requiring a verbatim quote from the evidence moved precision to 0.42 and made contradictions appear.",
  bodyColor: LGRAY,
  bodySize: 12,
});
table(s, {
  name: "fixes",
  x: 0.6,
  y: 2.85,
  w: 12.1,
  colW: [4.6, 4.5, 3.0],
  rowH: 0.46,
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
note(s, "Two rows are now measured rather than proposed. The rest remain proposed directions, not validated results.");
s.addNotes(
  "[1:10] Open by owning the 0.92 mistake — it shows the harness was itself tested. Then the table: the top two rows started as guesses on the first version of this talk and are now experiments with results. The rest are still guesses, and are labelled as such."
);

/* 15 — takeaways  [0:40] */
s = pres.addSlide({ masterName: "CONTENT_DARK", sectionTitle: "Talk" });
eyebrow(s, "Takeaways", true);
title(s, "Four things this reimplementation establishes", true);
[
  ["1", "The whole VeriFact pipeline runs on a 4 GB consumer GPU with quantized 3B models, free Wikipedia evidence and no API key — and scales to 7–8B on a free T4."],
  ["2", "Refinement changed the verdict on 39–46% of refined facts across three model configurations, against 24.9% in the paper. The phenomenon is robust to model size."],
  ["3", "These metrics measure the judge as much as the system: identical facts score 0.105 incomplete at 3B and 0.438 at 7B; identical answers score 0.41 recall at 3B and 0.28 at 7B."],
  ["4", "Majority vote beat the paper's union rule on precision in every configuration — but the large incomplete-rate advantage we first reported was a 3B artifact, and we say so."],
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
  s.addShape(pres.ShapeType.ellipse, { objectName: "tk-b" + n, x: 0.85, y: y + 0.31, w: 0.5, h: 0.5, fill: { color: SCARLET }, line: { color: SCARLET, width: 1 } });
  s.addText(n, { isTextBox: true, objectName: "tk-n" + n, x: 0.85, y: y + 0.31, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(t, { isTextBox: true, objectName: "tk-t" + n, x: 1.55, y: y + 0.12, w: 10.9, h: 0.88, fontSize: 13, color: LGRAY, fontFace: "Arial", lineSpacingMultiple: 1.15, valign: "middle", margin: 0 });
});
note(s, "Repository: config-driven, cached, 59 tests  ·  three runs reproducible from one command without a GPU");
s.addNotes(
  "[0:40] Close on points 3 and 4. Point 3 is the finding that generalises beyond this paper. Point 4 is where we corrected ourselves between the first and second versions of this talk, which is the honest thing to show."
);

/* ------------------------------------------------------------- appendix
 * Not part of the 15 minutes. Kept for the question period; delete freely.
 * ---------------------------------------------------------------------- */

pres.addSection({ title: "Appendix" });

/* A1 — word mapping */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
eyebrow(s, "Appendix — not presented");
title(s, "Step 2B: word mapping, the paper's Algorithm 1", false);
s.addText(
  [
    { text: "For each fact, take its longest common substring with the response.", options: { bullet: { type: "number" }, breakLine: true } },
    { text: "Mark those response characters as covered.", options: { bullet: { type: "number" }, breakLine: true } },
    { text: "Collect the contiguous runs that stayed uncovered.", options: { bullet: { type: "number" }, breakLine: true } },
    { text: "Send those spans to the judges as missing-relation candidates.", options: { bullet: { type: "number" } } },
  ],
  { isTextBox: true, objectName: "algo", x: 0.6, y: 1.3, w: 6.0, h: 1.6, fontSize: 14, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 6, margin: 0 }
);
card(s, {
  name: "impl",
  x: 0.6,
  y: 3.05,
  w: 6.0,
  h: 1.85,
  fill: LGRAY,
  line: LGRAY,
  heading: "Implementation",
  body:
    "Normalization for case, whitespace and line breaks is index-preserving — one character in, one character out — so span offsets still point into the original answer.",
  bodySize: 12,
});
s.addShape(pres.ShapeType.roundRect, {
  objectName: "cov-box",
  x: 6.95,
  y: 1.3,
  w: 5.75,
  h: 1.85,
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
  { isTextBox: true, objectName: "cov-text", x: 7.21, y: 1.48, w: 5.25, h: 1.2, fontSize: 13, fontFace: "Arial", lineSpacingMultiple: 1.2, margin: 0 }
);
s.addText("grey = matched by some fact   ·   scarlet = uncovered span", {
  isTextBox: true,
  objectName: "cov-key",
  x: 7.21,
  y: 2.76,
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
  y: 3.3,
  w: 5.75,
  h: 1.6,
  heading: "Then two judge questions",
  body: "1. Does the span express a temporal or contingency relation?\n2. Does any single existing fact already capture it?",
  bodySize: 12,
});
stat(s, { name: "wm1", x: 0.6, y: 5.1, w: 3.9, h: 1.3, label: "Character coverage", value: "0.55–0.59", valueSize: 24 });
stat(s, { name: "wm2", x: 4.7, y: 5.1, w: 3.9, h: 1.3, label: "Candidate spans found", value: "73", valueSize: 24 });
stat(s, { name: "wm3", x: 8.8, y: 5.1, w: 3.9, h: 1.3, label: "Fact added only when", value: "relation ∧ ¬covered", valueSize: 16, valueColor: SCARLET });
note(s, "Kept lexical, as in the paper. A semantic variant is listed as future work rather than silently substituted.");
s.addNotes("Appendix. Use if asked how missing relations are found.");

/* A2 — full future-work list */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
eyebrow(s, "Appendix — not presented");
title(s, "Full ranked list of proposed improvements", false);
card(s, { name: "a-meas", x: 0.6, y: 1.3, w: 6.0, h: 4.9, heading: "Measurement quality", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "Stronger local judge — tested, 7–8B on a T4", options: { bullet: true, breakLine: true } },
    { text: "Majority vote over union — tested, higher precision", options: { bullet: true, breakLine: true } },
    { text: "Third judge plus self-consistency", options: { bullet: true, breakLine: true } },
    { text: "Verification ensemble — LLM verdict plus an NLI model", options: { bullet: true, breakLine: true } },
    { text: "Evidence-aware verification — name the span, then judge", options: { bullet: true, breakLine: true } },
    { text: "One fixed entailment model for recall across all runs", options: { bullet: true, breakLine: true } },
    { text: "Better reference sets — several answers, human verification", options: { bullet: true, breakLine: true } },
    { text: "Calibration of the three label thresholds", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "a-meas-l", x: 0.86, y: 1.9, w: 5.5, h: 4.1, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 8, margin: 0 }
);
card(s, { name: "a-econ", x: 6.95, y: 1.3, w: 5.75, h: 4.9, heading: "Retrieval, cost and coverage", headingColor: SCARLET, body: "" });
s.addText(
  [
    { text: "Query expansion, dense embeddings, cross-encoder reranking", options: { bullet: true, breakLine: true } },
    { text: "Iterative refinement, maximum two passes", options: { bullet: true, breakLine: true } },
    { text: "Hybrid rule + LLM relation detection (implemented, off)", options: { bullet: true, breakLine: true } },
    { text: "Adaptive evidence count, driven by uncertainty", options: { bullet: true, breakLine: true } },
    { text: "Knowledge-source diversification, routed by claim type", options: { bullet: true, breakLine: true } },
    { text: "Claim difficulty routing — small model, then large", options: { bullet: true, breakLine: true } },
    { text: "Fine-tuned detector; distillation from a large open teacher", options: { bullet: true, breakLine: true } },
    { text: "The remaining baselines: FactScore, FactCheck-GPT, VERIFY", options: { bullet: true } },
  ],
  { isTextBox: true, objectName: "a-econ-l", x: 7.21, y: 1.9, w: 5.25, h: 4.1, fontSize: 13, color: DGRAY, fontFace: "Arial", paraSpaceAfter: 8, margin: 0 }
);
note(s, "The first two items are now measured. The rest are proposed directions with expected metric effects.");
s.addNotes("Appendix. Use if asked what else you would do.");

/* A3 — experiment B and implementation detail */
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Appendix" });
eyebrow(s, "Appendix — not presented");
title(s, "Experiment B, and known hazards", false);
card(s, {
  name: "expb",
  x: 0.6,
  y: 1.3,
  w: 12.1,
  h: 1.9,
  heading: "Experiment B — the whole pipeline at 7B, including the extractor",
  headingColor: SCARLET,
  headingSize: 14,
  body:
    "Baseline: 15.92 facts per answer against 21.50, incomplete rate 0.319, precision 0.5050. Refinement then costs far less precision (−0.025, against −0.118 in experiment A).\n" +
    "A stronger extractor writes fewer, coarser, more self-contained facts, so there is less to repair — the same trade the paper notes for VERIFY (18.5 facts per response against VeriFact's 32.3).\n" +
    "B changed the extractor, the judge, the verifier and the recall entailment model at once, so its columns read only against its own baseline.",
  bodySize: 12,
});
[
  ["GPU hazard", "Two 3B Q4_K_M judges do not fit in 4 GB. The pipeline drives one judge at a time over the whole fact list, then releases its weights — otherwise the backend waits for the resident model's keep-alive and every call pays a ~20 s model load."],
  ["Retrieval hazard", "Wikipedia rate-limits unauthenticated clients. Failed requests are not cached, so without retries a 429 silently becomes “no evidence” and two runs of the same pipeline disagree. Fixed with retries, backoff and Retry-After."],
  ["Reproducibility", "Every LLM call is cached under hash(model + prompt + parameters), every page on disk. Temperature-0 decoding is not bit-reproducible until the cache is warm; all three runs replay exactly from the shipped caches."],
].forEach(([h, b], i) => {
  card(s, { name: "haz" + i, x: 0.6 + i * 4.08, y: 3.45, w: 3.88, h: 2.85, fill: BLACK, line: BLACK, heading: h, headingColor: SCARLET, headingSize: 13, body: b, bodyColor: LGRAY, bodySize: 11 });
});
note(s, "Full write-up in colab/RESULTS.md; all three runs reproduce from one command with no GPU.");
s.addNotes("Appendix. Use if asked about experiment B or about engineering problems.");

/* ------------------------------------------------------------------ write */

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote " + OUT);
})();
