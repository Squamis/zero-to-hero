# Dev Log

Proof-of-study repo for the AI zero-to-hero learning roadmap. One directory per level, each with its own benchmark and a plot showing the deltas between techniques. AI-assisted with Claude as a building partner, not a ghostwriter.

## 2026-05-03

**Session goal**: Ship L1.7c (Best-of-N test-time compute), the first L1 micro-benchmark. Match L0's pattern: same task, era-boundary model, parallelized harness, plot the deltas. Then run the cross-era pairing on `gpt-3.5-turbo-instruct` to test the same thesis statement L0 used, one technique generation later.

**What I learned (Best-of-N test-time compute)**:

- **Best-of-N is flat on Mistral-7B-Instruct v0.1.** Across the full sweep (N = 1, 3, 5, 10, 20, 40 at T = 0.7), accuracy hovered at 38 to 44 percent on GSM8K-50. That's statistical noise around L0's 40 percent zero-shot CoT baseline at T = 0. 38x the cost for zero accuracy gain.
- **Best-of-N produces real lift on gpt-3.5-turbo-instruct.** Same sweep, same task, same prompt: 46 percent at N = 1 climbing to a 62 percent peak at N = 20, easing back to 60 percent at N = 40. Roughly +14 to +16 points from test-time compute alone.
- **The era boundary explains both.** Mistral-7B-Instruct's outputs at T = 0.7 converge to roughly the same answer paths, so majority-voting them is just N = 1 with extra cost. gpt-3.5-turbo-instruct, a pre-self-consistency-era completion model, has enough internal variance for majority voting to recover correct paths a single sample would have missed.
- **Same lesson as L0, one technique generation later.** L0 showed prompt-engineering deltas vanish on a model that already does CoT internally. L1.7c shows test-time-compute deltas vanish on a model that already produces enough internal variance that the correct path gets recovered most of the time. Each model generation absorbs the prior generation's technique into its default behavior. The harness layer keeps moving up.
- **Diminishing returns visible on GPT-3.5 too.** N = 20 was the peak; N = 40 came back down to 60 percent. Wang et al. used N = 40 for self-consistency, but on GSM8K-50 the curve plateaus by N = 20.
- **Cost scales exactly linearly with N on both models.** Straight line on the log-log cost panel. The interesting variable is what you get for that linear cost.

**What I learned (engineering)**:

- About 80 percent of L1 code is verbatim L0 reuse. The expensive part of L0 was getting the harness right (parallelization, persistence, model swapping); once that was solid, layering a new technique was small.
- New work was small and well-scoped: token-usage tracking in `client.py` (CompletionResult dataclass), `majority_vote()` helper in `grader.py`, a single `best_of_n_cot()` function in `techniques.py`, an N-sweep loop in `run.py`, and a two-panel curve plot.
- gpt-3.5-turbo-instruct is roughly 10x faster wall-clock than Mistral-7B-Instruct v0.1 through OpenRouter for the same prompt shape. Hosted endpoint vs OpenRouter-to-open-weights routing.
- Cost calibration: a full L1.7c sweep on Mistral was about $0.10 (1.16M tokens). Same sweep on gpt-3.5-turbo-instruct was about $1.50 to $2.00 (921K tokens, but pricier per token). Earlier "$0.50 to $1.00" estimate for the cross-era was wrong; the real number is $1.50 to $2.00.

**What I built**:

