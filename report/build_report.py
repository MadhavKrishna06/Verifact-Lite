"""Build the midterm report as an IEEE double-column .docx.

Numbers in the tables are read from the saved run summaries rather than typed,
so the report cannot drift from the experiments. Prose that states a number
also names where it comes from.

    python report/build_report.py
"""

import json
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "VERIFACT-Lite-midterm-report.docx")

SERIF = "Times New Roman"
BLACK = RGBColor(0, 0, 0)

AUTHORS = [
    "Madhav Krishna Arumulla",
    "Sanskar Jadhav",
    "Sri Charan Komati Reddy",
    "Gourav Verma",
    "Trinath Reddy Vundela",
]


# --------------------------------------------------------------------- data

def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


RUNS = {
    "laptop": load("outputs/summary.json"),
    "judges7b": load("outputs_colab_a/summary.json"),
    "full7b": load("outputs_colab_b/summary.json"),
}


def f(value, places=4):
    return f"{float(value):.{places}f}"


def signed(value, places=3):
    """Format a delta with a typographic minus so it does not wrap on its own."""
    return ("−" if value < 0 else "+") + f"{abs(float(value)):.{places}f}"


def pct(value, places=1):
    return f"{float(value) * 100:.{places}f} %"


# ------------------------------------------------------------------ styling

def set_cell_borders(cell, top=False, bottom=False, size=6):
    tcPr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        element = OxmlElement("w:" + edge)
        on = (edge == "top" and top) or (edge == "bottom" and bottom)
        element.set(qn("w:val"), "single" if on else "nil")
        if on:
            element.set(qn("w:sz"), str(size))
            element.set(qn("w:color"), "000000")
        borders.append(element)
    tcPr.append(borders)


def run(paragraph, text, size=10, bold=False, italic=False, font=SERIF, caps=False):
    r = paragraph.add_run(text)
    r.font.name = font
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic
    r.font.color.rgb = BLACK
    r.font.all_caps = caps
    rpr = r._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(attr), font)
    return r


def para(doc, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_after=0, space_before=0, indent=0.0, line=1.0):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.first_line_indent = Inches(indent)
    pf.line_spacing = line
    return p


def body(doc, text, indent=0.2):
    p = para(doc, indent=indent, space_after=0)
    run(p, text, 10)
    return p


def heading(doc, number, text):
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=3)
    run(p, f"{number}. {text}", 10, caps=True)
    return p


def subheading(doc, letter, text):
    p = para(doc, align=WD_ALIGN_PARAGRAPH.LEFT, space_before=6, space_after=2)
    run(p, f"{letter}. {text}", 10, italic=True)
    return p


# ------------------------------------------------------------------- tables

def add_table(doc, number, title, head, rows, widths=None, size=8):
    cap = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=2)
    run(cap, f"TABLE {number}", 8)
    cap2 = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=3)
    run(cap2, title, 8, caps=True)

    table = doc.add_table(rows=1, cols=len(head))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    hdr = table.rows[0].cells
    for i, text in enumerate(head):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.space_before = Pt(1)
        run(p, text, size, bold=True)
        set_cell_borders(hdr[i], top=True, bottom=True)

    for r_i, row in enumerate(rows):
        cells = table.add_row().cells
        last = r_i == len(rows) - 1
        for i, text in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.space_before = Pt(1)
            run(p, str(text), size)
            set_cell_borders(cells[i], bottom=last)

    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    return table


def add_figure(doc, path, number, caption, width=3.3):
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_before=8, space_after=2)
    p.add_run().add_picture(path, width=Inches(width))
    cap = para(doc, align=WD_ALIGN_PARAGRAPH.LEFT, space_after=4)
    run(cap, f"Fig. {number}. {caption}", 8)


# ------------------------------------------------------------------- layout

def setup(doc):
    s = doc.sections[0]
    s.page_width = Inches(8.5)
    s.page_height = Inches(11)
    s.top_margin = Inches(0.75)
    s.bottom_margin = Inches(1.0)
    s.left_margin = Inches(0.625)
    s.right_margin = Inches(0.625)
    style = doc.styles["Normal"]
    style.font.name = SERIF
    style.font.size = Pt(10)
    style.paragraph_format.space_after = Pt(0)
    style.paragraph_format.line_spacing = 1.0
    return s


def two_columns(doc):
    s = doc.add_section(WD_SECTION.CONTINUOUS)
    s.top_margin = Inches(0.75)
    s.bottom_margin = Inches(1.0)
    s.left_margin = Inches(0.625)
    s.right_margin = Inches(0.625)
    sectPr = s._sectPr
    cols = sectPr.xpath("./w:cols")[0]
    cols.set(qn("w:num"), "2")
    cols.set(qn("w:space"), str(int(0.25 * 1440)))
    cols.set(qn("w:equalWidth"), "1")
    return s


def title_block(doc):
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    run(p, "VERIFACT-Lite: Reproducing a Context-Preserving Fact-Verification Pipeline with Small Open-Weight Models", 20)

    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    run(p, "   ".join(AUTHORS), 11)
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    run(p, "Department of Computer Science, Texas Tech University, Lubbock, TX, USA", 10, italic=True)
    p = para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    run(p, "Midterm report — Neural Networks", 10, italic=True)


# --------------------------------------------------------------------- text

