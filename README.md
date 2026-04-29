# zero-to-hero

Proof-of-study repo for the [AI zero-to-hero learning roadmap](https://github.com/Squamis/zero-to-hero) — one directory per level, each with its own benchmark and a plot showing the techniques' deltas.

The whole point of the curriculum is "you don't graduate a level until your benchmark shows the level is doing what it claims." This repo is where the benchmarks live.

## Layout

- `L0/` — Prompt engineering. GSM8K-50 across zero-shot, role, few-shot, zero-shot CoT, few-shot CoT, self-consistency.
- `L1/`+ — coming as the curriculum progresses.

## Running L0

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your OpenRouter key
python L0/run.py            # full 50-problem benchmark
python L0/plot.py           # generates L0/results/accuracy.png
```

See `L0/README.md` for the level's design notes.

## Why an old model?

Each level's model is chosen to match the era the techniques were developed in. L0's prompt-engineering techniques (CoT, few-shot, self-consistency) were canonized in 2022–early 2023; the deltas are most visible on a model from that period. We use **Mistral-7B-Instruct v0.1** (Sept 2023) via OpenRouter — small enough that the techniques visibly move the needle, and from the exact window when this prompt-engineering toolbox was being formalized. A 2026 frontier model would ace zero-shot GSM8K and erase the lesson.
