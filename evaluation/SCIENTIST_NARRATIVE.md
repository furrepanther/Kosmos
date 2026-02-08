# I Tried to Use an AI Scientist for Enzyme Kinetics Research. Here's What Actually Happened.

*A narrative evaluation by a computational biologist, February 2026*

---

## Who I Am and Why I Tried This

I'm a computational biologist with enough programming background to be dangerous — I can write Python, wrangle data in pandas, and set up a conda environment without too much cursing. I read the Kosmos paper (arXiv:2511.02824v2) when it came out in November 2025 and was genuinely intrigued. The claims were bold: an autonomous AI scientist that could generate hypotheses, design experiments, execute code, analyze results, and iterate — all without human intervention. Seven validated discoveries. Four to six months of expert-equivalent work. A scientific rigor score of 79.4%.

I had a real question I wanted to explore: how temperature affects enzyme catalytic rates. It's well-trodden ground — Arrhenius kinetics, thermal denaturation, the bell-curve of activity vs. temperature — but that's precisely why I picked it. If the system couldn't find the temperature optimum at 37°C and the denaturation cliff above 42°C, it wasn't finding anything.

My setup was modest: DeepSeek-chat via LiteLLM (about $0.001 per thousand tokens), SQLite for persistence, no Neo4j graph database, no Docker sandbox. I had a 49-row enzyme kinetics CSV with temperature, activity, pH, substrate concentration, and replicates. I wanted to hand the system my data and a question and see what came back.

## Getting It Running

Three bugs had to be fixed before anything worked at all.

**Bug 1: The LLMResponse type mismatch.** Every agent crashed the moment it tried to call `.strip()` on the LLM response. The LLM client returned an `LLMResponse` object, not a raw string. Every agent in the system assumed it was getting a string. This is the kind of bug that tells you the end-to-end pipeline has never been run — each component was tested with mocks, but nobody wired them together and pressed go.

**Bug 2: The missing `priority_score` column.** The experiment designer crashed when trying to convert hypotheses into experiments because the database schema didn't include a `priority_score` field that the code expected. A simple schema-vs-code mismatch — the kind of thing a single integration test would have caught.

**Bug 3: JSON serialization failure.** When an ML experiment ran successfully, the system tried to store a scikit-learn Pipeline object directly in the SQLite database. JSON can't serialize a Pipeline. The experiment ran, produced results, and then those results vanished into a traceback. Silently. No warning, no fallback storage, just gone.

These are the kinds of bugs you'd expect in research software that has been developed module-by-module but never exercised end-to-end with a real model against a real database. I don't say this to be unkind — I've shipped worse in my own research code. But it means the paper's claims were tested against a version of the software that is materially different from what's in the repository.

After the fixes, the pipeline ran. An automated evaluation suite hit 36 of 37 checks (97% pass rate). The system was functional, if not exactly impressive.

## What the System Actually Produced

I asked it: *"How does temperature affect enzyme catalytic rates?"*

**Hypotheses.** The system generated three, drawing on 30 papers from Semantic Scholar, arXiv, and PubMed for context:

1. Enzyme catalytic rates increase with temperature up to an optimal point, following Arrhenius-type thermal activation kinetics.
2. Calcium-binding enzymes undergo conformational changes at elevated temperatures that alter substrate binding affinity (decreased Km).
3. Sustained exposure to temperatures above 45°C causes irreversible thermal denaturation, reducing specific activity by >50%.

Scientifically literate? Yes. Novel? No. These are textbook statements, not research hypotheses. They lack specificity — which enzyme, which substrate, what quantitative prediction, what mechanism to distinguish from alternatives. The automated quality assessment scored them 3/10 across specificity, mechanism, testability, and novelty. They read like the introduction to an undergraduate lab report, not a research proposal.

**Experiment design.** The system achieved a rigor score of 1.00 on protocol structure — meaning the infrastructure for good experimental design is there. But only 1 of the 3 hypotheses actually got tested. The other two never made it to the execution phase before the system declared convergence.

**Code generation.** This is where things got interesting, in the wrong way. The code generator has four built-in templates: t-test comparison, correlation analysis, log-log scaling, and ML classification. For my enzyme kinetics question, it matched the ML template and ran a classification pipeline — train/test split, StandardScaler, 5-fold cross-validation. It completed in 0.37 seconds with 75% accuracy and an F1 of 0.77. Technically functional, but a classification model is not the right tool for a temperature-activity relationship. Nobody would design this experiment for this question.

**Analysis.** The DataAnalyst agent asked DeepSeek to interpret the results. The response came back: `supported=None`, `confidence=0.5`. No actual interpretation — just "manual review recommended for all findings." The system couldn't parse the LLM's response into its expected structure, so it returned a default. A rubber stamp that says "I don't know."

