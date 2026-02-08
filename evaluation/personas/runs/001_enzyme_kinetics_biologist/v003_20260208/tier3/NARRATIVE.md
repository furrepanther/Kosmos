# Third Time's the Charm? What v003 Actually Changed

*A third evaluation by Dr. Sarah Chen, computational biologist, February 2026*

---

## Motivation and Setup

After v002 I'd said: fix the code template matching, enable LiteLLM-based code generation, and I'd try a third run. Seven more fixes shipped — targeting novelty checking, code templates, error recovery, and hypothesis refinement. The commit message said "Fix 7 evaluation findings to improve scientific rigor." Time to see if that translated into output I'd actually trust.

Same setup again: DeepSeek-chat via LiteLLM, SQLite, no Neo4j, no Docker. Same 49-row enzyme kinetics CSV. Same question: *"How does temperature affect enzyme catalytic rates?"* 3 iterations, $1.00 budget. The run completed in 795 seconds — about 13 minutes. No crashes, exit code 0, 37/37 checks passing. Third run in a row with a clean bill of health on the infrastructure side.

## Getting It Running

One command, no intervention. This is now the baseline expectation, not a milestone. The system initialized, loaded 114 scientific skills, warned about 18 missing biology-specific ones (cellxgene, pymol-visualization, etc. — still not installed), connected to the database, failed to reach Neo4j, fell back to InMemoryWorldModel, and started the research cycle. All of this happened in under 30 seconds. The plumbing works.

## What It Produced

The pipeline ran all seven evaluation phases. Here's what happened in the parts that matter.

**Phase 2 — the single-iteration smoke test — broke.** Not in a way the checks caught, but in a way that matters. The experiment designer tried three times to generate a protocol for the top hypothesis and crashed each time with the same error:

```
ValidationError: Variable.values — Input should be a valid list, got 'Variable (from dataset)'
```

DeepSeek returned a string where the `Variable` Pydantic model expected a list of values. Three retries, same error. The error recovery system kicked in — and then got stuck. It fired `NextAction.ERROR_RECOVERY` 20 times in a row without doing anything because the research director doesn't know how to handle that action type. It just logs `Unknown action: NextAction.ERROR_RECOVERY` and loops. The workflow ended in `WorkflowState.ERROR` after burning through 22 action slots doing nothing useful.

The evaluation still reports this phase as PASS because the checks only verify: director created, plan generated, workflow started, hypotheses generated, workflow advanced, no AttributeErrors. The system did advance — into an error state. The check `workflow_advanced` reports "Final state: error" and passes. That's technically correct but scientifically misleading. Phase 2 is testing whether the pipeline can complete one iteration, and it can't.

**Phase 3 — the 3-iteration full loop — succeeded.** Different question ("substrate concentration and enzyme reaction velocity"), and this time the experiment designer managed to produce a protocol on its first attempt. Title: "Temperature-Dependent Cutinase Activity via Molecular Dynamics Simulation." Rigor score: 1.00, validation passing 8/8 checks. Power analysis ran correctly — ANOVA for 7 groups, t-test with Bonferroni correction, recommended n=31 per group. The protocol structure is properly scientific.

The code generator used the `generic_computational` template. This is new from the v002 fixes — last time it fell back to `ml_experiment` and ran a classification pipeline on enzyme kinetics data. Now it's running a template that's at least domain-neutral. The code executed in 0.01 seconds, which tells you it's running synthetic data through a template, not actual molecular dynamics. But the template is appropriate for the question.

Analysis ran. The DataAnalyst agent interpreted the results and concluded the hypothesis was not supported (supported=False, confidence not stated). Then the refiner kicked in, spawned 2 variant hypotheses, and the system completed 3 iterations with 8 total actions before converging by iteration limit. The loop works. All phases were reached: generate, design, execute, analyze, refine, converge.

