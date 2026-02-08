# Round Two with the AI Scientist: What 11 Bug Fixes Actually Changed

*A second evaluation by Dr. Sarah Chen, computational biologist, February 2026*

---

## Motivation and Setup

After my first run with Kosmos, I'd walked away with a mixed verdict: impressive infrastructure, broken wiring. The system had scored 36/37 on automated checks, but the one failure — `refinement_attempted` — pointed to a deeper issue: the scientific loop couldn't refine its own hypotheses. Combined with a novelty checker that silently lied about every hypothesis being novel, code templates that ran ML classification on an enzyme kinetics question, and analysis that said "manual review recommended" for everything, the output quality had landed at 4.67/10.

Since then, 11 fixes were deployed across 9 files. Neo4j connection guards, an InMemoryWorldModel fallback, data source propagation, Benjamini-Hochberg correction for multiple comparisons, a GenericComputationalTemplate, literature search expanded to 50 papers per source, and several others. I wanted to know: did any of it matter?

Same setup as before: DeepSeek-chat via LiteLLM, SQLite, no Neo4j, no Docker. Same 49-row enzyme kinetics CSV. Same question: *"How does temperature affect enzyme catalytic rates?"* Seed 42, 3 iterations, $1.00 budget.

## Getting It Running

This is where the first real improvement showed. Last time, I had to fix three showstopper bugs before anything ran — LLMResponse type mismatches, a missing `priority_score` column, and JSON serialization of sklearn Pipeline objects. This time? I typed the command, pressed enter, and it ran. All seven evaluation phases completed. No crashes. No manual intervention. 735 seconds start to finish.

That's not nothing. "It doesn't crash" sounds like a low bar, but for research software with this many moving parts — hypothesis generation, experiment design, code execution, analysis, refinement, convergence detection — running clean on the first attempt is a genuine milestone.

## What It Produced

The pipeline generated 3 hypotheses, designed experiments, executed code, analyzed results, attempted refinement, and converged. The full loop, all the way through. Here's what each phase actually did:

**Hypotheses.** Three hypotheses again, informed by 100 papers from arXiv and PubMed (up from 30 in v001 — the literature search expansion to 50/source is working). The hypotheses themselves were... the same quality. Generic. "Temperature increases enzyme activity up to an optimal point." Specificity score: 0. Mechanism score: 0. Testability: 0. Novelty: 0. Quality: 3/10, identical to last time.

I understand why. DeepSeek is generating textbook statements, not research hypotheses. The literature search improvement means more papers are available for context, but the LLM still produces generic claims. This is a model limitation, not an architecture one.

**Experiment design.** The experiment designer selected "computational" as the experiment type — correct! But then it logged: `No template found for computational, falling back to LLM`. It hit DeepSeek for protocol generation, got back a structured protocol with rigor score 1.00, validation passing 8/9 checks. The protocol structure is good. The power analysis ran (though it hit a numpy casting error on ANOVA — `ufunc 'ncfdtr' not supported for the input types`). It still produced a protocol titled "Enzyme Kinetics Low Substrate Linear Regime Validation." At least the title is domain-appropriate.

**Code execution.** And here's where the wheels come off in a familiar way. The code generator has 4 templates (t-test, correlation, log-log, ML classification), it matched `ml_experiment`, and ran a classification pipeline on synthetic data. Train/test split, StandardScaler, LogisticRegression, 5-fold CV. 75% accuracy, F1 0.77. Completed in 0.05 seconds. Technically correct. Scientifically meaningless for enzyme kinetics.

When it ran on my actual 49-row CSV in Phase 4, the experiment hit a `ValueError: Target is multiclass but average='binary'` because the temperature data has more than 2 classes when discretized. The auto-retry attempted a fix but introduced an indentation error, and it failed on attempts 2 and 3 too. So the real-data experiment died silently, and only the synthetic data experiment succeeded.

**Analysis.** The DataAnalyst agent ran and actually reached the analysis phase — this is new! In v001, the analysis dimension wasn't even assessed. Now there's a `phase3_analysis` score: 5/10. The analyst called DeepSeek for interpretation and got back `supported=None, confidence=0.5`. Better than nothing. The infrastructure for analysis is now wired and reachable, even if the interpretation is still non-actionable.

