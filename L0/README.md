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

## Actual results

Two models, same prompts, same 50-problem GSM8K subset (seed=42).

| Technique | mistral-7b-instruct-v0.1 | gpt-3.5-turbo-instruct |
|---|---:|---:|
| zero-shot | 38% | 36% |
| role | 22% | 40% |
| few-shot (answer-only) | 12% | 26% |
| zero-shot CoT | 40% | 42% |
| few-shot CoT | 36% | **80%** |
| self-consistency (N=5) | 38% | **84%** |

See `results/comparison.png` for the visual.

**Observations**:
- On `gpt-3.5-turbo-instruct` (a true pre-CoT-era completion model), the techniques work as the original papers describe — few-shot CoT doubles zero-shot, self-consistency adds another 4 points on top.
- On `mistralai/mistral-7b-instruct-v0.1` (a modern instruct model from the same era), the same techniques produce flat or negative deltas. The model already does CoT and self-consistency internally; layering more prompting on top doesn't help and sometimes interferes.
- Role prompting is model-dependent: -16 on Mistral, +4 on GPT-3.5-instruct.
- Few-shot answer-only is *destructive* on both: -26 on Mistral, -10 on GPT. The Wei et al. failure mode is real and generalizes.
- This is the core lesson of L0: **prompt engineering is the layer the current frontier model doesn't yet do for you. As models absorb techniques into their default behavior, the deltas vanish.**

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
