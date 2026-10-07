"""Full VERIFACT-Lite run: detection + refinement + verification (variant D).

Reuses outputs/answers.json so the answers are byte-identical to the baseline run.

    python -m experiments.run_verifact
"""

from __future__ import annotations

from experiments.common import (
    base_parser,
    build_payload,
    load_answers,
    print_summary,
    save_answers,
    setup,
)
from src.utils import write_json


def main() -> None:
    parser = base_parser("Run the full VERIFACT-Lite pipeline.")
    args = parser.parse_args()
    cfg, pipeline, out_dir = setup(args)

    answers = load_answers(out_dir)
    results, answers = pipeline.run_dataset(variant_keys=("D",), answers=answers)
    save_answers(out_dir, answers)

    payload = build_payload("verifact", cfg, pipeline, results, ("D",))
    write_json(out_dir / "verifact.json", payload)
    print_summary("VERIFACT-Lite", payload["summaries"]["D"])

    change = payload.get("label_change") or {}
    if change:
        print("\n=== Before vs after verification of refined facts ===")
        print(f"  refined facts verified : {change['refined_facts_verified']}")
        print(f"  label changes          : {change['label_changes']}")
        print(f"  label change rate      : {change['label_change_rate']:.3f}")
        for transition, count in sorted(change["transitions"].items(), key=lambda x: -x[1]):
            print(f"    {transition:<28} {count}")
    print(f"\nwrote {out_dir / 'verifact.json'}")


if __name__ == "__main__":
    main()