- New directory `zero-to-hero/L1/` mirroring the L0 layout: `client.py`, `data.py`, `grader.py`, `techniques.py`, `run.py`, `plot.py`, `README.md`.
- `client.py` returns a `CompletionResult` dataclass (text + prompt_tokens + completion_tokens + total_tokens) so cost is tracked at the call boundary. `complete_text()` preserves the L0 string-only signature for backward compat.
- `grader.py` adds a `majority_vote()` helper that takes a list of extracted answers, drops the Nones, and returns the most common answer (Counter insertion-order wins ties).
- `techniques.py` is a single `best_of_n_cot(question, n)` function. Inner-parallelism via ThreadPoolExecutor for the N samples; returns (predicted_answer, total_tokens) so the run loop can plot cost.
- `run.py` sweeps over `--ns` values (default `[1, 3, 5, 10, 20, 40]`), parallelizes problems with `--workers`, fans out N samples with `--inner-workers`, persists `results/results.json` after each N value so partial runs survive.
- `plot.py` is a two-panel line chart. Single-file mode plots one curve. Multi-file mode (mirrors L0's pattern) overlays one line per model on each panel; legend distinguishes them.
- L0 baseline (40 percent on Mistral) shown as a dashed reference line on the accuracy panel.

**Decisions made**:

- Stick with the L0 era-boundary pattern: open-weights model from the technique's canonization era as the build-path baseline, closed-API older completion model as the cross-era reference. Same shape as L0's Mistral-vs-GPT3.5 comparison.
- Zero-shot CoT as the base prompt (rather than few-shot CoT). Zero-shot CoT was Mistral's best L0 baseline at 40 percent; building on top of the strongest baseline isolates the test-time-compute contribution.
- Temperature 0.7 across the full sweep, matching Wang et al. 2022. Lower temperature kills the variance Best-of-N needs; higher destabilizes arithmetic.
- N values `[1, 3, 5, 10, 20, 40]` log-spaced. N = 5 matches L0's `self_consistency` point. N = 40 matches Wang et al.'s headline number.
- Default workers tuned to `--workers 8 --inner-workers 10` so the maximum concurrent OpenRouter calls is 80, comfortable margin under any rate limits.

**Benchmark results (50 problems, GSM8K test, seed=42, T=0.7)**:

`mistralai/mistral-7b-instruct-v0.1` (modern instruct, already CoT-trained):
- N=1: 42% (15K tokens, 147s)
- N=3: 40% (44K tokens, 155s)
- N=5: 40% (74K tokens, 195s)
- N=10: 44% (149K tokens, 184s)
- N=20: 40% (298K tokens, 383s)
- N=40: 38% (579K tokens, 672s)
- Total: ~1.16M tokens, ~29 min wall clock, ~$0.10

`openai/gpt-3.5-turbo-instruct` (pre-self-consistency-era completion model):
- N=1: 46% (12K tokens, 14s)
- N=3: 52% (35K tokens, 16s)
- N=5: 50% (57K tokens, 16s)
- N=10: 54% (116K tokens, 21s)
- N=20: **62%** (235K tokens, 38s) — peak
- N=40: 60% (467K tokens, 65s)
- Total: ~921K tokens, ~3 min wall clock, ~$1.50 to $2.00

**Comparison plot saved to** `L1/results/comparison.png`. The visual story: Mistral's curve hugs the L0 baseline horizontally; GPT-3.5's curve climbs from 46 percent to a 62 percent peak at N = 20 before easing off. The same divergence-shape as L0's Mistral-vs-GPT3.5 comparison, just sliced through the test-time-compute axis instead of the prompt-engineering axis.

**What the comparison proved (the L1 thesis statement)**:

- The "each generation absorbs prior techniques" claim is now confirmed at *two* technique generations, not just one. L0 confirmed it for prompt engineering; L1.7c confirms it for test-time compute.
- Mistral-7B-Instruct, a 2023 modern instruct model, internalized self-consistency-style internal variance enough that explicit Best-of-N on top adds nothing. The model already does this.
- gpt-3.5-turbo-instruct, a pre-self-consistency-era completion model from the same calendar window, has *not* internalized that variance. Explicit Best-of-N on top recovers it externally.
- This is the L1 thesis the rest of the level is built around: the layer the current frontier model doesn't yet do for you is where the technique's leverage lives. Move up the abstraction stack as the model absorbs each layer.

**Next session**:
- Walk L1.3 (Select). Best next mini-benchmark candidate: few-shot example selection (random vs similarity-retrieved vs hand-picked) on the same GSM8K-50 task.
- Or jump to the load-bearing synthesis benchmark: harness-as-durable-artifact across two open-weights models on OpenRouter (Mistral-7B-Instruct vs early Llama 3 8B Instruct) with one fixed harness. That's the L1 thesis statement most directly.
- Pin a snapshot of OpenRouter pricing in the L1 README so future cost estimates are calibrated.
- Decide whether to add Mistral results plus GPT-3.5 results plus comparison plot to L1/results/ (currently in tree) or .gitignore them and let users regenerate.

---

## 2026-05-02

**Session goal**: Walk L1 (context engineering) from the top. Process the canonical resources, populate lit notes, surface atomic notes, fix curriculum bugs, and align L1.2's video stack so the build path lines up with vendor-neutral practitioner material before scaffolding `zero-to-hero/L1/`.

**What I learned (context engineering)**:

- **Harness is the product, not the model.** Lance Martin and Drew Breunig converge on the same point from different angles: a well-built harness around a weaker model can outperform a frontier model used naively. Corollary: the harness is the durable artifact. If you can swap the model and the harness still works (or breaks loudly enough to teach you), you have actually built something. Companies whose value prop *is* the harness get walked past by the next model generation. This is the load-bearing claim the L1 benchmark will test.
- **Context poisoning over naive compaction.** When an agent fails on a tool call (wrong arguments, wrong tool, error response), the failed call should stay in the context window. Naive compaction summarizes it out, and the agent walks back into the same failure path. Gemini playing Pokémon is the canonical example. Compaction strategies need to discriminate: distill exposition, preserve failure traces.
- **Caching helps cost, not context rot.** API-side prompt caching is a billing optimization, not a quality knob. The fix for context rot is to actually shorten, restructure, or isolate the context. Treating caching as a quality fix masks the underlying problem.
- **Memory write is the sovereignty knob.** Read pathways are mostly mechanical (similarity, retrieval). The write pathway is where user agency lives. Claude requires explicit human invocation to write to memory; ChatGPT auto-writes. Auto-write silently shapes what the agent will recall later, removing user agency over their own memory layer.
- **Eval decomposition is a control mechanism for *me*, not for the AI.** Drew Breunig's framing: breaking "is the chatbot good?" into measurable sub-questions is not to help the AI, it is to maintain visibility over a system whose behavior is otherwise opaque. Evals are a control surface for the operator.
- **Single-agent vs multi-agent for deep research is unsettled, but probably on different axes.** Cognition's "Don't Build Multi-Agents" (Walden Yan) and Anthropic's "How we built our Multi-Agent Research System" appear to disagree, but Cognition's failure cases are *build* tasks where outputs must compose, while Anthropic's success cases are *retrieve* tasks where outputs are independently consumable. Lance Martin's synthesis (parallelize gathering, serialize writing) treats them as compatible at the workload-shape level.
- **The Bitter Lesson cuts both ways.** Add the minimum amount of structure needed to make the system work today, *and* actively remove that structure as the model improves. Most projects execute the first half and forget the second. The scaffolding that enabled v1 quietly becomes the bottleneck on v2.
- **A well-described index page beats heavy RAG a surprising amount of the time.** Lance Martin's empirical finding: a single index page listing every file with short descriptions often outperforms an embedding + vector-search + reranker pipeline on agentic-search tasks. Caveat: description quality is load-bearing; small drops cascade into wrong file picks.

**What I learned (curriculum / process)**:

- **Pre-check resource URLs before adopting them.** L1.1's canonical Anthropic post URL was a 404. The actual post lives at `/engineering/effective-context-engineering-for-ai-agents`, which is also L1.2's spine resource. So 1.1 and 1.2 had been pointing at the same post with 1.1 holding a dead link. Fixed both, deleted the orphan stub. Lesson for future curriculum work: verify every URL before adoption (already in the TA handbook, now actually applied).
- **Vendor-neutral practitioner walkthroughs beat vendor companion videos for the build path.** L1.2's original Anthropic companion video did not drill into the Write pattern despite the post's framing. Lance Martin's *Context Engineering for Agents* talk is structured around the four-pattern frame (write/select/compress/isolate) explicitly, with concrete walks through scratchpads, agent state, and persisting plans outside the window. Promoted Lance to L1.2 canonical, demoted Anthropic to a decision-history line.
- **Voice memo intake belongs in a sub-agent, not the main thread.** Voice memos are long enough that processing inline burns the parent context window for raw material the parent never needs to see. Saved as a standing operating rule for future sessions.
- **Per-task-unit parallelization is the right default for fan-out work.** When a piece of work decomposes into N independent units (per source, per atomic, per ingest), spawn N sub-agents in one batch instead of one big sub-agent doing all of them sequentially. Today's batches: 5 Drew atomics in parallel, 8 Lance atomics in parallel, 4 wiki ingests in parallel.

**What I built (curriculum-side, no benchmark code shipped today)**:

- **L1 ALT adopted as canonical.** Promoted the technique-spined L1 (write/select/compress/isolate organized) over the older resource-spined version. The archived original lives at `L1 — context engineering (archived resource-spine version).md` in the vault for reference.
- **L1.2 video stack rebuilt.** New canonical: Lance Martin, *Context Engineering for Agents* (LangChain), 63 min. New alt: Lance Martin + Yichao "Peak" Ji, *Context Engineering for AI Agents with LangChain and Manus*, 61 min. Anthropic *Building more effective AI agents* moved to a 2026-05-02 decision-history line with prior commentary preserved attached.
- **L0 synthesis layer expanded.** Added two Anthropic docs entries: the prompt-engineering overview (`/build-with-claude/prompt-engineering/overview`) and the Claude API overview (`/api/overview`). Closed-API, so reading material per the open-weights-on-build-path rule.
- **L3.2 origin-story companion added.** Anthropic's *Spotlight on Shopify, Code with Claude* flagged as the "where MCP came from" companion at L3.2. URL pin still TODO.
- **L4 benchmark expanded.** Added Lance Martin's three-way RAG vs index-page vs context-stuffing comparison as a per-technique benchmark slot to replicate on the vault corpus.
- **3 lit notes populated end-to-end** via voice intake (3 dictation runs across the day):
  - `Effective context engineering for AI agents Anthropic lit note` (the canonical L1 spine post, ~120 lines)
  - `Context Engineering for Agents by Lance Martin lit note` (the new L1.2 canonical video)
  - `Context Engineering for AI Agents LangChain and Manus lit note` (the new L1.2 alt video, created from scratch)
- **13 placeholder atomic notes written**, marked as Claude-generated for me to rewrite in my own voice:
  - From Drew Breunig (5): `harness is the product not the model`, `eval decomposition as a control mechanism`, `subagent is a new LLM call with a wrapper`, `engagement vs quick-task-solving is the AI design fork`, `parallelize across many small fast agents vs one large slow one`
  - From Lance Martin (8): `context poisoning keep failed tool calls in context`, `index page with file descriptions beats heavy RAG`, `deep research as gather-parallel coalesce-serial`, `caching helps cost not context rot`, `memory write is the sovereignty knob`, `the bitter lesson minimum structure then remove it`, `language being invented and lawyers congregating`, `buzzword construction recipe vs anti-context triple-threat`
- **4 wiki ingests** into the LLM Wiki, all bidirectionally cross-linked:
  - Lance Martin, *Context Engineering for Agents* (blog companion to the talk; `rlancemartin.github.io/2025/06/23/context_engineering/`)
  - Lance Martin, *Bitter Lesson* (`rlancemartin.github.io/2025/07/30/bitter_lesson/`)
  - Anthropic, *How we built our Multi-Agent Research System* (`anthropic.com/engineering/multi-agent-research-system`)
  - Cognition (Walden Yan), *Don't Build Multi-Agents* (`cognition.ai/blog/dont-build-multi-agents`)
  - The Cognition vs Anthropic unsettled debate is now fully wired bidirectionally in the wiki, with Lance's gather-parallel/coalesce-serial synthesis sitting between them.

**Decisions made**:

- **L1 ALT (technique-spined) is canonical.** The old resource-spined L1 is archived.
- **Lance Martin promoted, Anthropic demoted at L1.2.** Vendor-neutral practitioner content beats first-party companion video when the first-party content does not match the section's pattern.
- **L1 benchmark concept locked in.** Hold the L0 task (or a context-sensitive analogue) fixed, vary the *full context window* (system prompt design, few-shot selection, dynamic assembly, Best-of-N from L1.7c), and measure deltas. Run the same harness across at least two open-weight models on OpenRouter to demonstrate the swap-model corollary empirically. Build is upcoming.
- **Voice memo intake always runs via sub-agent.** Saved as a standing rule for future sessions.
- **No code shipped to the repo today.** L0 remains the only level with a benchmark in the repo; today was the alignment work that lets the L1 build start clean.

**Benchmark results**: none. No code change to the repo today.

**Next session**:
- Walk L1.3 (Select), L1.4 (Compress), L1.5 (Isolate), L1.6 (System prompt design), L1.7 (Reasoning-model context). Same announce → show inputs → run → show outputs → discuss rhythm.
- Pick the L1 era-boundary model (early Llama 3 8B Instruct or similar; verify against current OpenRouter catalog).
- Decide whether to keep GSM8K from L0 (clean comparison) or move to a more context-dependent task suite (longer-context QA, multi-doc synthesis) where context-window design has more lever.
- Scaffold `zero-to-hero/L1/` mirroring L0: client, data, grader, techniques, run, plot, README.
- Run a cross-technique / cross-era pairing per the TA handbook §6a: a multi-technique stack on an older model vs a single-technique frontier model on the same task. Measure cost-adjusted result.
- Patch open gaps in L1 as we walk: 1.4 standalone compaction resource, 1.6 Riley Goodside system-prompt-design URLs, 1.7a extended-thinking resource (current candidates rejected).

---

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
