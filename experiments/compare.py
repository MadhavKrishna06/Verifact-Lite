"""Build the presentation outputs from the saved runs.

Reads outputs/baseline.json, outputs/verifact.json and (when present)
outputs/ablation.json, then writes:

    outputs/comparison.csv
    outputs/summary.json
    outputs/methodology_table.md
    outputs/examples/presentation_examples.json
    outputs/examples/centerpiece.md
    outputs/charts/*.png              (when matplotlib is installed)

    python -m experiments.compare
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.metrics import improvement
from src.utils import load_config, read_json, resolve_path, write_json

METRIC_ROWS = [
    ("questions", "questions", "int"),
    ("avg_facts_per_answer", "avg_facts", "float"),
    ("incomplete_facts", "incomplete_facts", "int"),
    ("incomplete_fact_rate", "incomplete_rate", "float"),
    ("missing_relations", "missing_relations", "int"),
    ("candidate_spans", "candidate_spans", "int"),
    ("refined_facts", "refined_facts", "int"),
    ("added_facts", "added_facts", "int"),
    ("supported", "supported", "int"),
    ("contradicted", "contradicted", "int"),
    ("undecided", "undecided", "int"),
    ("precision", "precision", "float"),
    ("decided_precision", "decided_precision", "float"),
    ("recall", "recall", "float"),
    ("f1", "f1", "float"),
    ("reference_facts", "reference_facts", "int"),
    ("covered_reference_facts", "covered_reference_facts", "int"),
]

METHODOLOGY_TABLE = """# Methodology: original paper vs VERIFACT-Lite

| Component | Original paper (Liu et al., EMNLP 2025) | VERIFACT-Lite |
|---|---|---|
| Judge 1 | GPT-4o (API) | {judge1} |
| Judge 2 | Llama 3.3-70B | {judge2} |
| Judge 3 | Qwen 2.5-32B | not used (two local judges) |
| Extraction / refinement / verification model | Llama 3.3-70B-Instruct | {primary} |
| Detection ensemble | union of 3 judges' positive detections | {strategy} of {n_judges} local judge(s) |
| Evidence source | Google Search via Serper API (paid) | {retrieval} (free, cached) |
| Evidence ranking | FactCheck-GPT cross-encoder | {ranker} over retrieved paragraphs |
| Benchmark | FACTRBENCH, 1,096 prompts | mini reference benchmark, {n_questions} prompts |
| Reference facts | 4 frontier LLMs + human Reddit answers | {n_ref} manually verified reference facts |
| Scale | large-scale, multi-GPU | single consumer GPU, quantized {quant} |