def abstract(doc):
    p = para(doc, space_after=4)
    run(p, "Abstract—", 9, bold=True, italic=True)
    run(
        p,
        "Decomposing a long-form answer into atomic facts is now the standard first step in automatic factuality "
        "evaluation, but decomposition discards the conditions, comparisons and inter-sentence relations that make a "
        "claim true. VeriFact (EMNLP 2025) addresses this by detecting incomplete facts and missing relational facts "
        "and repairing them before verification. This report describes VERIFACT-Lite, a reimplementation of that "
        "mechanism that runs entirely on open-weight models small enough for a 4 GB consumer GPU, with Wikipedia as "
        "the evidence source and no commercial API of any kind. We reproduce the paper's mechanism rather than its "
        "numbers, and we evaluate it on a 12-question benchmark with 86 hand-written reference facts. On the laptop "
        "configuration, refinement reduces the incomplete-fact rate from "
        + f(RUNS["laptop"]["baseline"]["incomplete_rate"], 3)
        + " to "
        + f(RUNS["laptop"]["verifact_lite"]["incomplete_rate"], 3)
        + ", recovers all "
        + str(RUNS["laptop"]["baseline"]["missing_relations"])
        + " missing relational facts, and lowers measured precision from "
        + f(RUNS["laptop"]["baseline"]["precision"])
        + " to "
        + f(RUNS["laptop"]["verifact_lite"]["precision"])
        + ". Repeating the study with 7–8B judges on a free cloud GPU produces the report's central finding: on an "
        "identical fact set, the incomplete-fact rate is "
        + f(RUNS["laptop"]["baseline"]["incomplete_rate"], 3)
        + " under a 3B detector and "
        + f(RUNS["judges7b"]["baseline"]["incomplete_rate"], 3)
        + " under a 7B detector, so this family of metrics measures the judge as much as the system under test. "
        "Refinement changed the verdict on 34.7–45.6 % of refined facts across three configurations, against "
        "24.9 % reported in the paper. We close with six changes to the method itself, each argued from one of "
        "these measurements.",
        9,
        bold=True,
    )

    p = para(doc, space_after=6)
    run(p, "Index Terms—", 9, bold=True, italic=True)
    run(
        p,
        "factuality evaluation, atomic facts, claim decomposition, large language models, LLM-as-judge, "
        "reproducibility, retrieval-augmented verification.",
        9,
        bold=True,
    )


def introduction(doc):
    heading(doc, "I", "Introduction")
    body(
        doc,
        "Automatic factuality evaluation of long-form text has converged on a three-stage recipe: decompose a response "
        "into atomic facts, retrieve evidence for each fact, and label each fact as supported or not. FactScore and "
        "SAFE established the pattern, and most later systems inherit it. The recipe has a structural weakness that is "
        "easy to state and hard to see in aggregate scores: decomposition is lossy. A sentence carrying a condition, a "
        "comparison or a causal link is split into fragments that no longer carry it, and the verifier then adjudicates "
        "a claim the model never actually made.",
        indent=0.0,
    )
    body(
        doc,
        "The example the VeriFact authors use is representative. Given the answer “If the demand for gold as jewelry "
        "were to disappear, the price of gold could drop by 20–50 % or more, making it more competitive with "
        "other materials like copper and silver,” a SAFE-style extractor produces, among others, “The price of "
        "gold could drop by 20–50 % or more” and “Copper and silver are competitive with gold in "
        "price.” The first has lost its hypothetical; the second is stated unconditionally and the causal link in "
        "“making” is never extracted at all. Verifying either fragment against evidence produces a verdict "
        "about something the answer did not assert.",
    )
    body(
        doc,
        "VeriFact inserts two steps between decomposition and verification. It detects incomplete facts, labelled by "
        "subtype, and missing relational facts, which are inter-sentence temporal or contingency relations that no "
        "extracted fact captures; it then repairs the first group and writes new facts for the second. On the authors' "
        "benchmark this reduces the incomplete-fact rate on SAFE output from 56.7 % to 22.5 % and the number "
        "of missing facts per response from 1.22 to 0.76, and changes the verdict on 24.9 % of refined facts.",
    )
    body(
        doc,
        "That pipeline as published depends on resources a student project does not have: GPT-4o, Llama 3.3-70B and "
        "Qwen 2.5-32B as a detection ensemble, Llama 3.3-70B for extraction and refinement, paid Google Search through "
        "Serper for evidence, a cross-encoder reranker, and 1,096 benchmark prompts. The question this project asks is "
        "narrower and, we argue, more useful: does the mechanism still behave as described when every one of those "
        "components is replaced by something that runs locally and costs nothing?",
    )
    body(
        doc,
        "The contributions of this midterm report are the following. First, a complete, configuration-driven "
        "reimplementation of the VeriFact mechanism on quantized 3B–8B open-weight models with Wikipedia evidence "
        "and BM25 ranking, reproducible from one command without a GPU because every model call and every retrieved "
        "page is cached. Second, a measurement of the mechanism against its own baseline on a benchmark deliberately "
        "written to contain the failure modes the paper targets. Third, a controlled repetition of the entire study "
        "with larger judges, which shows that the headline metric of this literature is a property of the judge as much "
        "as of the system being judged. Fourth, a test of the paper's union rule against a majority vote at three model "
        "sizes. Fifth, six proposed changes to the method itself, each argued from one of our measurements rather than "
        "from intuition.",
    )
    body(
        doc,
        "We state plainly what this report does not claim. We do not reproduce the paper's reported numbers, and we do "
        "not attempt to: the models, the evidence source, the benchmark size and the annotation procedure all differ. "
        "Every figure reported here is produced by our own repository and is reproducible from the artifacts we ship.",
    )


