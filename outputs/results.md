_These numbers were measured by this repository on the mini reference benchmark. They are not the paper's numbers and are not comparable to them._

Questions: **12** &nbsp;|&nbsp; reference facts: **86**

### Baseline vs VERIFACT-Lite

| Metric | Baseline | VERIFACT-Lite | Delta |
|---|---|---|---|
| questions | 12 | 12 | +0 |
| avg_facts_per_answer | 21.5000 | 24.6667 | +3.1667 |
| incomplete_facts | 27 | 27 | +0 |
| incomplete_fact_rate | 0.1047 | 0.0912 | -0.0134 |
| missing_relations | 51 | 0 | -51 |
| candidate_spans | 73 | 73 | +0 |
| refined_facts | 0 | 163 | +163 |
| added_facts | 0 | 51 | +51 |
| supported | 109 | 108 | -1 |
| contradicted | 3 | 3 | +0 |
| undecided | 146 | 185 | +39 |
| precision | 0.4200 | 0.3426 | -0.0774 |
| decided_precision | 0.9732 | 0.9730 | -0.0002 |
| recall | 0.4077 | 0.4077 | +0.0000 |
| f1 | 0.4138 | 0.3723 | -0.0415 |
| reference_facts | 86 | 86 | +0 |
| covered_reference_facts | 35 | 35 | +0 |

### Improvement

- incomplete fact reduction: **12.8%**
- missing relation reduction: **100.0%**
- precision change: **-0.0774**
- recall change: **+0.0000**
- F1 change: **-0.0415**

### Ablation

| System | Incomplete rate | Missing relations | Precision | Recall | F1 |
|---|---|---|---|---|---|
| Baseline | 0.105 | 51 | 0.4200 | 0.4077 | 0.4138 |
| + Incomplete Refine | 0.078 | 51 | 0.3680 | 0.4077 | 0.3868 |
| + Missing Relation | 0.113 | 0 | 0.3839 | 0.4077 | 0.3954 |
| Full VERIFACT-Lite | 0.091 | 0 | 0.3426 | 0.4077 | 0.3723 |

### Judge ablation (single judge vs union ensemble)

| Judge | Incomplete detected | Missing relations detected | Problem-detection recall vs ensemble | Precision vs ensemble |
|---|---|---|---|---|
| qwen | 20 | 2 | 0.259 | 1.000 |
| llama | 34 | 51 | 1.000 | 1.000 |
| ensemble | 34 | 51 | 1.000 | 1.000 |

### Ensemble strategy: union vs majority vote

Both rows use the same judge decisions; only the rule that turns them into a refinement decision differs. Union is the paper's rule.

| Strategy | Incomplete rate | Missing relations | Precision | Recall | F1 |
|---|---|---|---|---|---|
| union | 0.091 | 0 | 0.3426 | 0.4077 | 0.3723 |
| majority | 0.042 | 0 | 0.4071 | 0.4077 | 0.4074 |

### Before vs after verification of refined facts

- refined facts verified both ways: **178**
- label changes: **70**
- label change rate: **0.393**

| Transition | Count |
|---|---|
| UNDECIDED->UNDECIDED | 79 |
| SUPPORTED->UNDECIDED | 37 |
| SUPPORTED->SUPPORTED | 29 |
| UNDECIDED->SUPPORTED | 29 |
| UNDECIDED->CONTRADICTED | 2 |
| CONTRADICTED->UNDECIDED | 1 |
| CONTRADICTED->SUPPORTED | 1 |

### Charts

![incomplete_fact_rate](outputs/charts/incomplete_fact_rate.png)
![missing_facts](outputs/charts/missing_facts.png)
![precision_recall_f1](outputs/charts/precision_recall_f1.png)
![ablation](outputs/charts/ablation.png)