| Question | Answer |
|---|---|
| Exact reproduction of the paper's numbers? | No |
| Core methodology reproduced? | Yes |
| Cost? | $0 |
| Local execution? | Yes |
| Paid API required? | No |
"""


def _fmt(value, kind: str):
    if value is None:
        return ""
    if kind == "float":
        return round(float(value), 4)
    try:
        return int(value)
    except (TypeError, ValueError):
        return value


def write_comparison_csv(path: Path, baseline: dict, verifact: dict, ablation: dict) -> None:
    columns = ["metric", "baseline", "verifact_lite", "delta"]
    extra = {k: v for k, v in (ablation or {}).items() if k in ("B", "C")}
    for key in extra:
        columns.append({"B": "incomplete_refine_only", "C": "missing_relation_only"}[key])

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for name, key, kind in METRIC_ROWS:
            b = baseline.get(key)
            v = verifact.get(key)
            delta = ""
            if isinstance(b, (int, float)) and isinstance(v, (int, float)):
                delta = round(float(v) - float(b), 4)
            row = [name, _fmt(b, kind), _fmt(v, kind), delta]
            for vk in extra:
                row.append(_fmt(extra[vk].get(key), kind))
            writer.writerow(row)


def pick_examples(questions: list[dict], limit: int = 6) -> list[dict]:
    """Select the strongest qualitative examples automatically.

    Preference order: refined facts whose verification label changed, then
    omitted conditions and missing comparisons, then temporal/contingency
    relational facts that were added.
    """
    scored: list[tuple[float, dict]] = []
    for q in questions:
        variant = (q.get("variants") or {}).get("D") or {}
        refinements = [r for r in variant.get("refinements", []) if r.get("status") == "refined"]
        added = variant.get("added", [])
        changes = [ba for ba in q.get("before_after", []) if ba["before"] != ba["after"]]
        if not refinements and not added:
            continue

        score = 0.0
        score += 3.0 * len(changes)
        score += 1.5 * sum(
            1 for r in refinements if r.get("error_type") == "omitted_condition_or_source"
        )
        score += 1.2 * sum(1 for r in refinements if r.get("error_type") == "missing_comparison")
        score += 1.0 * sum(
            1 for a in added if a.get("relation_type") in ("contingency", "temporal")
        )
        score += 0.5 * len(refinements)

        label_by_claim = {v["claim"]: v for v in variant.get("verifications", [])}
        scored.append(
            (
                score,
                {
                    "question_id": q["question_id"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "baseline_facts": [
                        f.get("original_text") or f.get("text")
                        for f in ((q.get("variants") or {}).get("A") or variant).get("facts", [])
                    ],
                    "detected_issues": [
                        {
                            "fact_id": r["fact_id"],
                            "original": r["original"],
                            "error_type": r.get("error_type"),
                            "reason": r.get("reason"),
                            "refined": r["refined"],
                        }
                        for r in refinements
                    ],
                    "missing_relations": [
                        {
                            "span": rel["span"],
                            "relation_type": rel["relation_type"],
                            "judges": rel.get("judges"),
                            "already_covered": rel.get("already_covered"),
                        }
                        for rel in q.get("relations", [])
                        if rel.get("is_missing_relation")
                    ],
                    "added_facts": added,
                    "label_changes": changes,
                    "verification_labels": {
                        c: {"label": v["label"], "status": v["status"]}
                        for c, v in label_by_claim.items()
                    },
                    "metrics": {
                        "baseline": _variant_metrics((q.get("variants") or {}).get("A")),
                        "verifact": _variant_metrics(variant),
                    },
                    "example_score": round(score, 2),
                },
            )
        )

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:limit]]


def _variant_metrics(variant: dict | None) -> dict:
    if not variant:
        return {}
    return {
        "num_facts": variant.get("num_facts"),
        "incomplete_rate": round(float(variant.get("incomplete_rate", 0) or 0), 4),
        "supported": variant.get("supported"),
        "contradicted": variant.get("contradicted"),
        "undecided": variant.get("undecided"),
        "precision": round(float(variant.get("precision", 0) or 0), 4),
        "recall": round(float(variant.get("recall", 0) or 0), 4),
        "f1": round(float(variant.get("f1", 0) or 0), 4),
    }


def centerpiece_markdown(example: dict, baseline: dict, verifact: dict) -> str:
    lines = ["# VERIFACT-Lite: before / after example", ""]
    lines += ["## QUESTION", example["question"], "", "## ORIGINAL ANSWER", example["answer"], ""]
    lines += ["## BASELINE FACTS"]
    for fact in example["baseline_facts"][:12]:
        lines.append(f"- {fact}")
    lines.append("")
    if example["detected_issues"]:
        lines.append("## DETECTED ISSUES AND REFINEMENTS")
        for issue in example["detected_issues"]:
            lines += [
                f"- **{issue['fact_id']}** ({issue['error_type']})",
                f"  - baseline: {issue['original']}",
                f"  - reason:   {issue['reason']}",
                f"  - refined:  {issue['refined']}",
            ]
        lines.append("")
    if example["missing_relations"]:
        lines.append("## MISSING RELATIONS (word mapping -> judges)")
        for rel in example["missing_relations"]:
            lines.append(f"- span `{rel['span']}` -> {rel['relation_type']}")
        lines.append("")
    if example["added_facts"]:
        lines.append("## ADDED FACTS")
        for fact in example["added_facts"]:
            lines.append(f"- [{fact['relation_type']}] {fact['text']}")
        lines.append("")
    if example["label_changes"]:
        lines.append("## VERIFICATION BEFORE VS AFTER REFINEMENT")
        for change in example["label_changes"]:
            lines += [
                f"- {change['fact_id']}: {change['before']} -> {change['after']}",
                f"  - before: {change['original']}",
                f"  - after:  {change['refined']}",
            ]
        lines.append("")
    lines += [
        "## METRICS (whole mini benchmark)",
        "",
        "| System | Precision | Recall | F1 |",
        "|---|---|---|---|",
        f"| Baseline | {baseline.get('precision', 0):.4f} | {baseline.get('recall', 0):.4f} | {baseline.get('f1', 0):.4f} |",
        f"| VERIFACT-Lite | {verifact.get('precision', 0):.4f} | {verifact.get('recall', 0):.4f} | {verifact.get('f1', 0):.4f} |",
        "",
    ]
    return "\n".join(lines)


def make_charts(out_dir: Path, baseline: dict, verifact: dict, ablation: dict) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - optional dependency
        print(f"[warn] matplotlib unavailable ({exc}); skipping charts")
        return []

    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    def bar(path: Path, title: str, labels: list[str], values: list[float], ylabel: str, fmt="{:.3f}"):
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(labels, values, color=["#7f8fa6", "#2d6cdf", "#3fa45b", "#d98f2b"][: len(labels)])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.spines[["top", "right"]].set_visible(False)
        for rect, value in zip(bars, values):
            ax.annotate(
                fmt.format(value),
                (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                ha="center",
                va="bottom",
                fontsize=9,
            )
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        written.append(str(path))

    systems = ["Baseline", "VERIFACT-Lite"]
    bar(
        charts_dir / "incomplete_fact_rate.png",
        "Incomplete fact rate (lower is better)",
        systems,
        [baseline.get("incomplete_rate", 0), verifact.get("incomplete_rate", 0)],
        "incomplete facts / total facts",
    )
    bar(
        charts_dir / "missing_facts.png",
        "Missing relational facts (lower is better)",
        systems,
        [baseline.get("missing_relations", 0), verifact.get("missing_relations", 0)],
        "count over the benchmark",
        fmt="{:.0f}",
    )

    fig, ax = plt.subplots(figsize=(7, 4))
    metrics = ["precision", "recall", "f1"]
    width = 0.35
    xs = range(len(metrics))
    ax.bar([x - width / 2 for x in xs], [baseline.get(m, 0) for m in metrics], width, label="Baseline", color="#7f8fa6")
    ax.bar([x + width / 2 for x in xs], [verifact.get(m, 0) for m in metrics], width, label="VERIFACT-Lite", color="#2d6cdf")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([m.capitalize() for m in metrics])
    ax.set_ylim(0, 1)
    ax.set_title("Precision / Recall / F1")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    path = charts_dir / "precision_recall_f1.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    written.append(str(path))

    if ablation:
        order = [k for k in ("A", "B", "C", "D") if k in ablation]
        labels = [
            {"A": "Baseline", "B": "+Incomplete", "C": "+Relation", "D": "Full"}.get(k, k)
            for k in order
        ]
        fig, ax = plt.subplots(figsize=(7, 4))
        for metric, colour in (("precision", "#2d6cdf"), ("recall", "#3fa45b"), ("f1", "#d98f2b")):
            ax.plot(labels, [ablation[k].get(metric, 0) for k in order], marker="o", label=metric, color=colour)
        ax.set_title("Ablation: precision / recall / F1")
        ax.set_ylim(0, 1)
        ax.legend(frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        path = charts_dir / "ablation.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        written.append(str(path))

    return written


RESULTS_START = "<!-- RESULTS:START -->"
RESULTS_END = "<!-- RESULTS:END -->"


def results_markdown(summary: dict, ablation: dict, charts: list[str]) -> str:
    baseline = summary["baseline"]
    verifact = summary["verifact_lite"]
    imp = summary["improvement"]
    change = summary.get("label_change") or {}
    judges = summary.get("judge_ablation") or {}

    lines = [
        "_These numbers were measured by this repository on the mini reference benchmark. "
        "They are not the paper's numbers and are not comparable to them._",
        "",
        f"Questions: **{baseline.get('questions', 0)}** &nbsp;|&nbsp; "
        f"reference facts: **{baseline.get('reference_facts', 0)}**",
        "",
        "### Baseline vs VERIFACT-Lite",
        "",
        "| Metric | Baseline | VERIFACT-Lite | Delta |",
        "|---|---|---|---|",
    ]
    for name, key, kind in METRIC_ROWS:
        b, v = baseline.get(key, 0), verifact.get(key, 0)
        if kind == "float":
            lines.append(f"| {name} | {float(b):.4f} | {float(v):.4f} | {float(v) - float(b):+.4f} |")
        else:
            lines.append(f"| {name} | {b} | {v} | {(v or 0) - (b or 0):+d} |")

    lines += [
        "",
        "### Improvement",
        "",
        f"- incomplete fact reduction: **{imp['incomplete_fact_reduction_pct']:.1f}%**",
        f"- missing relation reduction: **{imp['missing_relation_reduction_pct']:.1f}%**",
        f"- precision change: **{imp['precision_change']:+.4f}**",
        f"- recall change: **{imp['recall_change']:+.4f}**",
        f"- F1 change: **{imp['f1_change']:+.4f}**",
        "",
    ]

    if ablation:
        lines += [
            "### Ablation",
            "",
            "| System | Incomplete rate | Missing relations | Precision | Recall | F1 |",
            "|---|---|---|---|---|---|",
        ]
        names = {
            "A": "Baseline",
            "B": "+ Incomplete Refine",
            "C": "+ Missing Relation",
            "D": "Full VERIFACT-Lite",
        }
        for key in ("A", "B", "C", "D"):
            row = ablation.get(key)
            if not row:
                continue
            lines.append(
                f"| {names[key]} | {row.get('incomplete_rate', 0):.3f} | "
                f"{row.get('missing_relations', 0)} | {row.get('precision', 0):.4f} | "
                f"{row.get('recall', 0):.4f} | {row.get('f1', 0):.4f} |"
            )
        lines.append("")

    if judges:
        lines += [
            "### Judge ablation (single judge vs union ensemble)",
            "",
            "| Judge | Incomplete detected | Missing relations detected | Problem-detection recall vs ensemble | Precision vs ensemble |",
            "|---|---|---|---|---|",
        ]
        for alias, stats in judges.items():
            lines.append(
                f"| {alias} | {stats['incomplete_detected']} | {stats['missing_relation_detected']} | "
                f"{stats['problem_detection_recall']:.3f} | {stats['precision_vs_ensemble']:.3f} |"
            )
        lines.append("")

    majority = summary.get("ablation_majority") or {}
    if majority:
        lines += [
            "### Ensemble strategy: union vs majority vote",
            "",
            "Both rows use the same judge decisions; only the rule that turns them into a "
            "refinement decision differs. Union is the paper's rule.",
            "",
            "| Strategy | Incomplete rate | Missing relations | Precision | Recall | F1 |",
            "|---|---|---|---|---|---|",
        ]
        for label, table in (("union", ablation), ("majority", majority)):
            row = (table or {}).get("D")
            if not row:
                continue
            lines.append(
                f"| {label} | {row.get('incomplete_rate', 0):.3f} | "
                f"{row.get('missing_relations', 0)} | {row.get('precision', 0):.4f} | "
                f"{row.get('recall', 0):.4f} | {row.get('f1', 0):.4f} |"
            )
        lines.append("")

    if change:
        lines += [
            "### Before vs after verification of refined facts",
            "",
            f"- refined facts verified both ways: **{change['refined_facts_verified']}**",
            f"- label changes: **{change['label_changes']}**",
            f"- label change rate: **{change['label_change_rate']:.3f}**",
            "",
            "| Transition | Count |",
            "|---|---|",
        ]
        for transition, count in sorted(change["transitions"].items(), key=lambda x: -x[1]):
            lines.append(f"| {transition} | {count} |")
        lines.append("")

    if charts:
        lines.append("### Charts")
        lines.append("")
        for chart in charts:
            rel = chart.replace("\\", "/")
            idx = rel.find("outputs/")
            rel = rel[idx:] if idx >= 0 else rel
            lines.append(f"![{Path(rel).stem}]({rel})")
        lines.append("")

    return "\n".join(lines)


def update_readme(root: Path, body: str) -> bool:
    """Insert the measured results between the README markers."""
    readme = root / "README.md"
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8")
    if RESULTS_START not in text or RESULTS_END not in text:
        return False
    head, rest = text.split(RESULTS_START, 1)
    _, tail = rest.split(RESULTS_END, 1)
    readme.write_text(
        f"{head}{RESULTS_START}\n\n{body}\n{RESULTS_END}{tail}", encoding="utf-8"
    )
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Build comparison tables, examples and charts.")
    parser.add_argument("--config", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    out_dir = resolve_path(cfg, (cfg.get("paths") or {}).get("outputs", "outputs"))
    baseline_payload = read_json(out_dir / "baseline.json")
    verifact_payload = read_json(out_dir / "verifact.json")
    ablation_payload = read_json(out_dir / "ablation.json")
    majority_payload = read_json(out_dir / "ablation_majority.json")

    if not baseline_payload or not verifact_payload:
        raise SystemExit(
            "missing runs: execute `python -m experiments.run_baseline` and "
            "`python -m experiments.run_verifact` first"
        )

    baseline = baseline_payload["summaries"]["A"]
    verifact = verifact_payload["summaries"]["D"]
    ablation = (ablation_payload or {}).get("summaries", {})

    write_comparison_csv(out_dir / "comparison.csv", baseline, verifact, ablation)

    questions = verifact_payload["questions"]
    if ablation_payload:
        # The ablation run carries all four variants per question; prefer it.
        questions = ablation_payload["questions"]
    examples = pick_examples(questions)
    write_json(out_dir / "examples" / "presentation_examples.json", examples)

    summary = {
        "baseline": baseline,
        "verifact_lite": verifact,
        "ablation": ablation,
        "ablation_majority": (majority_payload or {}).get("summaries", {}),
        "improvement": improvement(baseline, verifact),
        "label_change": verifact_payload.get("label_change", {}),
        "judge_ablation": (ablation_payload or verifact_payload).get("judge_ablation", {}),
        "config": verifact_payload.get("config", {}),
        "runtime_stats": verifact_payload.get("runtime_stats", {}),
        "n_examples": len(examples),
    }
    write_json(out_dir / "summary.json", summary)

    judges = (cfg.get("judges") or [])
    challenge = resolve_path(cfg, (cfg.get("paths") or {}).get("challenge_set"))
    n_questions = sum(1 for _ in open(challenge, encoding="utf-8") if _.strip())
    n_ref = baseline.get("reference_facts", 0)
    methodology = METHODOLOGY_TABLE.format(
        judge1=f"{judges[0]['name']} ({judges[0]['model_id']})" if judges else "n/a",
        judge2=f"{judges[1]['name']} ({judges[1]['model_id']})" if len(judges) > 1 else "not used",
        primary=f"{cfg['model']['name']} ({cfg['model']['model_id']})",
        strategy=(cfg.get("ensemble") or {}).get("strategy", "union"),
        n_judges=len(judges) or 1,
        retrieval=(cfg.get("retrieval") or {}).get("source", "wikipedia").capitalize(),
        ranker=(cfg.get("retrieval") or {}).get("ranker", "bm25").upper(),
        n_questions=n_questions,
        n_ref=n_ref,
        quant=cfg["model"].get("quantization", "Q4_K_M"),
    )
    (out_dir / "methodology_table.md").write_text(methodology, encoding="utf-8")

    if examples:
        (out_dir / "examples" / "centerpiece.md").write_text(
            centerpiece_markdown(examples[0], baseline, verifact), encoding="utf-8"
        )

    charts = make_charts(out_dir, baseline, verifact, ablation)

    print("=== Baseline vs VERIFACT-Lite ===")
    header = f"{'metric':<26}{'baseline':>12}{'verifact':>12}{'delta':>10}"
    print(header)
    print("-" * len(header))
    for name, key, kind in METRIC_ROWS:
        b, v = baseline.get(key, 0), verifact.get(key, 0)
        if isinstance(b, float) or isinstance(v, float):
            print(f"{name:<26}{float(b):>12.4f}{float(v):>12.4f}{float(v) - float(b):>10.4f}")
        else:
            print(f"{name:<26}{b:>12}{v:>12}{(v or 0) - (b or 0):>10}")

    imp = summary["improvement"]
    print("\n=== Improvement ===")
    print(f"  incomplete fact reduction : {imp['incomplete_fact_reduction_pct']:.1f}%")
    print(f"  missing relation reduction: {imp['missing_relation_reduction_pct']:.1f}%")
    print(f"  precision change          : {imp['precision_change']:+.4f}")
    print(f"  recall change             : {imp['recall_change']:+.4f}")
    print(f"  F1 change                 : {imp['f1_change']:+.4f}")

    results_md = results_markdown(summary, ablation, charts)
    (out_dir / "results.md").write_text(results_md, encoding="utf-8")
    injected = update_readme(Path(cfg["_root"]), results_md)

    print(f"\nwrote {out_dir / 'comparison.csv'}")
    print(f"wrote {out_dir / 'results.md'}")
    if injected:
        print("updated README.md results section")
    print(f"wrote {out_dir / 'summary.json'}")
    print(f"wrote {out_dir / 'methodology_table.md'}")
    print(f"wrote {out_dir / 'examples' / 'presentation_examples.json'} ({len(examples)} examples)")
    for chart in charts:
        print(f"wrote {chart}")


if __name__ == "__main__":
    main()