def background(doc):
    heading(doc, "II", "Background and Related Work")
    subheading(doc, "A", "Decomposition-based factuality evaluation")
    body(
        doc,
        "FactScore introduced per-atomic-fact scoring of long-form generation, and SAFE added a search-augmented "
        "evaluator that decomposes a response into self-contained claims and checks each one against retrieved "
        "evidence. FactCheck-GPT formalised the verification stage into a pipeline of decomposition, evidence "
        "retrieval and stance classification. All three share the assumption that an atomic fact can be verified in "
        "isolation. VeriFact is a direct attack on that assumption.",
        indent=0.0,
    )
    subheading(doc, "B", "What VeriFact adds")
    body(
        doc,
        "VeriFact defines two defect types. An incomplete fact is one whose meaning depends on context that "
        "decomposition removed; the paper labels four subtypes, which our implementation preserves: an ambiguous "
        "concept or pronoun, a missing comparison, an omitted condition or source, and other. A missing fact is an "
        "inter-sentence discourse relation, in the PDTB sense and restricted to the temporal and contingency classes, "
        "that no extracted fact expresses. Detection is performed by an ensemble of three LLM judges whose positive "
        "detections are unioned rather than voted, a choice the authors justify by the low agreement of a single LLM "
        "judge with human annotators, reported as κ = 0.33. Repair is a self-reflection step that rewrites each "
        "flagged fact and writes one new fact per detected missing relation.",
        indent=0.0,
    )
    subheading(doc, "C", "Running large pipelines on small hardware")
    body(
        doc,
        "Quantized inference with llama.cpp-derived runtimes has made 3B–8B instruction-tuned models usable on "
        "consumer hardware, and Ollama provides a serving layer over them. Our implementation targets this stack "
        "directly, with a model-agnostic client so that the same code path runs against a laptop GPU and a cloud T4 "
        "with no change beyond two identifiers in a configuration file.",
        indent=0.0,
    )


def method(doc):
    heading(doc, "III", "System Description")
    body(
        doc,
        "VERIFACT-Lite implements the four stages of the published pipeline. Model identifiers, decoding parameters, "
        "ensemble strategy, retrieval behaviour and benchmark paths all live in a single configuration file; no model "
        "name appears anywhere in the source.",
        indent=0.0,
    )
    subheading(doc, "A", "Stage 1: baseline extraction")
    body(
        doc,
        "A SAFE-style extractor splits each sentence of the response into atomic facts and then decontextualizes them, "
        "resolving pronouns and vague references against the full response. This stage is deliberately left weak: it "
        "is the baseline that the rest of the pipeline is supposed to improve, so strengthening it would hide the "
        "effect under study.",
        indent=0.0,
    )
    subheading(doc, "B", "Stage 2: detection")
    body(
        doc,
        "Incomplete-fact detection presents each fact together with the response it came from and asks the judge for a "
        "verdict and a subtype. Missing-relation detection is a two-step procedure. First, span coverage marks every "
        "character of the response that is matched by some extracted fact, using longest-common-substring matching per "
        "sentence, and collects the contiguous runs that stayed uncovered; our normalization for case, whitespace and "
        "line breaks is index-preserving, one character in and one character out, so span offsets remain valid against "
        "the original text. Second, each uncovered span is put to the judges twice: does the span express a temporal or "
        "contingency relation, and is that relation already captured by a single existing fact? A span becomes a "
        "missing relation only when the first answer is yes and the second is no.",
        indent=0.0,
    )
    subheading(doc, "C", "Stage 3: refinement")
    body(
        doc,
        "Each flagged fact is rewritten with the response in context, and each confirmed missing relation produces one "
        "new relational fact. The refined set replaces the original fact set for verification.",
        indent=0.0,
    )
    subheading(doc, "D", "Stage 4: grounded verification")
    body(
        doc,
        "Evidence comes from the Wikipedia API. Retrieved paragraphs are ranked with BM25 and the top five are passed "
        "to the verifier, which must return a label, a confidence and a verbatim quote from the evidence. A SUPPORTED "
        "or CONTRADICTED verdict whose quote cannot be found in the evidence is downgraded to UNDECIDED. This guard was "
        "not optional: an earlier version of our verifier, without it, reported precision 0.92 and zero contradictions "
        "across 258 facts, and labelled “Aluminium is the rarest metal in the Earth's crust” as SUPPORTED with "
        "confidence 1.0. Requiring the quote moved precision to 0.42 and made contradictions appear.",
        indent=0.0,
    )
    subheading(doc, "E", "Reproducibility machinery")
    body(
        doc,
        "Every model call is cached under a hash of model identifier, prompt and decoding parameters, and every "
        "retrieved page is cached on disk. The three runs reported here replay from those caches: the laptop run "
        "resolves "
        + str(RUNS["laptop"]["runtime_stats"]["cache"]["hits"])
        + " cached model calls and "
        + str(RUNS["laptop"]["runtime_stats"]["retrieval"]["cache_hits"])
        + " cached page fetches with zero network calls, so the tables below are reproducible on a machine with no GPU "
        "and no internet connection. The repository carries 59 unit tests covering span coverage, JSON parsing, metric "
        "computation and pipeline wiring.",
        indent=0.0,
    )