**Refinement actually produced variants.** This is a genuine improvement from v002. Last time, refinement was reachable but crashed every time on a Pydantic validation error (`HypothesisLineage: hypothesis_id — Input should be a valid string, got None`). This time, the refiner spawned 2 variants per iteration — 4 total across 2 refinement cycles. The hypothesis pool grew from 3 to 9. The variants have IDs, they're stored in the database, they're logged. The refinement wiring is now functional.

There's a non-critical issue: every hypothesis fails to persist to the knowledge graph with `'Hypothesis' object has no attribute 'parent_hypothesis_id'`. The InMemoryWorldModel expects an attribute the Hypothesis model doesn't have. This is a schema mismatch between the world model and the data model, not a pipeline-breaking issue — the hypotheses exist in the SQL database, they just don't make it to the graph.

**Literature search scaled.** 150 papers retrieved (50 from each of arXiv, Semantic Scholar, PubMed), 149 after deduplication. The novelty checker ran against 66-78 existing hypotheses in the database, found 0 similar papers via vector search (the ChromaDB collection is empty — papers aren't being embedded), and scored each hypothesis. The novelty infrastructure works but operates in a vacuum.

## What Worked

**Refinement is functional.** v001: not reachable. v002: reachable but crashes. v003: runs, spawns variants, stores them. This is the most meaningful improvement across all three runs. A scientific loop that can't refine its hypotheses isn't a loop — it's a one-shot generator. Now it loops.

**Code template matching improved.** The `generic_computational` template replaced the `ml_experiment` fallback for computational experiment types. Running a generic computation is better than running logistic regression on enzyme kinetics data. It's still not great — the template produces synthetic results in 0.01s, not real analysis — but at least it's not actively wrong.

**Error recovery fires.** When the experiment designer fails, the system detects it, retries with exponential backoff (2s, 4s), and after 3 failures transitions to an error state. In v001/v002 this wasn't tested. The mechanism exists. It just doesn't recover — it gets stuck in a loop of unhandled `ERROR_RECOVERY` actions.

**Zero crashes across all phases.** 37/37 checks. All seven phases complete. No manual intervention. Three runs in a row with this result. The infrastructure is stable.

## What Didn't

**Phase 2 is broken in a way the checks don't catch.** The single-iteration smoke test hit a `Variable` Pydantic validation error on every retry and ended in `WorkflowState.ERROR`. The error recovery loop fired 20 no-op actions. This is a regression from v002, where Phase 2 at least completed its iteration (albeit with wrong experiment types). The Variable parsing assumes DeepSeek will return a list for `values` but it returns a string like `"Variable (from dataset)"`. This is the same class of problem as v002's refinement crash — the LLM returns data that doesn't match the Pydantic schema — but in a different location.

**Hypothesis quality unchanged.** 3/10, for the third consecutive run. Specificity: 0, mechanism: 0, testability: 0, novelty: 0. The scoring is keyword-based (does the hypothesis mention specific mechanisms? quantitative predictions? testable conditions?) and DeepSeek consistently produces generic statements. One hypothesis from Phase 3: "At low substrate concentrations (below 1% of Km), enzyme reaction velocity follows first-order kinetics." That's a textbook definition, not a hypothesis. The literature context of 150 papers isn't helping because DeepSeek doesn't synthesize it into novel predictions.

**Quality score dropped.** 4.4/10, down from 4.71 in v002. The cause: Phase 2's experiment design and code execution scores are missing (the phase errored out before reaching those stages). When you average fewer dimensions, the score shifts. The dimensions that do appear are identical to v002.

**World model is a black hole.** Every entity — hypothesis, experiment, result — fails to persist to the InMemoryWorldModel graph. The attribute mismatches are consistent: `'Hypothesis' object has no attribute 'parent_hypothesis_id'`, `'Result' object has no attribute 'status'`. The fallback from Neo4j works (the system doesn't crash), but the world model accumulates nothing. It's a facade.

**Novelty checker runs against an empty vector store.** The ChromaDB collection has 0 papers. The novelty checker searches for similar papers via vector embeddings, finds none, then falls back to comparing against existing hypotheses in the SQL database (where it finds 66-78). The literature papers (150 of them!) are never embedded. So the novelty score is based purely on hypothesis-to-hypothesis similarity, not hypothesis-to-literature similarity.

**Paper claims held at 6/15.** Same 6 PASS, 8 PARTIAL, 1 BLOCKER as v001 and v002. The BLOCKER is the 79.4% accuracy benchmark — no test dataset exists to validate it. The PARTIALs are claims about scale (166 rollouts, 42,000 lines of code, 1,500 papers) that can't be verified in a 13-minute run.

## Model vs. Architecture

The pattern is the same as v002, just clearer:

**Model limitations** (would improve with Claude Sonnet/Opus):
- Hypothesis quality: 3/10. A frontier model would produce testable, mechanism-specific hypotheses
- Variable parsing: DeepSeek returns strings where lists are expected. A better model would follow the schema
- Analysis interpretation: supported=False with no confidence score. A better model would explain why

**Architecture limitations** (persist regardless of model):
- `ERROR_RECOVERY` action handler doesn't exist — the system loops 20 times doing nothing
- `parent_hypothesis_id` attribute missing from Hypothesis model — world model can't persist anything
- ChromaDB collection stays empty — papers are searched but never embedded
- `generic_computational` template runs in 0.01s on synthetic data — not real analysis
- Convergence by iteration limit — always fires before scientific convergence

The v002 → v003 delta is smaller than v001 → v002. The easy wins (crash prevention, phase reachability) were already captured. What's left is the harder stuff: making the LLM produce research-grade outputs, making the code templates do real computation, and making the world model actually accumulate knowledge.

## Verdict

**v003 is marginally better than v002.** Refinement works now — that's real. The code template is less wrong. But Phase 2 regressed, the quality score dropped, and the headline metrics (rigor, paper claims) didn't move.

| Metric | v001 | v002 | v003 | Trend |
|--------|------|------|------|-------|
| Checks passed | 36/37 | 37/37 | 37/37 | Stable |
| Quality score | 4.67/10 | 4.71/10 | 4.4/10 | Down (measurement artifact) |
| Rigor score | 7.88/10 | 7.88/10 | 7.88/10 | Flat |
| Paper claims PASS | 6/15 | 6/15 | 6/15 | Flat |
| Crashes | 3 bugs | 0 | 0 | Stable |
| Refinement | Not reachable | Crashes | Works | Improved |
| Code template | Wrong (ML) | Wrong (ML) | Neutral (generic) | Improved |
| Error recovery | Not tested | Not tested | Fires but loops | New finding |

The honest assessment: three rounds of fixes have taken Kosmos from "crashes on first run" to "runs cleanly but produces textbook-level output." The infrastructure trajectory is right. But the output trajectory is flat. The evaluation framework itself is part of the problem — it gives 37/37 PASS to a run where Phase 2 ends in an error state. The checks measure whether phases are reached, not whether they produce good science.

**What would actually move the needle:**

1. **Fix the Variable parsing** — when the LLM returns a string for `values`, wrap it in a list. 10-minute fix, prevents Phase 2 from erroring out.
2. **Handle ERROR_RECOVERY** — add a case for `NextAction.ERROR_RECOVERY` in the research director's action dispatch. Currently it loops forever.
3. **Embed papers into ChromaDB** — the 150 papers from literature search need to be vectorized and stored so the novelty checker can use them.
4. **Add `parent_hypothesis_id` to the Hypothesis model** — one attribute, fixes all world model persistence.
5. **Try a better model** — Claude Sonnet via the existing LiteLLM path. The architecture can handle it. The question is whether the model can produce output worth handling.

I'd run v004 if fixes 1, 2, and 5 were implemented. The architecture has been stabilized across three iterations. It's time to test it with a model that can write a real hypothesis.