**Convergence.** The system ran 3 iterations and 9 total actions, then declared "converged" because it hit the iteration limit. Not because it reached scientific convergence — because it ran out of loops. The convergence detector has sophisticated criteria (novelty decline, diminishing returns, cost-per-discovery thresholds), but in practice, the iteration limit fires first every time.

## What Worked Well

Here's the thing that surprised me: the *infrastructure* for good science is genuinely impressive. The scientific rigor scorecard came in at 7.88/10, and that number is earned.

**Power analysis.** There's a 525-line `PowerAnalyzer` module that adjusts sample sizes based on test type (t-test, ANOVA, correlation, regression, chi-square) and desired statistical power. It knows that a correlation test needs different sample sizes than a two-sample t-test. This is more sophisticated than what most graduate students do.

**Effect size randomization.** When generating synthetic data for experiments, the system doesn't just hardcode a medium effect. It randomizes: 30% null effects, 20% small, 20% medium, 30% large. This prevents the circular validation problem where every experiment is guaranteed to find significance. Someone thought carefully about this.

**Assumption checking.** The code templates embed Shapiro-Wilk normality tests and Levene's test for homogeneity of variance directly in the generated experiment code. If the data violates normality assumptions, the code knows to flag it.

**Multi-format data loading.** CSV, TSV, Parquet, JSON, JSONL — all five formats work. The `DataProvider` class handles them cleanly with proper error messages.

**Cost tracking and budget enforcement.** The system tracks API costs per call and enforces hard budget stops with a `BudgetExceededError`. In a world where a runaway loop could burn through $500 of API credits, this is a genuinely important safety feature.

**Reproducibility seeds.** A `ReproducibilityManager` sets seeds for Python's random module, NumPy, PyTorch, and TensorFlow when configured. It also captures comprehensive environment information for replication.

**The architecture itself.** The research loop — hypothesize, design, execute, analyze, refine, converge — is the right loop. It's what a good researcher does, just formalized. The workflow state machine has proper transitions, rollback handling, and action tracking. The bones are good.

## What Didn't Work

**The novelty checker is broken.** It exists — 250+ lines of code that compute semantic similarity against existing literature using the SPECTER embedding model. When the system ran, the NoveltyChecker initialized, loaded the SPECTER model onto CUDA, found 0 similar papers via vector search, and then crashed 45 times in rapid succession with: `'PaperEmbedder' object has no attribute 'embed_text'`. The method should be `embed_query`. Because the error is caught and swallowed, every hypothesis passes as "novel." The checker runs, fails, and lies about it.

**Hypothesis refinement silently fails.** After analyzing results, the system attempts to refine hypotheses — spawn variant hypotheses based on what was learned. In our run, the refiner initialized, tried to spawn 2 variants, hit a Pydantic validation error (`HypothesisLineage` model), and returned 0 refined hypotheses, 0 retired. No warning surfaced to the user. The system just moved on as if refinement had been considered and rejected, when in fact it crashed.

**Only 1 of 3 hypotheses was tested.** The system generated three hypotheses, designed experiments for them (with multiple retries due to errors), executed one, analyzed it, tried to refine it, failed, and converged. Two hypotheses never got their day in court. This is a loop control problem — the system doesn't round-robin through its hypothesis pool.

**Code generation fell to the wrong template.** The four built-in templates are pattern-matched against the hypothesis and research question. For enzyme kinetics, it matched `ml_experiment` — a classification pipeline. Not a dose-response curve, not a nonlinear regression, not even a simple correlation. The LLM-based code generation path was disabled because the Anthropic API key wasn't set (we were using LiteLLM/DeepSeek, not Claude directly). So the system fell to template matching, and the template was wrong for the question.

**Analysis is a rubber stamp.** When the DataAnalyst can't parse the LLM's interpretation into a structured `ResultInterpretation`, it returns `supported=None` with `confidence=0.5` and "manual review recommended." This happened in every run. The analysis phase exists but produces no actionable output.

**Neo4j world model not functional.** The `Neo4jWorldModel` class exists and the paper describes the world model as a "central coordination hub." But `create_world_model` can't be imported from the factory module. The knowledge graph features are architecturally present but not wired in.

**Report generation broken.** The Summarizer module — which would produce the final research report with citations — isn't importable. The end of the pipeline is a dead end.

**Literature search present but limited.** The unified search returns papers from three sources and deduplication works, but the paper claims ~36 literature rollouts reading ~1,500 papers per run. Our evaluation saw 30 papers retrieved in a single query. The gap between claim and implementation is large.

## The DeepSeek Question: Is It the Model or the Architecture?

This is the question that actually matters. I was running DeepSeek-chat — a capable but not frontier model — where the paper presumably used Claude. How much of what I saw is "DeepSeek isn't good enough" versus "the system is broken regardless"?

**Problems a better model would fix:**