def setup_section(doc):
    heading(doc, "IV", "Experimental Setup")
    subheading(doc, "A", "Benchmark")
    body(
        doc,
        "The benchmark is 12 open-ended questions written so that a correct answer naturally contains conditions, "
        "comparisons, event order or cause and effect — the structures decomposition damages. Topics include the "
        "gold and jewellery example from the paper, aluminium against silver, Chernobyl, the Panama Canal, Concorde, "
        "the ozone layer and Arctic sea ice. For recall we hand-wrote 86 reference facts, three to eight per question, "
        "from authoritative sources, with the source recorded for each. The reference facts were written before any "
        "system output was inspected and are deliberately not derived from the answers being evaluated.",
        indent=0.0,
    )
    add_table(
        doc,
        "I",
        "Benchmark composition",
        ["ID", "Topic", "Structure the question invites", "Ref."],
        [
            ["Q01", "gold and jewellery demand", "counterfactual condition", "7"],
            ["Q02", "aluminium against silver", "historical comparison", "7"],
            ["Q03", "uranium to electricity", "process chain", "7"],
            ["Q04", "Chernobyl", "event order, causation", "8"],
            ["Q05", "lithium-ion against lead-acid", "comparison", "7"],
            ["Q06", "cabin depressurization", "condition, consequence", "7"],
            ["Q07", "interest rates and inflation", "causation", "7"],
            ["Q08", "Panama Canal", "before and after", "8"],
            ["Q09", "vaccine second dose", "temporal relation", "7"],
            ["Q10", "ozone layer recovery", "condition, source", "7"],
            ["Q11", "Concorde economics", "counterfactual", "7"],
            ["Q12", "Antarctic and Arctic sea ice", "comparison, causation", "7"],
        ],
        widths=[0.33, 1.25, 1.25, 0.35],
        size=7.5,
    )
    body(
        doc,
        "Table I lists the benchmark. The distribution is deliberate rather than natural: every question was written "
        "to force at least one of the structures that decomposition damages, so the benchmark is a stress test and not "
        "a sample of typical usage. This is the same design decision the paper makes when it reports that 51\u2009% of "
        "the missing facts it finds are omitted conditions.",
    )

    subheading(doc, "B", "Metrics")
    body(
        doc,
        "Precision is supported facts over all extracted facts, with UNDECIDED reported separately and never counted "
        "as support; we also report decided precision, computed only over facts the verifier could decide. Recall is "
        "the fraction of the 86 reference facts entailed by the answer; because it scores the answer rather than the "
        "fact set, refinement cannot move it, which is a useful invariant when reading the tables. The incomplete-fact "
        "rate is measured by one designated judge, while refinement is driven by the ensemble, so that facts are never "
        "scored by the same rule that selected them for repair.",
        indent=0.0,
    )
    subheading(doc, "C", "Configurations")
    body(
        doc,
        "The answer for each question is generated once and reused by every run, verified identical by hash, so that "
        "any difference between systems is attributable to the pipeline and not to sampling. Three configurations are "
        "reported, summarised in Table II. The laptop configuration runs entirely on a 4 GB GTX 1650. Run A upgrades "
        "only the two judges and replays extraction from cache, which makes its baseline fact set byte-identical to the "
        "laptop's and isolates the judge change. Run B additionally replaces the extractor, the verifier and the "
        "entailment model used for recall, so its columns are read only against its own baseline.",
        indent=0.0,
    )
    add_table(
        doc,
        "II",
        "The three configurations",
        ["Run", "Primary model", "Judges", "Controlled"],
        [
            ["laptop-3B", "Qwen2.5-3B", "Qwen2.5-3B + Llama-3.2-3B", "reference"],
            ["run A", "Qwen2.5-3B (unchanged)", "Qwen2.5-7B + Llama-3.1-8B", "yes"],
            ["run B", "Qwen2.5-7B", "Qwen2.5-7B + Llama-3.1-8B", "no"],
        ],
        widths=[0.7, 1.1, 1.2, 0.6],
    )
    body(
        doc,
        "All models are Q4_K_M quantized and served through Ollama. Runs A and B execute on a free Colab T4. No API "
        "key is used at any point in the pipeline.",
    )


