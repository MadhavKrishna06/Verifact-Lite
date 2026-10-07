"""Print several completed runs side by side.

Each argument is ``label=path/to/summary.json`` (the file ``experiments.compare``
writes). Use it to put the laptop run next to a Colab run:

    python colab/compare_runs.py laptop-3B=outputs/summary.json judges-7B=outputs_colab_a/summary.json
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils import read_json  # noqa: E402

ROWS = [
    ("facts / answer", "avg_facts", "{:.2f}"),
    ("incomplete rate", "incomplete_rate", "{:.3f}"),
    ("missing relations", "missing_relations", "{:.0f}"),
    ("refined facts", "refined_facts", "{:.0f}"),
    ("added facts", "added_facts", "{:.0f}"),
    ("supported", "supported", "{:.0f}"),
    ("contradicted", "contradicted", "{:.0f}"),
    ("undecided", "undecided", "{:.0f}"),
    ("precision", "precision", "{:.4f}"),
    ("decided precision", "decided_precision", "{:.4f}"),
    ("recall", "recall", "{:.4f}"),
    ("F1", "f1", "{:.4f}"),
]


def fmt(value, spec: str) -> str:
    if value is None:
        return "-"
    try:
        return spec.format(float(value))
    except (TypeError, ValueError):
        return str(value)


def section(title: str, runs: list[tuple[str, dict]], key: str) -> None:
    print(f"\n=== {title} ===")
    width = max(len(name) for name, _, _ in ROWS) + 2
    header = " " * width + "".join(f"{label:>22}" for label, _ in runs)
    print(header)
    print("-" * len(header))
    for name, field, spec in ROWS:
        cells = "".join(f"{fmt((run.get(key) or {}).get(field), spec):>22}" for _, run in runs)
        print(f"{name:<{width}}{cells}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)

    runs: list[tuple[str, dict]] = []
    for arg in args:
        if "=" not in arg:
            raise SystemExit(f"expected label=path, got {arg!r}")
        label, path = arg.split("=", 1)
        data = read_json(path)
        if not data:
            raise SystemExit(f"no summary at {path}; run `python -m experiments.compare` for that config first")
        runs.append((label, data))

    section("Baseline", runs, "baseline")
    section("VERIFACT-Lite", runs, "verifact_lite")

    print("\n=== Label change on refined facts ===")
    for label, run in runs:
        change = run.get("label_change") or {}
        if change:
            print(
                f"  {label:<18} {change.get('label_changes', 0)} / {change.get('refined_facts_verified', 0)}"
                f"  = {float(change.get('label_change_rate', 0)):.3f}"
            )
        else:
            print(f"  {label:<18} (none recorded)")

    print("\n=== Judge ablation ===")
    for label, run in runs:
        print(f"  {label}")
        for alias, stats in (run.get("judge_ablation") or {}).items():
            print(
                f"    {alias:<12} incomplete={stats.get('incomplete_detected', 0):<4}"
                f" relations={stats.get('missing_relation_detected', 0):<4}"
                f" precision_vs_ensemble={float(stats.get('precision_vs_ensemble', 0)):.3f}"
            )

    print("\n=== Models used ===")
    for label, run in runs:
        cfg = run.get("config") or {}
        primary = (cfg.get("model") or {}).get("model_id", "?")
        judges = ", ".join(j.get("model_id", "?") for j in (cfg.get("judges") or []))
        print(f"  {label:<18} primary={primary}")
        print(f"  {'':<18} judges={judges}")


if __name__ == "__main__":
    main()
