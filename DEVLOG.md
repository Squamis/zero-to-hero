# Dev Log

Proof-of-study repo for the AI zero-to-hero learning roadmap. One directory per level, each with its own benchmark and a plot showing the deltas between techniques. AI-assisted with Claude as a building partner, not a ghostwriter.

## 2026-04-29

**Session goal**: Set up the zero-to-hero project on GitHub. Build out L0 (prompt engineering) end-to-end: client, six techniques, GSM8K-50 benchmark, plot. Use an open-weight model on OpenRouter and stay era-appropriate to the techniques.

**What I learned (prompt engineering)**:
- Each model generation tends to absorb the prior generation's prompt-engineering techniques into its default behavior. Modern instruction-tuned models do CoT spontaneously without being asked. Reasoning models internalize self-consistency. Today's top-shelf prompt techniques become tomorrow's default model behavior.
- The corollary: prompt engineering as a discipline is always "the layer the current frontier model doesn't yet do for you." The techniques don't disappear, they move up the abstraction stack.
- Mistral-7B-Instruct v0.1 (Sept 2023) already produces spontaneous step-by-step reasoning on math problems, even with a bare zero-shot prompt. The `Question:/Answer:` template was enough to elicit a 91 + 182 = 273 trace.
- Role prompting affects style and tone, not capability. It can even hurt — the "expert mathematician" framing made the model produce more confident-sounding output and silently swap a `+` for a `*` mid-calculation, returning 32,864 on a problem with gold = 273.
- Few-shot with answer-only exemplars is *worse* than zero-shot on reasoning tasks. The format trains the model to commit to a number before reasoning, then rationalize backwards. This is exactly the failure Wei et al. flagged in the original CoT paper.
- "Let's think step by step" (Kojima et al. zero-shot CoT) is the cheapest reliability win in the toolbox.
- Few-shot CoT (Wei et al.) is tighter than zero-shot CoT because the exemplars teach both reasoning style AND output format.
- Self-consistency only earns its keep when the model is uncertain enough to produce variance across samples. On problems the model is solid on, all 5 samples agree and you've spent 5x the tokens for no gain. The technique is insurance against variance, not a free accuracy boost.

**What I learned (engineering)**:
- OpenRouter is sparse on truly base / non-instruct models. The only legit pre-CoT-era option is `openai/gpt-3.5-turbo-instruct` (closed weights). For open-weight, you're stuck with instruction-tuned models that already do CoT to some degree.
- The OpenAI SDK can be pointed at OpenRouter by setting `base_url="https://openrouter.ai/api/v1"`. Same `chat.completions.create` interface.
- Sequential API calls are the wrong default for benchmarks. Each problem is fully independent — `ThreadPoolExecutor` with `max_workers=10` cuts wall-clock 10x trivially. Self-consistency's N samples per problem are also independently parallelizable.
- HuggingFace `datasets` library has GSM8K natively: `load_dataset("gsm8k", "main", split="test")`. Gold answers end with `#### <number>`.
- GSM8K grading is straightforward: extract the last number after explicit cues (`####`, `answer:`, `=`, `\boxed{}`), fall back to the last number in the text, compare with tolerance 1e-3.
- Era-matching the model to the techniques is the lesson-preserving choice. Run L0 prompts on a 2026 frontier model and the deltas vanish — the model is already doing every technique internally.
- `python3-venv` isn't on this Ubuntu install, but `uv venv` works without ensurepip.

**What I built**:
- New repo: github.com/Squamis/zero-to-hero
- Top-level: README.md, .env.example, .gitignore, requirements.txt, DEVLOG.md
- `L0/client.py` — OpenRouter wrapper around the OpenAI SDK, model id pulled from .env
- `L0/data.py` — GSM8K loader, samples N problems from the test split with a fixed seed
- `L0/grader.py` — extract numeric answer from model output (cue-based regex with fallback to last number), compare against gold with tolerance
- `L0/techniques.py` — all six L0 techniques as functions sharing the same `complete()` call:
  - `zero_shot` — bare `Question:/Answer:` baseline
  - `role_prompt` — "You are an expert mathematician..."
  - `few_shot` — 4 hand-picked exemplars from GSM8K train, answer-only
  - `zero_shot_cot` — Kojima's "Let's think step by step"
  - `few_shot_cot` — same exemplars as `few_shot` but with reasoning shown (Wei et al. 2022)
  - `self_consistency` — few-shot CoT, sampled N=5 at temp=0.7, majority vote on extracted answer (Wang et al. 2022)