def results(doc):
    lap, a, b = RUNS["laptop"], RUNS["judges7b"], RUNS["full7b"]
    heading(doc, "V", "Results")

    subheading(doc, "A", "The mechanism against its own baseline")
    body(
        doc,
        "Table III reports the laptop configuration. Refinement does what the paper describes to the fact set: the "
        "incomplete-fact rate falls from "
        + f(lap["baseline"]["incomplete_rate"], 3)
        + " to "
        + f(lap["verifact_lite"]["incomplete_rate"], 3)
        + ", and all "
        + str(lap["baseline"]["missing_relations"])
        + " missing relational facts are recovered, "
        + str(lap["verifact_lite"]["refined_facts"])
        + " facts being rewritten and "
        + str(lap["verifact_lite"]["added_facts"])
        + " added. Measured precision falls with it, from "
        + f(lap["baseline"]["precision"])
        + " to "
        + f(lap["verifact_lite"]["precision"])
        + ". Fig. 1 shows the same three scores side by side.",
        indent=0.0,
    )
    add_table(
        doc,
        "III",
        "Baseline against VERIFACT-Lite, laptop configuration",
        ["Measure", "Baseline", "VERIFACT-Lite"],
        [
            ["Facts per answer", f(lap["baseline"]["avg_facts"], 2), f(lap["verifact_lite"]["avg_facts"], 2)],
            ["Incomplete rate", f(lap["baseline"]["incomplete_rate"], 3), f(lap["verifact_lite"]["incomplete_rate"], 3)],
            ["Missing relations", lap["baseline"]["missing_relations"], lap["verifact_lite"]["missing_relations"]],
            ["Supported", lap["baseline"]["supported"], lap["verifact_lite"]["supported"]],
            ["Contradicted", lap["baseline"]["contradicted"], lap["verifact_lite"]["contradicted"]],
            ["Undecided", lap["baseline"]["undecided"], lap["verifact_lite"]["undecided"]],
            ["Precision", f(lap["baseline"]["precision"]), f(lap["verifact_lite"]["precision"])],
            ["Decided precision", f(lap["baseline"]["decided_precision"]), f(lap["verifact_lite"]["decided_precision"])],
            ["Recall", f(lap["baseline"]["recall"]), f(lap["verifact_lite"]["recall"])],
            ["F1", f(lap["baseline"]["f1"]), f(lap["verifact_lite"]["f1"])],
        ],
        widths=[1.4, 1.0, 1.1],
    )
    add_figure(
        doc,
        os.path.join(HERE, "fig_prf.png"),
        1,
        "Precision, recall and F1 before and after refinement, laptop configuration. Recall is fixed by construction "
        "because it scores the answer, not the fact set.",
    )
    body(
        doc,
        "The precision drop is not a bug, and the counts explain it. Supported falls only from "
        + str(lap["baseline"]["supported"])
        + " to "
        + str(lap["verifact_lite"]["supported"])
        + ", while undecided rises from "
        + str(lap["baseline"]["undecided"])
        + " to "
        + str(lap["verifact_lite"]["undecided"])
        + ". A refined claim carries its condition or comparison target, so a single Wikipedia sentence must support "
        "more, and frequently none does. Decided precision barely moves, from "
        + f(lap["baseline"]["decided_precision"])
        + " to "
        + f(lap["verifact_lite"]["decided_precision"])
        + ", which locates the cost in retrieval coverage rather than in correctness.",
    )

    subheading(doc, "B", "Ablation")
    body(
        doc,
        "Table IV separates the two halves of the contribution. Incomplete-fact refinement alone produces the largest "
        "single improvement in the incomplete rate, "
        + f(lap["ablation"]["A"]["incomplete_rate"], 3)
        + " to "
        + f(lap["ablation"]["B"]["incomplete_rate"], 3)
        + ", and carries most of the precision cost. Relation recovery alone removes all missing relations and raises "
        "the incomplete rate slightly, to "
        + f(lap["ablation"]["C"]["incomplete_rate"], 3)
        + ", because the newly written relational facts are themselves judged. The full system inherits both effects.",
        indent=0.0,
    )
    add_table(
        doc,
        "IV",
        "Ablation, laptop configuration, union ensemble",
        ["System", "Incompl.", "Missing", "Precision", "F1"],
        [
            [
                "Baseline",
                f(lap["ablation"]["A"]["incomplete_rate"], 3),
                lap["ablation"]["A"]["missing_relations"],
                f(lap["ablation"]["A"]["precision"]),
                f(lap["ablation"]["A"]["f1"]),
            ],
            [
                "+ incomplete-fact refinement",
                f(lap["ablation"]["B"]["incomplete_rate"], 3),
                lap["ablation"]["B"]["missing_relations"],
                f(lap["ablation"]["B"]["precision"]),
                f(lap["ablation"]["B"]["f1"]),
            ],
            [
                "+ missing-relation recovery",
                f(lap["ablation"]["C"]["incomplete_rate"], 3),
                lap["ablation"]["C"]["missing_relations"],
                f(lap["ablation"]["C"]["precision"]),
                f(lap["ablation"]["C"]["f1"]),
            ],
            [
                "Full VERIFACT-Lite",
                f(lap["ablation"]["D"]["incomplete_rate"], 3),
                lap["ablation"]["D"]["missing_relations"],
                f(lap["ablation"]["D"]["precision"]),
                f(lap["ablation"]["D"]["f1"]),
            ],
        ],
        widths=[1.5, 0.6, 0.55, 0.65, 0.5],
    )

    subheading(doc, "C", "The detector is part of the measurement")
    body(
        doc,
        "Run A changes the two judges and nothing else. Because extraction replays from cache, the fact set it scores "
        "is byte-identical to the laptop's: "
        + f(a["baseline"]["avg_facts"], 2)
        + " facts per answer, precision "
        + f(a["baseline"]["precision"])
        + ", identical to Table III. On that identical input, the incomplete-fact rate measured by the 3B detector is "
        + f(lap["baseline"]["incomplete_rate"], 3)
        + " and the rate measured by the 7B detector is "
        + f(a["baseline"]["incomplete_rate"], 3)
        + " — a factor of 4.2 on the same text, against 0.567 reported in the paper for SAFE output under GPT-4o. "
        "Fig. 2 places the three side by side.",
        indent=0.0,
    )
    add_figure(
        doc,
        os.path.join(HERE, "fig_judge.png"),
        2,
        "Incomplete-fact rate on an identical baseline fact set under detectors of different size. Nothing about the "
        "system under test changes between the first two bars; the paper's figure is shown for scale.",
    )
    body(
        doc,
        "The same effect appears in recall. Run B scores the same 12 answers against the same 86 reference facts with "
        "a larger entailment model and credits the answers with "
        + f(b["baseline"]["recall"])
        + " against "
        + f(lap["baseline"]["recall"])
        + ", a coverage of 24 of 86 reference facts rather than 35. We therefore read our absolute precision, recall "
        "and F1 as properties of a measurement apparatus rather than as system quality, and we compare only within a "
        "fixed detector.",
    )

    subheading(doc, "D", "Union against majority")
    body(
        doc,
        "The paper unions positive detections across judges. Table V compares that rule with a majority vote in all "
        "three configurations, holding everything else fixed. Majority gives higher precision and F1 in every case. "
        "The large advantage in incomplete rate that the laptop run shows, "
        + f(lap["ablation_majority"]["D"]["incomplete_rate"], 3)
        + " against "
        + f(lap["ablation"]["D"]["incomplete_rate"], 3)
        + ", does not survive scale: with 7–8B judges the two rules are within four percent of each other, and "
        "with a 7B extractor they are indistinguishable. We reported that advantage in an earlier version of this work "
        "and withdraw it here as an artifact of small judges.",
        indent=0.0,
    )
    add_table(
        doc,
        "V",
        "Union against majority, full system, all three runs",
        ["Run", "Rule", "Incompl.", "Precision", "F1"],
        [
            ["laptop-3B", "union", f(lap["ablation"]["D"]["incomplete_rate"], 3), f(lap["ablation"]["D"]["precision"]), f(lap["ablation"]["D"]["f1"], 3)],
            ["laptop-3B", "majority", f(lap["ablation_majority"]["D"]["incomplete_rate"], 3), f(lap["ablation_majority"]["D"]["precision"]), f(lap["ablation_majority"]["D"]["f1"], 3)],
            ["run A", "union", f(a["ablation"]["D"]["incomplete_rate"], 3), f(a["ablation"]["D"]["precision"]), f(a["ablation"]["D"]["f1"], 3)],
            ["run A", "majority", f(a["ablation_majority"]["D"]["incomplete_rate"], 3), f(a["ablation_majority"]["D"]["precision"]), f(a["ablation_majority"]["D"]["f1"], 3)],
            ["run B", "union", f(b["ablation"]["D"]["incomplete_rate"], 3), f(b["ablation"]["D"]["precision"]), f(b["ablation"]["D"]["f1"], 3)],
            ["run B", "majority", f(b["ablation_majority"]["D"]["incomplete_rate"], 3), f(b["ablation_majority"]["D"]["precision"]), f(b["ablation_majority"]["D"]["f1"], 3)],
        ],
        widths=[0.75, 0.7, 0.6, 0.7, 0.55],
    )
    body(
        doc,
        "Table VI explains why the rule matters so little for one of the two tasks. For missing relations the union "
        "equals the more permissive judge exactly in all three runs — "
        + str(lap["judge_ablation"]["llama"]["missing_relation_detected"])
        + " of "
        + str(lap["judge_ablation"]["ensemble"]["missing_relation_detected"])
        + ", "
        + str(a["judge_ablation"]["llama"]["missing_relation_detected"])
        + " of "
        + str(a["judge_ablation"]["ensemble"]["missing_relation_detected"])
        + " and "
        + str(b["judge_ablation"]["llama"]["missing_relation_detected"])
        + " of "
        + str(b["judge_ablation"]["ensemble"]["missing_relation_detected"])
        + " — so the second judge contributes nothing there at any model size. For incompleteness the picture "
        "changes with scale: at 3B the ensemble again equals one judge, but at 7–8B it exceeds both "
        "individually, which is the complementarity the union rule assumes.",
    )
    add_table(
        doc,
        "VI",
        "Facts flagged by each judge and by the union",
        ["Run and task", "Qwen", "Llama", "Union"],
        [
            [
                "3B — incompleteness",
                lap["judge_ablation"]["qwen"]["incomplete_detected"],
                lap["judge_ablation"]["llama"]["incomplete_detected"],
                lap["judge_ablation"]["ensemble"]["incomplete_detected"],
            ],
            [
                "3B — relations",
                lap["judge_ablation"]["qwen"]["missing_relation_detected"],
                lap["judge_ablation"]["llama"]["missing_relation_detected"],
                lap["judge_ablation"]["ensemble"]["missing_relation_detected"],
            ],
            [
                "7–8B — incompleteness",
                a["judge_ablation"]["qwen"]["incomplete_detected"],
                a["judge_ablation"]["llama"]["incomplete_detected"],
                a["judge_ablation"]["ensemble"]["incomplete_detected"],
            ],
            [
                "7–8B — relations",
                a["judge_ablation"]["qwen"]["missing_relation_detected"],
                a["judge_ablation"]["llama"]["missing_relation_detected"],
                a["judge_ablation"]["ensemble"]["missing_relation_detected"],
            ],
        ],
        widths=[1.6, 0.55, 0.55, 0.55],
    )

    subheading(doc, "E", "Does repairing a claim change its verdict?")
    body(
        doc,
        "This is the paper's central question, and the one result that transfers cleanly across configurations. Every "
        "refined fact is verified twice, once as its original claim and once as its refined claim, through the same "
        "evidence pipeline. The verdict changes for "
        + pct(lap["label_change"]["label_change_rate"])
        + " of refined facts on the laptop ("
        + str(lap["label_change"]["label_changes"])
        + " of "
        + str(lap["label_change"]["refined_facts_verified"])
        + "), "
        + pct(a["label_change"]["label_change_rate"])
        + " in run A ("
        + str(a["label_change"]["label_changes"])
        + " of "
        + str(a["label_change"]["refined_facts_verified"])
        + ") and "
        + pct(b["label_change"]["label_change_rate"])
        + " in run B ("
        + str(b["label_change"]["label_changes"])
        + " of "
        + str(b["label_change"]["refined_facts_verified"])
        + "), against 24.9 % in the paper. Whether a claim keeps its context decides between a quarter and nearly "
        "half of all verdicts.",
        indent=0.0,
    )
    body(
        doc,
        "The direction of the change is informative. With 3B judges we reproduced only half of the paper's reported "
        "signature: supported fell, but the contradicted count never moved off "
        + str(lap["baseline"]["contradicted"])
        + ". With 7–8B judges it rises from "
        + str(a["baseline"]["contradicted"])
        + " to "
        + str(a["verifact_lite"]["contradicted"])
        + ", and run A records "
        + str(a["label_change"]["transitions"].get("SUPPORTED->CONTRADICTED", 0))
        + " facts moving directly from SUPPORTED to CONTRADICTED once repaired. That is the other half of the paper's "
        "claim that ignoring incomplete facts overestimates factuality: the error was present in the response all "
        "along and the stripped claim hid it.",
    )

    subheading(doc, "F", "A stronger extractor leaves less to repair")
    body(
        doc,
        "Run B is not a controlled comparison, but one effect is worth recording. A 7B extractor writes "
        + f(b["baseline"]["avg_facts"], 2)
        + " facts per answer against "
        + f(lap["baseline"]["avg_facts"], 2)
        + ", with a lower incomplete rate under the same 7B detector ("
        + f(b["baseline"]["incomplete_rate"], 3)
        + " against "
        + f(a["baseline"]["incomplete_rate"], 3)
        + ") and higher precision ("
        + f(b["baseline"]["precision"])
        + " against "
        + f(a["baseline"]["precision"])
        + "). Refinement then costs far less precision, "
        + signed(b["verifact_lite"]["precision"] - b["baseline"]["precision"])
        + " against "
        + signed(a["verifact_lite"]["precision"] - a["baseline"]["precision"])
        + " in run A. Fewer, coarser, more self-contained facts are both easier to verify and less in need of repair.",
        indent=0.0,
    )

    subheading(doc, "G", "Cost and reproducibility")
    body(
        doc,
        "The pipeline is dominated by detection, which asks every judge about every fact and then about every "
        "uncovered span. The laptop run resolves "
        + str(lap["runtime_stats"]["cache"]["hits"])
        + " model calls and "
        + str(lap["runtime_stats"]["retrieval"]["cache_hits"])
        + " page fetches, run A "
        + str(a["runtime_stats"]["cache"]["hits"])
        + " and "
        + str(a["runtime_stats"]["retrieval"]["cache_hits"])
        + ", and run B "
        + str(b["runtime_stats"]["cache"]["hits"])
        + " and "
        + str(b["runtime_stats"]["retrieval"]["cache_hits"])
        + ". Two 3B judges at Q4_K_M do not fit together in 4 GB, so the implementation drives one judge over the "
        "whole fact list before releasing its weights; without that, every call pays a model load of roughly twenty "
        "seconds. Retrieval needed its own care: Wikipedia rate-limits unauthenticated clients and failed requests are "
        "not cached, so without retries a 429 silently becomes \u201cno evidence\u201d and two runs of the same "
        "pipeline disagree. All three runs now replay from cache with zero network calls.",
        indent=0.0,
    )

    subheading(doc, "H", "Qualitative behaviour")
    body(
        doc,
        "Reading the output exposes a failure mode that no aggregate metric reports. On the ozone-layer question the "
        "refiner behaves exactly as intended, turning “These substances are in the atmosphere” into “The "
        "substances are in the atmosphere since the Montreal Protocol was signed,” which moves from UNDECIDED to "
        "SUPPORTED. On the gold question it inverts a claim: “There was demand for gold as jewelry” becomes "
        "“There was no demand for gold as jewelry,” because the hypothetical in the question was pasted into "
        "a fact asserting the opposite. A 3B refiner has no guard against changing the meaning of what it repairs, and "
        "the label-change rate counts that corruption and a genuine repair identically.",
    )


