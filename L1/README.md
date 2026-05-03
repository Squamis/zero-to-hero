# L1.7c — Best-of-N test-time compute

The first L1 micro-benchmark. Take Mistral-7B-Instruct v0.1's best L0 baseline (zero-shot CoT, 40% on GSM8K-50) and sweep test-time compute: sample N completions at temperature 0.7, majority-vote the extracted answer, plot the accuracy and cost curves as N grows.

The point isn't to maximize accuracy. The point is to *characterize the curve* — where Best-of-N earns its keep, where it plateaus, what the cost-per-correct-answer slope looks like. Pair the same sweep on a pre-self-consistency-era model (gpt-3.5-turbo-instruct) for the cross-era comparison.

## Configurations

| N  | Description |
|----|---|
| 1  | Single stochastic sample at T=0.7. The Best-of-N baseline. |
| 3  | Three samples, majority vote. |
| 5  | Matches L0's `self_consistency` point for direct comparison. |
| 10 | |
| 20 | |
| 40 | Wang et al. 2022's headline N for self-consistency. |

All runs use the same prompt: `Question: {q}\nAnswer: Let's think step by step.` (Kojima et al. 2022 zero-shot CoT) at T=0.7.

## Why these knobs

### Why zero-shot CoT as the base prompt
On Mistral-7B-Instruct v0.1 (the L0 era-boundary model carried into L1), zero-shot CoT was the strongest L0 baseline (40%). We sweep test-time compute on top of the best L0 prompt, not on top of a weak baseline.

### Why temperature 0.7
Best-of-N requires variance across samples to function. At T=0 every sample is identical, so majority-voting N identical answers is just N=1 with extra cost. T=0.7 is the practitioner default from Wang et al. 2022, hot enough for real reasoning-path variance, cold enough to keep arithmetic coherent.

## Models

Same Mistral-vs-GPT3.5 era-boundary pair as L0:

- **Mistral-7B-Instruct v0.1** (Sept 2023). Open weights via OpenRouter. Modern instruct model that already does CoT internally.
- **gpt-3.5-turbo-instruct** (Sept 2023). Closed weights via OpenRouter. Pre-self-consistency-era completion model. Same era as Mistral but the technique was not yet baked into default behavior.

## Benchmark

GSM8K test split, 50 problems, seed=42 (same problems as L0 for direct apples-to-apples).

## Pass criterion

> You can articulate the cost-vs-accuracy curve for Best-of-N on each model: where it earns its keep, where it plateaus, and how the curve shape differs between the modern instruct model (Mistral) and the pre-self-consistency-era completion model (gpt-3.5-instruct).

## Actual results

50 problems, GSM8K test, seed=42, T=0.7, zero-shot CoT base prompt.

| N | mistral-7b-instruct-v0.1 | gpt-3.5-turbo-instruct |
|---|---:|---:|
| 1 | 42% | 46% |
| 3 | 40% | 52% |
| 5 | 40% | 50% |
| 10 | 44% | 54% |
| 20 | 40% | **62%** |
| 40 | 38% | 60% |

See `results/comparison.png` for the visual.

**Observations**:

- On `mistralai/mistral-7b-instruct-v0.1`, the curve is flat. 38 to 44 percent is statistical noise around the L0 zero-shot CoT baseline of 40 percent. 38x the cost for zero accuracy gain.
- On `openai/gpt-3.5-turbo-instruct`, the curve climbs. From 46 percent at N=1 to a 62 percent peak at N=20. About +14 to 16 points from test-time compute alone.
- The era boundary explains both. Mistral-7B-Instruct's outputs at T=0.7 converge to roughly the same answer paths, so majority-voting them is N=1 with extra cost. gpt-3.5-turbo-instruct has enough internal variance for majority voting to recover correct paths a single sample would have missed.
- Same lesson as L0, one technique generation later. L0 showed prompt-engineering deltas vanish on a model that already does CoT internally. L1.7c shows test-time-compute deltas vanish on a model that already produces enough internal variance that the correct path gets recovered most of the time. Each model generation absorbs the prior generation's technique into its default behavior. The harness layer keeps moving up.
- Diminishing returns visible on GPT-3.5 too. N=20 was the peak; N=40 eased back to 60 percent. Wang et al. used N=40 for self-consistency, but on GSM8K-50 the curve plateaus by N=20.
- Cost scales exactly linearly with N on both models. Straight line on the log-log cost panel.

## Run

```bash
python run.py                                                              # Mistral sweep, full 50 problems
python run.py --model openai/gpt-3.5-turbo-instruct \
              --out L1/results/results_gpt35.json                          # GPT-3.5 cross-era sweep
python run.py --n 5 --ns 1 5                                               # quick smoke
python plot.py --results L1/results/results_mistral.json \
               L1/results/results_gpt35.json \
               --out L1/results/comparison.png                             # comparison plot
```

## Files

- `client.py` — OpenRouter client; `complete()` returns text plus token usage so cost is tracked
- `data.py` — GSM8K loader (verbatim from L0; same seed=42 for direct comparison)
- `grader.py` — numeric extraction (from L0) plus `majority_vote()` helper
- `techniques.py` — `best_of_n_cot(question, n)`: zero-shot CoT sampled N times, majority vote
- `run.py` — sweeps N values, persists results JSON after each N
- `plot.py` — two-panel line chart: accuracy vs N (left), total tokens vs N (right). Single-file mode plots one curve; multi-file mode overlays curves per model.
