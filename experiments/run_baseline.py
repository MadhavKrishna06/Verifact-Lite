"""Baseline run: SAFE-style extraction + verification, no refinement (variant A).

    python -m experiments.run_baseline
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
    parser = base_parser("Run the baseline fact-extraction and verification pipeline.")
    args = parser.parse_args()
    cfg, pipeline, out_dir = setup(args)

    answers = load_answers(out_dir)
    results, answers = pipeline.run_dataset(variant_keys=("A",), answers=answers)
    save_answers(out_dir, answers)

    payload = build_payload("baseline", cfg, pipeline, results, ("A",))
    write_json(out_dir / "baseline.json", payload)
    print_summary("Baseline", payload["summaries"]["A"])
    print(f"\nwrote {out_dir / 'baseline.json'}")


if __name__ == "__main__":
    main()