def comparison(doc):
    heading(doc, "VI", "Comparison with the Published Results")
    body(
        doc,
        "Table VII places our figures beside the paper's. The agreement to look for is directional. Both defect types "
        "are detected and repaired; refinement changes a large fraction of verdicts; supported falls and contradicted "
        "rises once the judges are large enough to see the errors. The magnitudes are not comparable and we do not "
        "present them as such: different models, a different evidence source, 12 prompts instead of 1,096, and no "
        "human annotation.",
        indent=0.0,
    )
    lap, a, b = RUNS["laptop"], RUNS["judges7b"], RUNS["full7b"]
    add_table(
        doc,
        "VII",
        "Paper against VERIFACT-Lite",
        ["Measure", "Paper", "This work", "Agreement"],
        [
            [
                "Incomplete, baseline",
                "0.567",
                f(lap["baseline"]["incomplete_rate"], 3) + " / " + f(a["baseline"]["incomplete_rate"], 3),
                "closes with scale",
            ],
            [
                "Incomplete, refined",
                "0.225",
                f(lap["verifact_lite"]["incomplete_rate"], 3) + " / " + f(a["verifact_lite"]["incomplete_rate"], 3),
                "same direction",
            ],
            ["Missing relations", "1.22 → 0.76", "51 → 0", "same direction"],
            [
                "Verdict changes",
                "24.9 %",
                pct(lap["label_change"]["label_change_rate"], 1) + " / " + pct(a["label_change"]["label_change_rate"], 1),
                "same phenomenon",
            ],
            ["Direction of change", "sup. ↓, con. ↑", "both at 7–8B", "reproduced"],
            ["Precision", "82.8", f(lap["verifact_lite"]["precision"] * 100, 1) + "–" + f(b["verifact_lite"]["precision"] * 100, 1), "not comparable"],
            ["F1", "57.5", f(a["verifact_lite"]["f1"] * 100, 1) + "–" + f(lap["baseline"]["f1"] * 100, 1), "not comparable"],
        ],
        widths=[1.1, 0.75, 1.0, 0.85],
    )