- `L0/run.py` — benchmark runner. Loops techniques, parallelizes problems with ThreadPoolExecutor, persists results.json after every technique so partial runs survive interruption
- `L0/plot.py` — matplotlib bar chart of accuracy per technique, saved to L0/results/accuracy.png
- `L0/README.md` — level-specific design notes (techniques, model, benchmark, pass criterion)
- Live walkthrough script that runs all 6 techniques on a single GSM8K problem and prints the actual model output for each — pedagogy on demand
- Vault concept notes: `[[role prompting]]` and `[[few-shot prompting]]` with lessons distilled from the walkthrough, including failure-case evidence
- Roadmap note edits: wikilinks for all L0 techniques (`[[zero-shot prompting]]`, `[[few-shot prompting]]`, `[[role prompting]]`, `[[chain of thought]]`, `[[self-consistency]]`, etc.) and a callout explaining why this level uses a 2023 model (the "each generation absorbs prior techniques" observation)

**Decisions made**:
- Stuck with open-weight `mistralai/mistral-7b-instruct-v0.1` over closed `openai/gpt-3.5-turbo-instruct`. The closed model would show cleaner deltas (it doesn't spontaneously CoT), but open-weight is a hard constraint from the curriculum.
- Originally picked Llama-2-13B-chat for era match, but Llama 2 endpoints are deprecated on OpenRouter. Mistral-7B-Instruct v0.1 (Sept 2023) is an even better era match — exactly the window when CoT/self-consistency were being canonized.
- 50 GSM8K problems sampled with seed=42. Small enough to iterate quickly on technique implementations, large enough to show meaningful deltas. Full GSM8K (1319 problems) costs about $1.20 if we ever want to scale up.
- N=5 for self-consistency. The Wang et al. paper used N=40, but N=5 is enough for educational purposes — the lesson is the *mechanism*, not maxing accuracy.
- Greedy decoding (temp=0) for everything except self-consistency (temp=0.7). Matches the original papers.
- Started sequential, parallelized after first run was clearly bottlenecked by per-call latency. ThreadPoolExecutor over async — simpler with the sync OpenAI SDK.
- Saved API key by copying from `realestate-team-agent/.env` (the `hermes-agent/.env` one was 401-revoked).
- 4 hand-picked few-shot exemplars from GSM8K train — fixed, not retrieved. Cross-reference with the Wei et al. paper conventions.
- Used `uv venv` instead of `python3 -m venv` (system Python lacks ensurepip).

**Benchmark results (parallelized, 50 problems, GSM8K test, seed=42)**:

`mistralai/mistral-7b-instruct-v0.1` (Sept 2023, modern instruct, already CoT-trained):
- zero-shot: 38%
- role: 22% (down 16 points — *role prompting actively hurt*)
- few-shot (answer-only): 12% (down 26 points — *the Wei et al. failure mode in the wild*)
- zero-shot CoT: 40% (+2)
- few-shot CoT: 36% (-2)
- self-consistency: 38% (no change)

Total wall-clock: 703s (~12 min). Cost: ~$0.05.

`openai/gpt-3.5-turbo-instruct` (Sept 2023, completion model, NOT CoT-trained — closed weights, ran for comparison):
- zero-shot: 36%
- role: 40% (+4 — *role helped here, opposite of Mistral*)
- few-shot (answer-only): 26% (-10)
- zero-shot CoT: 42% (+6)
- few-shot CoT: 80% (+44 — *technique works as advertised in the original papers*)
- self-consistency: 84% (+48 — *the technique earns its keep when there's variance*)

Total wall-clock: 58s. Cost: ~$0.65.

**Comparison plot saved to** `L0/results/comparison.png`. The visual story: on the first four techniques both models are roughly tied at ~30-40%. On few-shot CoT and self-consistency, GPT-3.5-instruct shoots up to 80% / 84% while Mistral stays flat at 36% / 38%. The divergence is the thesis.

**What the comparison proved (the hypothesis from the morning, now empirically tested)**:
- The "each generation absorbs prior techniques" claim is real. On the modern instruct model (Mistral), prompt-engineering techniques produce flat or *negative* deltas — the model already does CoT and self-consistency internally, so layering more prompting on top does nothing or interferes with the model's own behavior.
- On the pre-CoT-era completion model (gpt-3.5-turbo-instruct), the same techniques produce dramatic deltas: few-shot CoT *doubled* zero-shot accuracy. Self-consistency added another +4 points on top.
- Role prompting is the most context-dependent: it *hurt* Mistral by 16 points but *helped* GPT-3.5-instruct by 4 points. The walkthrough lesson "role helps with style not capability" is too coarse — it should be "role's effect depends on whether the model already has a default tuned persona; if it does, role can interfere; if it doesn't, role gives it useful framing." Worth refining in the vault note.
- Few-shot answer-only hurt both models, dramatically on Mistral (-26) and meaningfully on GPT-3.5-instruct (-10). The Wei et al. failure mode generalizes across the era boundary.

**Next session**:
- Write the remaining concept notes with the empirical numbers backing them up: `[[zero-shot prompting]]`, `[[chain of thought]]`, `[[self-consistency]]`
- Refine the `[[role prompting]]` note with the model-dependent nuance from the GPT comparison
- Update L0/README.md with numbers
- Push everything (scaffold + Mistral results + GPT results + comparison plot + DEVLOG)
- Begin L1 (context engineering) — the data is in, L0 is validated