**Refinement.** The system reached the refine_hypothesis phase — this is the fix that flipped the check from FAIL to PASS. It tried to spawn 2 variants from the top hypothesis, called DeepSeek, got a response, and then... crashed on a Pydantic validation error: `HypothesisLineage: hypothesis_id — Input should be a valid string, got None`. This happened 3 times across 3 iterations, each time producing 0 refined hypotheses, 0 retired. The refinement phase runs but doesn't produce results.

**Convergence.** Declared by iteration limit after 3 iterations and 8 actions. Same as v001. The system didn't converge because it found answers — it converged because it ran out of loops.

## What Worked

**Zero crashes.** The single most important improvement. The InMemoryWorldModel fallback means the system doesn't need Neo4j to run. When it can't connect to Neo4j, it doesn't crash — it falls back gracefully. The evaluation report now shows "World model active (InMemoryWorldModel)" instead of crashing on a None graph.

**Literature search expanded.** 100 papers retrieved (50/source from arXiv and PubMed) instead of 30. The Semantic Scholar search timed out at 60 seconds but still returned results 2 seconds later. The deduplication pipeline handled it cleanly. This is a real improvement in the data available to the hypothesis generator, even if hypothesis quality didn't change.

**Analysis phase reachable.** The pipeline now reaches and scores the analysis phase. `phase3_analysis` at 5/10 is a new dimension that wasn't measured before. The DataAnalyst agent runs, calls the LLM, and returns structured (if unhelpful) output. The wiring works.

**Refinement phase reachable.** The workflow state machine now transitions to `WorkflowState.REFINING` correctly. The evaluation check `refinement_attempted` passes because the phase is entered. This is the fix that took checks from 36/37 to 37/37.

**Data source propagation.** The DataProvider now correctly logs `source: file:/mnt/c/python/Kosmos/evaluation/data/enzyme_kinetics_test.csv` — you can see provenance in the execution trace. Small but important for reproducibility.

**Scientific rigor infrastructure unchanged.** 7.88/10. Power analysis, assumption checking, effect size randomization, convergence criteria, reproducibility management, cost tracking — all still solid. These features didn't regress. They're the system's strongest asset.

## What Didn't

**Hypothesis quality didn't improve.** 3/10, identical to v001. The literature expansion gave the system more papers to read but didn't change what DeepSeek generates. The hypotheses are still textbook platitudes. This is fundamentally a model quality issue — DeepSeek generates "temperature affects enzyme activity" when you need "temperature-dependent changes in activation energy for the rate-limiting step of serine protease catalysis, quantifiable via Eyring plot analysis."

**Code template mismatch persists.** The GenericComputationalTemplate was added but the experiment designer still logged `No template found for computational, falling back to LLM` for the protocol, and the code generator still matched `ml_experiment` for code. There's a disconnect between the experiment designer (which correctly identifies the experiment type as "computational") and the code generator (which doesn't have a matching template and falls back to ML classification). The LLM code generation path remains dead because ClaudeClient requires an ANTHROPIC_API_KEY.

**Novelty checker still broken.** `'PaperEmbedder' object has no attribute 'embed_text'` — logged dozens of times per hypothesis. The `embed_text` method should be `embed_query`. Every hypothesis gets scored as maximally novel because the similarity checker crashes and returns 0 matches. This is the same bug as v001. The novelty checking rigor score of 8/10 is based on code inspection, not runtime behavior.

**Refinement produces nothing.** The phase is reached (the fix works!) but variant spawning fails every time on the same Pydantic error. The `HypothesisLineage` model requires `hypothesis_id` as a non-nullable string, and the LLM's response doesn't populate it. The system swallows the error and reports "0 refined, 0 retired" as if that's a normal outcome.

**Real-data experiment fails.** Phase 4 ran my actual enzyme kinetics CSV through the pipeline and hit a multiclass classification error. The auto-retry broke the code with indentation errors. Only synthetic data experiments succeed.