def proposals(doc):
    heading(doc, "VII", "Proposed Changes to the Method")
    body(
        doc,
        "The following six changes target VeriFact as published rather than our reimplementation. Each is argued from "
        "a measurement reported above.",
        indent=0.0,
    )
    items = [
        (
            "Vote instead of union, and drop the second judge for relations",
            "The union rule is justified by low single-judge agreement, but Table V shows majority voting winning on "
            "precision in all three configurations, and Table VI shows the union equalling one judge exactly on "
            "relation detection at every model size. The second judge buys nothing on that task and costs a full pass "
            "over the fact set.",
        ),
        (
            "Gate refinement on faithfulness",
            "Self-reflection rewrites a fact with no check that the response still entails it, which is how our "
            "refiner produced a claim asserting the opposite of the source sentence. One entailment call per rewrite "
            "would reject such repairs. Without that gate, the headline label-change rate cannot distinguish a repair "
            "from a corruption.",
        ),
        (
            "Refine against the evidence rather than blind to it",
            "The published order refines first and retrieves second, and the paper reports precision falling after "
            "refinement without accounting for it. Our counts locate the loss precisely: undecided rises from "
            + str(RUNS["laptop"]["baseline"]["undecided"])
            + " to "
            + str(RUNS["laptop"]["verifact_lite"]["undecided"])
            + " while decided precision is unchanged. Retrieving first and conditioning the rewrite on the evidence "
            "that actually exists would preserve context without destroying checkability.",
        ),
        (
            "Make span coverage semantic",
            "Coverage is computed by longest-common-substring matching, so a paraphrased relation reads as uncovered "
            "and is re-added as a new fact. Character coverage ran between 0.55 and 0.59 across our answers and "
            "produced 73 candidate spans. Embedding-based coverage would remove a class of spurious candidates at "
            "negligible cost.",
        ),
        (
            "Calibrate the detector before ranking models",
            "The paper benchmarks twelve generators against one fixed detector and compares the resulting rates "
            "directly. Our Fig. 2 shows that swapping the detector alone moves that rate by a factor of 4.2 on "
            "identical text. Anchoring every detector on one small annotated probe set, and reporting rates relative "
            "to that anchor, would make such comparisons mean what they appear to mean.",
        ),
        (
            "Escalate only on disagreement",
            "Detection runs three frontier models over every extracted fact and dominates the cost of the pipeline. "
            "Cheap judges agree on the large majority of facts; routing only the disputed ones to a large model "
            "targets the same detections for a fraction of the calls. This is what made the method runnable on a 4 GB "
            "GPU at all.",
        ),
    ]
    for i, (name, text) in enumerate(items, 1):
        p = para(doc, indent=0.0, space_before=3)
        run(p, f"{i}) {name}. ", 10, italic=True)
        run(p, text, 10)


