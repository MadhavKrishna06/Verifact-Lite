# Colab experiments — results

Three runs over the same 12 questions and the **same 12 generated answers**
(verified identical by hash). Reproduce any table with:

```bash
python colab/compare_runs.py laptop-3B=outputs/summary.json judges-7B=outputs_colab_a/summary.json full-7B=outputs_colab_b/summary.json
```

| Run | Primary model | Judges |
|---|---|---|
| `laptop-3B` | Qwen2.5-3B | Qwen2.5-3B + Llama-3.2-3B |
| `judges-7B` (experiment A) | Qwen2.5-3B | Qwen2.5-7B + Llama-3.1-8B |
| `full-7B` (experiment B) | Qwen2.5-7B | Qwen2.5-7B + Llama-3.1-8B |

## Experiment A is a controlled comparison; B is not

A changed only the judges. Its baseline is byte-identical to the laptop's —
21.50 facts per answer, 109 supported, 3 contradicted, 146 undecided,
precision 0.4200, F1 0.4138 — because extraction replayed from cache.

B changed the extractor, the incompleteness judge, the verifier **and** the
recall entailment model at once. Its columns may only be read against its own
baseline.

## 1. The metrics measure the judge as much as the system

Identical facts, identical answers, different measuring model:

| Measurement | 3B model | 7B model | Paper |
|---|---|---|---|
| Incomplete rate on the same baseline facts | 0.105 | **0.438** | 0.567 (GPT-4o on SAFE) |
| Recall on the same answers and reference facts | 0.4077 | **0.2812** | — |

The recall figure is the starkest: same 12 answers, same 86 reference facts,
same lexical gate (64 entailment calls, 22 gated out), and coverage falls from
35/86 to 24/86 purely because a larger model judges entailment more strictly.

The laptop deck says "10.5% vs 56.7% reflects a weaker judge, not a better
extractor". That is now measured rather than argued: a stronger judge finds
four times as many problems in the same text and lands two-thirds of the way to
the paper's figure.

## 2. Refinement behaves the same way, and the paper's full signature appears

| | laptop-3B | judges-7B | full-7B |
|---|---|---|---|
| precision, baseline → refined | 0.4200 → 0.3426 | 0.4200 → 0.3018 | 0.5050 → 0.4802 |
| contradicted, baseline → refined | 3 → 3 | 3 → **8** | 1 → 2 |
| refined facts changing verdict | 39.3% | 45.6% | 34.7% |

Precision falls after refinement in every configuration, as the paper reports.
With 3B judges contradicted never moved; with 7–8B judges it rises 3 → 8, which
is the other half of the paper's reported pattern (supported down, contradicted
up) and was missing from the laptop run entirely.

The verdict-change rate is 34.7–45.6% across all three, against the paper's
24.9%. The phenomenon is robust to model size.

## 3. Union vs majority: one claim survives, one does not

| Run | Rule | Incomplete | Precision | F1 |
|---|---|---|---|---|
| laptop-3B | union | 0.091 | 0.3426 | 0.3723 |
| laptop-3B | **majority** | **0.042** | **0.4071** | **0.4074** |
| judges-7B | union | 0.411 | 0.3018 | 0.3468 |
| judges-7B | **majority** | 0.393 | **0.4106** | **0.4092** |
| full-7B | union | 0.286 | 0.4802 | 0.3547 |
| full-7B | **majority** | 0.287 | **0.4985** | **0.3596** |

**Survives:** majority vote gives higher precision and F1 than union in all
three configurations.

**Does not survive:** "majority cuts the incomplete rate by 60%". That was a
3B artifact (0.042 vs 0.091). With 7–8B judges the two rules are within 4%
(0.393 vs 0.411), and with a 7B extractor they are identical (0.287 vs 0.286).

## 4. The permissive-judge finding splits by task

Facts flagged by each judge, and by the union ensemble:

| Run | | Qwen | Llama | Ensemble |
|---|---|---|---|---|
| laptop-3B | incomplete | 20 | 34 | 34 |
| laptop-3B | relations | 2 | 51 | 51 |
| judges-7B | incomplete | 32 | 27 | **33** |
| judges-7B | relations | 15 | 54 | 54 |
| full-7B | incomplete | 24 | 18 | **25** |
| full-7B | relations | 8 | 21 | 21 |

**Relation detection**: the ensemble equals Llama exactly in all three runs —
51/51, 54/54, 21/21. Qwen never finds a relation Llama missed, at any model
size. The union really is one judge's opinion here.

**Incompleteness detection**: with 3B judges the ensemble equals Llama (34), so
again no complementarity. With 7–8B judges the ensemble exceeds both (33 > 32,
27; and 25 > 24, 18), which is the first evidence of the judges actually
complementing each other — the behaviour the paper's union rule assumes.

## 5. A stronger extractor leaves less to repair

Experiment B's baseline produces 15.92 facts per answer against 21.50, with a
lower incomplete rate (0.319 vs 0.438 under the same 7B judge) and higher
precision (0.5050 vs 0.4200). Refinement then costs far less precision
(−0.025, against −0.118 in A).

Fewer, coarser, more self-contained facts are both easier to verify and less in
need of repair — the same trade the paper notes for VERIFY, which extracts 18.5
facts per response against VeriFact's 32.3.

## Caveats

* Temperature-0 decoding is not bit-reproducible until the cache is warm: a
  first pass over a cold cache can differ slightly from a re-run, after which
  the cache freezes the result. All saved artifacts here are self-consistent.
* 12 questions and 86 reference facts. Trends, not significance.
* B's recall and incomplete rate are not comparable with A's or the laptop's,
  because the models producing those judgements changed.
