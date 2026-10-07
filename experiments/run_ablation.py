"""Ablation study over the four pipeline variants.

    A  Baseline
    B  Baseline + incomplete-fact refinement
    C  Baseline + missing-relation refinement
    D  Full VERIFACT-Lite

    python -m experiments.run_ablation
"""

from __future__ import annotations

import csv

from experiments.common import (
    base_parser,
    build_payload,
    load_answers,
    print_summary,
    save_answers,
    setup,
)
from src.pipeline import VARIANTS
from src.utils import write_json

ABLATION_COLUMNS = [
    ("variant", "variant"),
    ("system", "label"),
    ("avg_facts", "avg_facts"),
    ("incomplete_facts", "incomplete_facts"),
    ("incomplete_rate", "incomplete_rate"),
    ("missing_relations", "missing_relations"),
    ("refined_facts", "refined_facts"),
    ("added_facts", "added_facts"),
    ("supported", "supported"),
    ("contradicted", "contradicted"),
    ("undecided", "undecided"),
    ("precision", "precision"),
    ("decided_precision", "decided_precision"),
    ("recall", "recall"),
    ("f1", "f1"),
]


def main() -> None:
    parser = base_parser("Run the A/B/C/D ablation study.")
    args = parser.parse_args()
    cfg, pipeline, out_dir = setup(args)

    variant_keys = ("A", "B", "C", "D")
    answers = load_answers(out_dir)
    results, answers = pipeline.run_dataset(variant_keys=variant_keys, answers=answers)
    save_answers(out_dir, answers)

    payload = build_payload("ablation", cfg, pipeline, results, variant_keys)
    write_json(out_dir / "ablation.json", payload)

    rows = []
    for vkey in variant_keys:
        summary = payload["summaries"].get(vkey) or {}
        row = {"variant": vkey, "label": VARIANTS[vkey]["label"]}
        for _, key in ABLATION_COLUMNS:
            if key in ("variant", "label"):
                continue
            value = summary.get(key, 0)
            row[key] = round(value, 4) if isinstance(value, float) else value
        rows.append(row)

    csv_path = out_dir / "ablation.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=[name for name, _ in ABLATION_COLUMNS])
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(key) for name, key in ABLATION_COLUMNS})

    for vkey in variant_keys:
        print_summary(f"{vkey} - {VARIANTS[vkey]['label']}", payload["summaries"].get(vkey, {}))

    print("\n=== Ablation table ===")
    header = f"{'System':<24}{'Incomplete':>12}{'Missing':>9}{'Precision':>11}{'Recall':>9}{'F1':>8}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['label']:<24}{row['incomplete_rate']:>12.3f}{row['missing_relations']:>9}"
            f"{row['precision']:>11.4f}{row['recall']:>9.4f}{row['f1']:>8.4f}"
        )

    print("\n=== Judge ablation (single judge vs ensemble) ===")
    for alias, stats in payload["judge_ablation"].items():
        print(
            f"  {alias:<10} incomplete={stats['incomplete_detected']:<4}"
            f" rel={stats['missing_relation_detected']:<4}"
            f" problem_recall={stats['problem_detection_recall']:.3f}"
            f" precision={stats['precision_vs_ensemble']:.3f}"
        )

    print(f"\nwrote {out_dir / 'ablation.json'} and {csv_path}")


if __name__ == "__main__":
    main()