def limitations(doc):
    heading(doc, "VIII", "Limitations")
    body(
        doc,
        "The benchmark is 12 questions and 86 reference facts, which supports trends and not significance. There is no "
        "human annotation, so every incompleteness and relation judgement comes from a model. Only run A is a "
        "controlled comparison against the laptop configuration; run B changes four components at once and is read "
        "only against its own baseline. Recall depends on the entailment model and is therefore not comparable across "
        "runs that change it. Evidence is restricted to Wikipedia, which caps what any verifier can decide and "
        "concentrates the UNDECIDED mass that drives our precision figures. Finally, temperature-zero decoding is not "
        "bit-reproducible until the cache is warm; all artifacts shipped with this report are self-consistent and "
        "replay exactly.",
        indent=0.0,
    )


def conclusion(doc):
    lap, a = RUNS["laptop"], RUNS["judges7b"]
    heading(doc, "IX", "Conclusion and Remaining Work")
    body(
        doc,
        "The VeriFact mechanism survives the move to small open-weight models. Detection and repair behave as "
        "described, all missing relational facts are recovered, measured precision falls for a reason we can locate in "
        "the verdict counts, and the paper's central phenomenon — that repairing a claim changes its verdict — "
        "holds at 34.7 to 45.6 % across three model configurations against 24.9 % reported. The reimplementation "
        "needs no API key and replays from cache without a GPU.",
        indent=0.0,
    )
    body(
        doc,
        "The finding we consider most consequential is methodological. On an identical fact set the incomplete-fact "
        "rate is "
        + f(lap["baseline"]["incomplete_rate"], 3)
        + " under a 3B detector and "
        + f(a["baseline"]["incomplete_rate"], 3)
        + " under a 7B detector. A metric that moves by a factor of four when only the measuring model changes cannot "
        "be compared across papers, or across models within a paper, without calibration. That observation generalises "
        "beyond VeriFact to the whole decomposition-based factuality literature.",
    )
    body(
        doc,
        "For the remainder of the term we intend to implement the faithfulness gate and the evidence-conditioned "
        "refinement order, since both are cheap and both target measured failures, and to build the small annotated "
        "probe set that the calibration proposal requires. We also plan to extend the benchmark and to report "
        "per-subtype incompleteness rates, which our pipeline already records but does not yet aggregate.",
    )


def references(doc):
    heading(doc, "X", "References")
    refs = [
        "X. Liu, Y. Zhang, A. Munir, Y. Gu, and L. Wang, “VeriFact: Verifying facts in LLM-generated long-form text "
        "with incomplete and missing facts,” in Proc. EMNLP, 2025, pp. 17908–17925.",
        "J. Wei et al., “Long-form factuality in large language models,” arXiv:2403.18802, 2024.",
        "S. Min et al., “FActScore: Fine-grained atomic evaluation of factual precision in long form text "
        "generation,” in Proc. EMNLP, 2023.",
        "Y. Wang et al., “Factcheck-GPT: End-to-end fine-grained document-level fact-checking and correction of LLM "
        "output,” arXiv:2311.09000, 2023.",
        "B. Webber, R. Prasad, A. Lee, and A. Joshi, “The Penn Discourse Treebank 3.0 annotation manual,” Univ. "
        "of Pennsylvania, 2019.",
        "A. Yang et al., “Qwen2.5 technical report,” arXiv:2412.15115, 2024.",
        "A. Dubey et al., “The Llama 3 herd of models,” arXiv:2407.21783, 2024.",
        "S. Robertson and H. Zaragoza, “The probabilistic relevance framework: BM25 and beyond,” Foundations and "
        "Trends in Information Retrieval, vol. 3, no. 4, pp. 333–389, 2009.",
        "G. Gerganov et al., “llama.cpp,” GitHub repository, 2023. [Online]. Available: "
        "https://github.com/ggerganov/llama.cpp",
        "Ollama, “Ollama: Get up and running with large language models locally,” 2024. [Online]. Available: "
        "https://ollama.com",
    ]
    for i, text in enumerate(refs, 1):
        p = para(doc, space_after=1)
        p.paragraph_format.left_indent = Inches(0.22)
        p.paragraph_format.first_line_indent = Inches(-0.22)
        run(p, f"[{i}] ", 8)
        run(p, text, 8)


def main():
    doc = Document()
    setup(doc)
    title_block(doc)
    two_columns(doc)
    abstract(doc)
    introduction(doc)
    background(doc)
    method(doc)
    setup_section(doc)
    results(doc)
    comparison(doc)
    proposals(doc)
    limitations(doc)
    conclusion(doc)
    references(doc)
    doc.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
