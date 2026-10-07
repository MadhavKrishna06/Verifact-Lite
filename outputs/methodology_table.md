# Methodology: original paper vs VERIFACT-Lite

| Component | Original paper (Liu et al., EMNLP 2025) | VERIFACT-Lite |
|---|---|---|
| Judge 1 | GPT-4o (API) | Qwen2.5-3B-Instruct (qwen2.5:3b-instruct-q4_K_M) |
| Judge 2 | Llama 3.3-70B | Llama-3.2-3B-Instruct (llama3.2:3b-instruct-q4_K_M) |
| Judge 3 | Qwen 2.5-32B | not used (two local judges) |
| Extraction / refinement / verification model | Llama 3.3-70B-Instruct | Qwen2.5-3B-Instruct (qwen2.5:3b-instruct-q4_K_M) |
| Detection ensemble | union of 3 judges' positive detections | union of 2 local judge(s) |
| Evidence source | Google Search via Serper API (paid) | Wikipedia (free, cached) |
| Evidence ranking | FactCheck-GPT cross-encoder | BM25 over retrieved paragraphs |
| Benchmark | FACTRBENCH, 1,096 prompts | mini reference benchmark, 12 prompts |
| Reference facts | 4 frontier LLMs + human Reddit answers | 86 manually verified reference facts |
| Scale | large-scale, multi-GPU | single consumer GPU, quantized Q4_K_M |

| Question | Answer |
|---|---|
| Exact reproduction of the paper's numbers? | No |
| Core methodology reproduced? | Yes |
| Cost? | $0 |
| Local execution? | Yes |
| Paid API required? | No |
