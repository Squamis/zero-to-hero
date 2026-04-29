# L0 — Prompt engineering

The hand-crafted-wording layer. Six techniques on a 50-problem GSM8K test slice. All techniques run against the same model so the only thing changing is the prompt.

## Techniques

| # | Technique | What's different from the prompt above it |
|---|-----------|--------------------------------------------|
| 1 | zero-shot | Just `Question:`/`Answer:`. Baseline. |
| 2 | role | Adds `You are an expert mathematician...` system framing. |
| 3 | few-shot | Adds 4 worked examples — answers only, no reasoning shown. |
| 4 | zero-shot CoT | `Let's think step by step.` (Kojima et al. 2022) |
| 5 | few-shot CoT | 4 worked examples *with reasoning* (Wei et al. 2022). |
| 6 | self-consistency | Few-shot CoT, sampled N=5 at temp=0.7, majority vote (Wang et al. 2022). |

## Model

**Mistral-7B-Instruct v0.1** via OpenRouter. Released Sept 2023 — the exact window when CoT, self-consistency, and few-shot prompting were being canonized. 7B is small enough that the techniques visibly move the needle. A frontier 2026 model would ace zero-shot GSM8K and erase the lesson.

## Benchmark

GSM8K test split, 50 problems sampled with `seed=42`. Grading: extract the final number from the model's response, compare numerically (tolerance 1e-3).

## Pass criterion

> You can articulate which techniques helped which task type, with measurable evidence.

We expect to see (rough order-of-magnitude based on the original CoT paper):
- zero-shot ≈ role ≈ 15–25%
- few-shot ≈ 20–30% (small lift, no reasoning shown)
- zero-shot CoT ≈ 30–40%
- few-shot CoT ≈ 35–50%
- self-consistency ≈ 40–55%

If the actual numbers diverge sharply, that's the lesson — figure out why.

## Run

```bash
python run.py                  # full 50 problems
python run.py --n 5            # quick smoke
python plot.py                 # generates results/accuracy.png
```

## Files

- `client.py` — OpenRouter client (OpenAI SDK pointed at `openrouter.ai/api/v1`)
- `data.py` — GSM8K loader (HuggingFace `datasets`)
- `grader.py` — numeric answer extraction
- `techniques.py` — the six techniques
- `run.py` — benchmark runner; saves `results/results.json`
- `plot.py` — bar chart from `results.json`
