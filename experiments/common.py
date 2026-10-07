"""Shared plumbing for the experiment scripts."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.metrics import aggregate, judge_ablation, label_change_stats
from src.pipeline import VerifactLitePipeline, result_to_dict
from src.utils import load_config, read_json, resolve_path, write_json

ANSWERS_FILE = "answers.json"


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--config", default=None, help="path to config.yaml")
    parser.add_argument("--limit", type=int, default=None, help="only run the first N questions")
    parser.add_argument("--quiet", action="store_true", help="suppress per-step logging")
    parser.add_argument(
        "--ensemble",
        choices=["union", "majority", "weighted"],
        default=None,
        help="override ensemble.strategy for this run (union is the paper's rule)",
    )
    return parser


def setup(args) -> tuple[dict, VerifactLitePipeline, Path]:
    cfg = load_config(args.config)
    if args.limit:
        cfg.setdefault("run", {})["limit"] = args.limit
    if getattr(args, "ensemble", None):
        cfg.setdefault("ensemble", {})["strategy"] = args.ensemble
    out_dir = resolve_path(cfg, (cfg.get("paths") or {}).get("outputs", "outputs"))
    out_dir.mkdir(parents=True, exist_ok=True)
    pipeline = VerifactLitePipeline(cfg, verbose=not args.quiet)
    return cfg, pipeline, out_dir


def load_answers(out_dir: Path) -> dict[str, str]:
    """Reuse answers from a previous run so every variant sees the same text."""
    data = read_json(out_dir / ANSWERS_FILE, default={}) or {}
    return {k: v for k, v in data.items() if isinstance(v, str)}


def save_answers(out_dir: Path, answers: dict[str, str]) -> None:
    write_json(out_dir / ANSWERS_FILE, answers)


def build_payload(
    name: str,
    cfg: dict,
    pipeline: VerifactLitePipeline,
    results: list,
    variant_keys: tuple[str, ...],
) -> dict:
    summaries = {vk: aggregate([r.variants[vk] for r in results if vk in r.variants]) for vk in variant_keys}

    detections = [d for r in results for d in r.detections]
    relations = [rel for r in results for rel in r.relations]
    before_after = [ba for r in results for ba in r.before_after]

    return {
        "run": name,
        "config": {
            "model": cfg.get("model"),
            "generation": cfg.get("generation"),
            "judges": cfg.get("judges"),
            "ensemble": cfg.get("ensemble"),
            "retrieval": {
                k: v
                for k, v in (cfg.get("retrieval") or {}).items()
                if k in {"source", "ranker", "top_k", "queries_per_fact", "offline_only"}
            },
        },
        "variant_keys": list(variant_keys),
        "summaries": summaries,
        "judge_ablation": judge_ablation(detections, relations, pipeline.completeness.judge_aliases),
        "label_change": label_change_stats(before_after) if before_after else {},
        "runtime_stats": pipeline.stats(),
        "questions": [result_to_dict(r) for r in results],
    }


def print_summary(title: str, summary: dict) -> None:
    if not summary:
        print(f"{title}: no results")
        return
    print(f"\n=== {title} ===")
    rows = [
        ("questions", summary.get("questions")),
        ("avg facts / answer", f"{summary.get('avg_facts', 0):.2f}"),
        ("incomplete facts", summary.get("incomplete_facts")),
        ("incomplete rate", f"{summary.get('incomplete_rate', 0):.3f}"),
        ("missing relations", summary.get("missing_relations")),
        ("refined facts", summary.get("refined_facts")),
        ("added facts", summary.get("added_facts")),
        ("supported", summary.get("supported")),
        ("contradicted", summary.get("contradicted")),
        ("undecided", summary.get("undecided")),
        ("precision", f"{summary.get('precision', 0):.4f}"),
        ("decided precision", f"{summary.get('decided_precision', 0):.4f}"),
        ("recall", f"{summary.get('recall', 0):.4f}"),
        ("F1", f"{summary.get('f1', 0):.4f}"),
    ]
    width = max(len(k) for k, _ in rows)
    for key, value in rows:
        print(f"  {key:<{width}} : {value}")