- *Hypothesis specificity.* Claude Sonnet or Opus would almost certainly produce more specific, mechanistic hypotheses. Instead of "temperature increases enzyme activity" it might generate "temperature-dependent changes in the activation energy barrier for the rate-limiting acylation step of serine protease catalysis, quantifiable via Eyring plot analysis." That's the difference between a textbook and a research proposal.
- *Code generation quality.* A frontier model would likely generate correct, domain-appropriate experiment code — nonlinear regression for enzyme kinetics, Arrhenius plots, proper dose-response analysis. DeepSeek matched the wrong template; Claude might not need templates at all.
- *Analysis interpretation.* DeepSeek couldn't produce parseable structured output from the analysis prompt. Claude's instruction following is materially better for structured JSON responses.
- *JSON compliance.* The hypothesis refinement failure was a Pydantic validation error on the LLM's output. Better structured output compliance would fix this.

**Problems a better model would NOT fix:**

- *`embed_text` vs `embed_query`.* This is a bug in Python code. No model can fix a wrong method name.
- *JSON serialization of sklearn Pipelines.* This is a type system issue. The database layer can't store arbitrary Python objects.
- *The missing `priority_score` column.* Schema mismatch. Pure engineering.
- *Only 1 of 3 hypotheses tested.* This is loop control logic, not model quality.
- *Template-first code generation.* When a template matches, the system uses it and bypasses the LLM entirely. A better model can't improve code it never gets to write.
- *Silent failure patterns.* The novelty checker fails 45 times and reports success. The refiner crashes and reports 0 refinements as if that's normal. These are error-handling design decisions, not model limitations.
- *Convergence hitting iteration limit.* The system converges because it runs out of loops, not because science is done. That's a configuration and control-flow issue.

## Would a Better Model Make This Useful?

Honest verdict: **a better model is necessary but not sufficient.**

Claude Sonnet or Opus would likely produce: more specific and mechanistic hypotheses (3/10 might become 6-7/10), working domain-appropriate experiment code (the template fallback might become unnecessary), meaningful analysis that actually interprets results (instead of "manual review recommended"), and better JSON compliance that would let refinement actually work.

But the architectural issues remain. The novelty checker would still crash on `embed_text`. Hypothesis refinement would still need the `HypothesisLineage` validation fixed. Results might still fail to serialize to the database. The system would still converge at the iteration limit rather than at scientific saturation. The report generator still can't be imported.

My rough estimate: with Claude and no code fixes, output quality improves from 4.7/10 to maybe 6/10. With Claude AND the ~10 bug fixes needed, it could reach 7-8/10. The system needs both a better model and better engineering to be a useful research tool.

The scientific rigor infrastructure — the 7.88/10 scorecard — is genuinely impressive and doesn't depend on the model at all. Power analysis, effect size randomization, assumption checking, cost tracking, reproducibility management — these are baked into the code templates and evaluation framework. They'd work just as well with Claude as with DeepSeek. This is the part of the system that reflects real scientific thinking by its developers.

## Bottom Line

**As a research tool today: not ready for production use.** I spent more time fixing bugs than doing science. The system produced one ML classification on synthetic data for a question that called for nonlinear regression on real data. The analysis told me to review the findings manually — which is exactly what I would have done without the system.

**As a proof of concept: genuinely promising.** The research loop architecture is sound. The scientific rigor infrastructure is better than most research software I've used. The multi-agent design (hypothesis generator, experiment designer, code executor, data analyst, convergence detector) is the right decomposition of the scientific method. Someone clearly thought hard about what makes science rigorous, and encoded that thinking into the system.

**The gap is 80% engineering and 20% model quality.** The components exist. The statistical validators exist. The power analyzer exists. The novelty checker exists. They're just not wired together, and the ones that are wired together have bugs at the seams. This is a integration problem, not a capability problem.

**With a better model AND the bug fixes, this could be genuinely useful** — not as an autonomous scientist, but as a first-pass hypothesis explorer. Hand it a dataset and a question, get back 5-10 specific hypotheses grounded in literature, with properly designed experiments and preliminary statistical analysis. It wouldn't replace a researcher, but it could replace the first two hours of a literature review and hypothesis brainstorming session. That's a real value proposition, even if it's more modest than "autonomous scientific discovery."

**Paper claims vs. reality:**

| Metric | Paper Claim | What I Observed |
|--------|-------------|-----------------|
| Claims fully validated | 15/15 | 6/15 |
| Claims partially met | — | 8/15 |
| Blockers | 0 | 1 (no benchmark for 79.4% accuracy) |
| Hypotheses quality | Research-grade | Textbook-grade (3/10) |
| Bugs requiring fixes before first run | 0 | 3 |
| Scientific rigor infrastructure | Present | Present and impressive (7.88/10) |
| End-to-end autonomous operation | Yes | With caveats and manual intervention |

The paper describes the system Kosmos could be. The repository contains the system Kosmos currently is. The distance between them is meaningful but crossable — mostly with a wrench, not a breakthrough.