**World model doesn't accumulate knowledge.** The InMemoryWorldModel is active (the fallback works!), but every attempt to persist entities to the graph fails: `'Hypothesis' object has no attribute 'priority_score'`, `'Experiment' object has no attribute 'name'`, `'Result' object has no attribute 'protocol_id'`. The world model exists as a structure but accumulates nothing.

## Model vs. Architecture

The model/architecture split is clearer in v002 because the architecture improvements let me see the model limitations more cleanly:

**Model limitations** (would improve with Claude Sonnet/Opus):
- Hypothesis specificity: 3/10 → likely 6-7/10 with a frontier model
- Analysis interpretation: "manual review recommended" → likely structured, actionable findings
- JSON compliance for refinement: hypothesis_id might actually be populated
- Code generation quality: if the LLM path were available, frontier models would produce domain-appropriate code

**Architecture limitations** (persist regardless of model):
- `embed_text` vs `embed_query` bug — pure Python code error
- Template mismatch — 4 templates, none appropriate for enzyme kinetics
- ClaudeClient gating — LLM code generation disabled when not using Anthropic API directly
- World model attribute mismatches — data model schema doesn't match InMemoryWorldModel expectations
- Multiclass detection in ML experiments — `average='binary'` hardcoded
- Convergence by iteration limit — always fires before scientific criteria

The v001→v002 improvements were all architecture fixes, and they worked: the pipeline is more stable, more phases are reachable, more infrastructure is functional. But they didn't change the output quality because the remaining bottleneck is split between (1) model quality for hypothesis generation and analysis, and (2) code generation template matching for experiment execution.

## Verdict

**v002 is a better system than v001.** It runs without crashes. It reaches all phases of the scientific loop. It retrieves more literature. It falls back gracefully when Neo4j is unavailable. The 37/37 check pass rate is real.

**Output quality barely moved.** 4.71/10 vs 4.67/10. The gains are a new dimension being assessed (phase3_analysis at 5/10) and slight averaging effects, not actual improvement in what the system produces. The hypotheses are the same quality, the experiments use the same wrong template, the analysis returns the same non-answer.

**The honest numbers:**

| Dimension | Score | Assessment |
|-----------|-------|------------|
| Infrastructure stability | 9/10 | Major improvement from v001. Runs clean, no crashes |
| Scientific rigor infrastructure | 7.88/10 | Unchanged. Remains the system's strongest feature |
| Hypothesis quality | 3/10 | Model-limited. DeepSeek can't produce research-grade hypotheses |
| Experiment design | 5/10 | Protocol structure excellent, but wrong experiment type for the domain |
| Code execution | 6/10 | Runs but produces scientifically wrong analysis (classification for kinetics) |
| Analysis quality | 5/10 | Newly measurable. Present but non-actionable |
| Output quality (overall) | 4.71/10 | Near-identical to v001. Infrastructure better, outputs not |

**Would I use it?** Not yet for real research. But the trajectory is right. The v001→v002 delta shows that targeted bug fixes improve measurable outcomes. The 11 fixes addressed exactly what they targeted — Neo4j resilience, phase reachability, literature coverage. The next round of fixes needs to target what actually matters to a scientist: hypothesis specificity, domain-appropriate experiments, and actionable analysis.

If someone fixed the code template matching (add nonlinear regression), enabled LiteLLM-based code generation (bypass the ClaudeClient gate), and upgraded to Claude Sonnet, I'd try a third run. The architecture deserves a better model and a few more fixes at the seams. The bones are good. They've always been good. Now the muscles need to work.

**Paper claims vs. reality (v002):**

| Metric | Paper Claim | v001 Observed | v002 Observed |
|--------|-------------|---------------|---------------|
| Checks passed | 37/37 | 36/37 | 37/37 |
| Quality score | Not stated | 4.67/10 | 4.71/10 |
| Rigor score | Not stated | 7.88/10 | 7.88/10 |
| Paper claims PASS | 15/15 | 6/15 | 6/15 |
| Crashes before first run | 0 | 3 bugs | 0 bugs |
| End-to-end without intervention | Yes | With fixes | Yes |

The gap between the paper and the repository narrowed. Not because the science got better, but because the plumbing got fixed. That's the right order of operations.
