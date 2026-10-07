"""Minimal Streamlit interface for VERIFACT-Lite.

    streamlit run app.py

The pipeline is the product; this UI is deliberately thin.
"""

from __future__ import annotations

import streamlit as st

from src.pipeline import VerifactLitePipeline
from src.refinement import assemble_final_facts
from src.utils import load_config, read_jsonl, resolve_path
from src.word_mapping import coverage_ratio, find_missing_spans

st.set_page_config(page_title="VERIFACT-Lite", layout="wide")


@st.cache_resource(show_spinner="loading local models ...")
def get_pipeline():
    cfg = load_config()
    return cfg, VerifactLitePipeline(cfg, verbose=False)


cfg, pipeline = get_pipeline()

st.title("VERIFACT-Lite")
st.caption(
    "A resource-constrained reimplementation of the core VERIFACT methodology "
    "(Liu et al., EMNLP 2025) using open-source, locally hosted models. "
    "Not a reproduction of the paper's reported numbers."
)

with st.sidebar:
    st.subheader("Configuration")
    st.write(f"**Primary model**: `{cfg['model']['model_id']}`")
    st.write(f"**Backend**: `{cfg['model']['backend']}`")
    st.write("**Judges**")
    for judge in pipeline.judges:
        st.write(f"- `{judge.model_id}` ({judge.alias})")
    st.write(f"**Ensemble**: {pipeline.completeness.strategy}")
    st.write(f"**Evidence**: {cfg['retrieval']['source']} + {cfg['retrieval']['ranker'].upper()}")
    run_verification = st.checkbox("Run retrieval + verification", value=True)
    st.caption("Verification queries Wikipedia and is the slowest stage.")

try:
    rows = read_jsonl(resolve_path(cfg, cfg["paths"]["challenge_set"]))
except Exception:
    rows = []
presets = {f"{r['id']}: {r['question'][:70]}": r["question"] for r in rows}

choice = st.selectbox("Example question (optional)", ["(custom)"] + list(presets))
default_q = presets.get(choice, "")
question = st.text_area("Question", value=default_q, height=70)
answer = st.text_area(
    "Answer (leave empty to generate once with the local model)", value="", height=140
)

if st.button("Run Evaluation", type="primary"):
    if not question.strip():
        st.error("enter a question")
        st.stop()

    if not answer.strip():
        with st.spinner("generating the answer once ..."):
            answer = pipeline.generate_answer(question)
    st.subheader("Answer under evaluation")
    st.info(answer)

    with st.spinner("STEP 1: baseline fact extraction ..."):
        facts, grouped = pipeline.extractor.extract(question, answer)

    st.subheader(f"Baseline facts ({len(facts)})")
    st.table([{"id": f.id, "fact": f.text} for f in facts])

    with st.spinner("STEP 2A: incomplete fact detection ..."):
        detections = pipeline.completeness.run(question, answer, facts)

    with st.spinner("STEP 2B/2C: word mapping and missing relation detection ..."):
        wm = cfg.get("word_mapping") or {}
        spans = find_missing_spans(
            answer,
            [f.text for f in facts],
            sentence_facts=grouped,
            min_chars=int(wm.get("min_span_chars", 12)),
            min_words=int(wm.get("min_span_words", 3)),
        )
        relations = pipeline.relations.run(answer, spans, facts)

    missing = [r for r in relations if r["is_missing_relation"]]
    st.subheader("Detected problems")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Incomplete facts**")
        flagged = [
            {
                "id": d["fact_id"],
                "type": d["type"],
                **{f"judge:{a}": ("yes" if v else "no") for a, v in d["judges"].items()},
                "reason": d["reason"],
            }
            for d in detections
            if d["ensemble"]
        ]
        st.table(flagged or [{"id": "-", "type": "none detected"}])
    with col2:
        st.markdown(
            f"**Uncovered spans** ({len(spans)}, character coverage "
            f"{coverage_ratio(answer, [f.text for f in facts]):.0%})"
        )
        st.table(
            [
                {
                    "span": r["span"],
                    "relation": r["relation_type"],
                    "already_covered": r["already_covered"],
                    "missing": r["is_missing_relation"],
                }
                for r in relations
            ]
            or [{"span": "-", "relation": "none"}]
        )

    with st.spinner("STEP 3: refinement ..."):
        refinements = [
            pipeline.refiner.refine_fact(question, answer, f) for f in facts if f.incomplete
        ]
        added = []
        for i, record in enumerate(missing, start=1):
            new_fact = pipeline.refiner.add_relation_fact(question, answer, record, facts, f"M{i}")
            if new_fact:
                added.append(new_fact)

    st.subheader("Refined facts")
    if refinements:
        st.table(
            [
                {
                    "id": r["fact_id"],
                    "status": r["status"],
                    "type": r["error_type"],
                    "before": r["original"],
                    "after": r["refined"],
                }
                for r in refinements
            ]
        )
    else:
        st.write("no incomplete facts were flagged")

    if added:
        st.markdown("**Added relational facts**")
        st.table([{"id": a["fact_id"], "relation": a["relation_type"], "fact": a["text"]} for a in added])

    final = assemble_final_facts(facts, refinements, added)
    st.subheader(f"Final fact set ({len(final)})")
    st.table([{"id": f.id, "status": f.status, "fact": f.text} for f in final])

    if not run_verification:
        st.stop()

    rows_v = []
    progress = st.progress(0.0, text="STEP 4: retrieval and verification ...")
    for i, fact in enumerate(final, start=1):
        result = pipeline.verify_claim(fact.text)
        rows_v.append(
            {
                "id": fact.id,
                "status": fact.status,
                "claim": fact.text,
                "label": result["label"],
                "confidence": round(result["confidence"], 2),
                "evidence": ", ".join(result["evidence_ids"]),
            }
        )
        progress.progress(i / max(len(final), 1), text=f"verified {i}/{len(final)}")
    progress.empty()

    st.subheader("Verification")
    st.table(rows_v)

    st.subheader("Evidence")
    for fact in final[:5]:
        result = pipeline.verify_claim(fact.text)
        with st.expander(f"{fact.id} - {fact.text[:80]}"):
            st.write(f"queries: {result['queries']}")
            for ev in result["evidence"]:
                st.markdown(f"**[{ev['id']}] [{ev['title']}]({ev['url']})**")
                st.write(ev["snippet"][:600])

    labels = [r["label"] for r in rows_v]
    supported = sum(1 for l in labels if l == "SUPPORTED")
    precision = supported / len(labels) if labels else 0.0

    refs = {
        r["id"]: r.get("reference_facts", [])
        for r in read_jsonl(resolve_path(cfg, cfg["paths"]["mini_reference"]))
    }
    matched_id = next((r["id"] for r in rows if r["question"] == question), None)
    reference_facts = refs.get(matched_id, []) if matched_id else []
    recall = 0.0
    if reference_facts:
        with st.spinner("computing recall against the mini reference benchmark ..."):
            covered = sum(
                1 for ref in reference_facts if pipeline.recall_checker.check(ref, answer)["covered"]
            )
        recall = covered / len(reference_facts)

    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    st.subheader("Metrics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precision", f"{precision:.3f}")
    m2.metric("Recall", f"{recall:.3f}" if reference_facts else "n/a")
    m3.metric("F1", f"{f1:.3f}" if reference_facts else "n/a")
    m4.metric("Undecided", sum(1 for l in labels if l == "UNDECIDED"))
    if not reference_facts:
        st.caption(
            "Recall needs reference facts. Pick a question from the challenge set to get them."
        )
