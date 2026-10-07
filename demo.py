"""Single-example walkthrough of the VERIFACT-Lite pipeline.

    python demo.py                      # the paper's gold/jewelry example
    python demo.py --question "..." --answer "..."
    python demo.py --qid Q03             # a question from data/challenge_set.jsonl
    python demo.py --no-verify           # stop after refinement (no retrieval)

Prints each stage so the baseline-vs-refined difference is visible end to end.
"""

from __future__ import annotations

import argparse
import textwrap

from src.pipeline import VerifactLitePipeline
from src.refinement import assemble_final_facts
from src.utils import load_config, read_jsonl, resolve_path
from src.word_mapping import coverage_ratio, find_missing_spans

# The example from Figure 1 of the paper, used as the default walkthrough.
PAPER_QUESTION = (
    "If there wasn't a demand for gold as jewelry, would its price drop enough to "
    "make it usable in consumer electronics?"
)
PAPER_ANSWER = (
    "If the demand for gold as jewelry were to disappear, the price of gold could drop by "
    "20-50% or more, making it more competitive with other materials like copper and silver."
)


def rule(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


def wrap(text: str, indent: str = "  ") -> str:
    return textwrap.fill(text, width=76, initial_indent=indent, subsequent_indent=indent)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run VERIFACT-Lite on one example.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--question", default=None)
    parser.add_argument("--answer", default=None, help="skip generation and evaluate this answer")
    parser.add_argument("--qid", default=None, help="question id from the challenge set")
    parser.add_argument("--no-verify", action="store_true", help="skip retrieval and verification")
    args = parser.parse_args()

    cfg = load_config(args.config)
    pipeline = VerifactLitePipeline(cfg, verbose=False)

    question = args.question
    answer = args.answer
    reference_facts: list[str] = []
    qid = args.qid or "DEMO"

    if args.qid:
        rows = read_jsonl(resolve_path(cfg, cfg["paths"]["challenge_set"]))
        match = next((r for r in rows if r["id"] == args.qid), None)
        if match is None:
            raise SystemExit(f"question id {args.qid} not found in the challenge set")
        question = match["question"]
        refs = {
            r["id"]: r.get("reference_facts", [])
            for r in read_jsonl(resolve_path(cfg, cfg["paths"]["mini_reference"]))
        }
        reference_facts = refs.get(args.qid, [])
    elif question is None:
        question, answer = PAPER_QUESTION, PAPER_ANSWER

    rule("QUESTION")
    print(wrap(question))

    if answer is None:
        print("\n  generating the answer once with the local model ...")
        answer = pipeline.generate_answer(question)
    rule("ORIGINAL ANSWER (generated once, shared by both pipelines)")
    print(wrap(answer))

    # STEP 1 ---------------------------------------------------------------
    facts, grouped = pipeline.extractor.extract(question, answer)
    rule(f"STEP 1 - BASELINE FACTS ({len(facts)})")
    for fact in facts:
        print(f"  {fact.id}: {fact.text}")

    # STEP 2A --------------------------------------------------------------
    detections = pipeline.completeness.run(question, answer, facts)
    incomplete = [d for d in detections if d["ensemble"]]
    rule(f"STEP 2A - INCOMPLETE FACT DETECTION ({len(incomplete)} flagged)")
    print(f"  judges: {', '.join(pipeline.completeness.judge_aliases)}"
          f"   ensemble: {pipeline.completeness.strategy}")
    for record in detections:
        votes = " ".join(f"{a}={'Y' if v else 'n'}" for a, v in record["judges"].items())
        flag = "INCOMPLETE" if record["ensemble"] else "complete  "
        print(f"  {record['fact_id']:<4} {flag} [{votes}] {record['type'] or '-'}")
        if record["ensemble"] and record["reason"]:
            print(wrap(f"reason: {record['reason']}", indent="        "))

    # STEP 2B --------------------------------------------------------------
    wm = cfg.get("word_mapping") or {}
    spans = find_missing_spans(
        answer,
        [f.text for f in facts],
        sentence_facts=grouped,
        min_chars=int(wm.get("min_span_chars", 12)),
        min_words=int(wm.get("min_span_words", 3)),
    )
    rule(f"STEP 2B - WORD MAPPING ({len(spans)} uncovered spans)")
    print(f"  character coverage of the answer: {coverage_ratio(answer, [f.text for f in facts]):.2%}")
    for span in spans:
        print(f"  [{span.start}:{span.end}] {span.text!r}")

    # STEP 2C --------------------------------------------------------------
    relations = pipeline.relations.run(answer, spans, facts)
    missing = [r for r in relations if r["is_missing_relation"]]
    rule(f"STEP 2C - MISSING RELATION DETECTION ({len(missing)} missing)")
    for record in relations:
        votes = " ".join(f"{a}={'Y' if v else 'n'}" for a, v in (record["judges"] or {}).items())
        verdict = "MISSING" if record["is_missing_relation"] else "ok     "
        print(f"  {verdict} {record['relation_type']:<12} [{votes}] covered={record['already_covered']}")
        print(wrap(f"span: {record['span']!r}", indent="        "))

    # STEP 3 ---------------------------------------------------------------
    refinements = [pipeline.refiner.refine_fact(question, answer, f) for f in facts if f.incomplete]
    rule(f"STEP 3 - REFINEMENT ({sum(1 for r in refinements if r['status'] == 'refined')} refined)")
    for record in refinements:
        print(f"  {record['fact_id']} [{record['status']}] ({record['error_type']})")
        print(wrap(f"before: {record['original']}", indent="        "))
        print(wrap(f"after:  {record['refined']}", indent="        "))

    # STEP 3B --------------------------------------------------------------
    added = []
    for i, record in enumerate(missing, start=1):
        new_fact = pipeline.refiner.add_relation_fact(question, answer, record, facts, f"M{i}")
        if new_fact:
            added.append(new_fact)
    rule(f"STEP 3B - ADDED RELATIONAL FACTS ({len(added)})")
    for fact in added:
        print(f"  {fact['fact_id']} [{fact['relation_type']}] {fact['text']}")

    final = assemble_final_facts(facts, refinements, added)
    rule(f"FINAL REFINED FACT SET ({len(final)})")
    for fact in final:
        print(f"  {fact.id:<4} [{fact.status:<9}] {fact.text}")

    if args.no_verify:
        print("\n(skipping retrieval and verification: --no-verify)")
        return

    # STEP 4 ---------------------------------------------------------------
    rule("STEP 4 - EVIDENCE RETRIEVAL AND VERIFICATION")
    for fact in final:
        result = pipeline.verify_claim(fact.text)
        print(f"\n  {fact.id} [{fact.status}] {fact.text}")
        print(f"    label      : {result['label']} (confidence {result['confidence']:.2f})")
        print(f"    queries    : {result['queries']}")
        print(f"    evidence   : {result['evidence_ids']}")
        for ev in result["evidence"][:2]:
            print(wrap(f"[{ev['id']}] {ev['title']}: {ev['snippet'][:180]}...", indent="      "))
        print(wrap(f"reason: {result['reason']}", indent="    "))

    # Before vs after ------------------------------------------------------
    changed = []
    for record in refinements:
        if record["status"] != "refined":
            continue
        before = pipeline.verify_claim(record["original"])["label"]
        after = pipeline.verify_claim(record["refined"])["label"]
        changed.append((record, before, after))
    if changed:
        rule("BEFORE VS AFTER VERIFICATION OF REFINED FACTS")
        for record, before, after in changed:
            mark = "CHANGED" if before != after else "same   "
            print(f"  {mark} {record['fact_id']}: {before} -> {after}")
            print(wrap(f"before: {record['original']}", indent="        "))
            print(wrap(f"after:  {record['refined']}", indent="        "))

    if reference_facts:
        rule("RECALL AGAINST THE MINI REFERENCE BENCHMARK")
        covered = 0
        for ref in reference_facts:
            result = pipeline.recall_checker.check(ref, answer)
            covered += bool(result["covered"])
            print(f"  {'COVERED' if result['covered'] else 'missing'} (sim {result['similarity']:.2f}) {ref}")
        print(f"\n  recall = {covered}/{len(reference_facts)} = {covered / len(reference_facts):.3f}")

    rule("RUNTIME")
    stats = pipeline.stats()
    print(f"  cache      : {stats['cache']}")
    print(f"  retrieval  : {stats['retrieval']}")
    for judge in stats["judges"]:
        print(f"  judge {judge['alias']:<6}: {judge['calls']} calls, {judge['total_latency_s']}s")


if __name__ == "__main__":
    main()
