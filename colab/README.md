# Running VERIFACT-Lite on a Colab T4

The laptop results were produced on a GTX 1650 with 4 GB of VRAM. Two 3B Q4_K_M judges do not fit there together, so the pipeline drives one judge at a time and unloads it before the next. That constraint shaped the whole project, and the judge-ablation result — the union rule collapsing onto the more permissive judge — may be an artifact of it.

A free Colab T4 has 16 GB. This directory runs the same code with bigger judges to find out.

## The two experiments

| | Primary model | Judges | Output dir |
|---|---|---|---|
| **A — judge upgrade** | Qwen2.5-3B (unchanged) | Qwen2.5-7B + Llama-3.1-8B | `outputs_colab_a/` |
| **B — full upgrade** | Qwen2.5-7B | Qwen2.5-7B + Llama-3.1-8B | `outputs_colab_b/` |

**A is the controlled comparison.** Extraction, decontextualization, refinement, retrieval and verification all still run on Qwen2.5-3B and replay from the shipped cache, so the baseline fact set is byte-identical to the laptop run. The only variable is detection quality. If the baseline column moves at all in A, something leaked and the comparison is not clean.

**B is a different system.** Everything moves to 7–8B, so the baseline changes too. Its precision and F1 may only be compared against *its own* baseline column, never against the laptop's.

Both reuse `outputs/answers.json`. The answers under evaluation were generated once on the laptop and are never regenerated — that is what makes any of these runs comparable.

## What A is testing

1. Does a 7–8B judge still flag nearly every fact? On the laptop, Llama-3.2-3B flagged 34 incomplete facts and 71 relations against Qwen2.5-3B's 20 and 2, giving it a precision of 0.200 against the majority decision.
2. Does the incomplete rate fall below the laptop's 0.091 (union) / 0.042 (majority)?
3. **Does the union-vs-majority gap close?** This is the real question. If better judges make union competitive with majority, the paper's recall-first rule is vindicated and the laptop's "majority wins" finding was a small-model artifact. If the gap holds, the finding stands on its own.

## Use

On the laptop:

```bash
python colab/make_bundle.py
```

That writes `colab/verifact_lite_bundle.zip` (~15 MB): code, benchmark, generated answers, LLM call cache and cached Wikipedia pages.

Then open `VERIFACT_Lite_Colab.ipynb` in Colab, set the runtime to a T4 GPU, and work down the cells. Expect 60–90 minutes for A and 90–150 for B; `LIMIT = "--limit 4"` shortens either for a first look.

The last cell downloads `outputs_colab_a/`, `outputs_colab_b/` and the grown caches. Unzip that over the repo and the comparison reproduces with no GPU:

```bash
python colab/compare_runs.py laptop-3B=outputs/summary.json judges-7B=outputs_colab_a/summary.json
```

## Notes

* `experiments.compare` only rewrites the README's results section for the default `outputs/` directory, so a Colab run cannot clobber the laptop numbers. Each run writes its own `results.md`, `comparison.csv`, `summary.json` and charts inside its own output directory.
* Both configs set `run.unload_between_judges: false`, which is correct at 16 GB. On a smaller GPU set it back to `true`.
* Colab's datacenter IP hits Wikipedia's rate limiter more readily than a home connection. The retry and backoff logic handles it, and the shipped evidence cache means most pages are never fetched again — but claims that refinement newly creates still need live retrieval.
* Free Colab sessions stop when idle. Keep the tab open, or run A alone in one session and B in another.
