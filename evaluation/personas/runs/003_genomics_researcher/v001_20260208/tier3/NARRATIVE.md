# Evaluating Kosmos as a Genomics Research Assistant

**Author**: Dr. Kenji Tanaka, Computational Genomics Researcher
**Date**: 2026-02-08
**System under test**: Kosmos AI Scientist v0.2.0
**Model**: deepseek/deepseek-chat via LiteLLM
**Dataset**: Gene expression profiles from drug-treated vs. control HeLa cell lines (132 rows, 11 genes, 4 dose levels, triplicates)

---

## 1. Motivation and Setup

I spend most of my working hours staring at differential expression tables. My lab generates RNA-seq data from cancer cell lines treated with candidate therapeutics, and my job is to figure out which genes respond, whether the response is dose-dependent, and what pathways those genes implicate. It is not glamorous work, but it is the kind of systematic, multi-comparison analysis where I thought an AI research system could genuinely help.

I came across Kosmos through its arXiv preprint (2511.02824v2), which claims the system can take a research objective and a CSV dataset, then autonomously generate hypotheses, design experiments, execute statistical code, and iterate toward validated discoveries. The paper mentions 166 data analysis rollouts per run and 42,000 lines of executed code. For someone who runs DESeq2 pipelines and volcano plots all day, those numbers sounded ambitious but plausible if the system had good domain awareness.

My research question was straightforward: "Which genes are differentially expressed between drug-treated and control cancer cell lines, and what biological pathways do they implicate?" I prepared a dataset with 132 rows covering 11 genes: three apoptosis markers I expected to be upregulated (CDKN1A, BAX, CASP3), three proliferation markers I expected to be downregulated (CCND1, MYC, CDK4), two housekeeping genes that should be unchanged (GAPDH, ACTB), and three genes with moderate or mixed effects (TP53, BCL2, VEGFA). Each gene had expression values at 0, 1, 5, and 10 micromolar drug doses, in triplicate. I included pre-computed log2 fold change and p-value columns so the system had everything it needed.

What I wanted from Kosmos was what I would want from a competent graduate student: load the data, run per-gene t-tests comparing treated versus control at each dose, compute log2 fold changes, apply FDR correction across the gene panel, produce a volcano plot, and identify which functional pathways are enriched among the significant hits. That is a four-hour task for a human. I gave Kosmos fifteen minutes.

## 2. Getting It Running

Installation was smooth. The repository cloned cleanly, dependencies resolved without conflicts, and `kosmos doctor` reported all 13 checks passing. The SQLite database initialized on first run with Alembic migrations. Unit tests passed at 97.8% (45/46), with the single failure being an Anthropic API authentication test that is irrelevant when using LiteLLM.

I did hit one configuration issue early. I had set `LITELLM_MODEL=deepseek/deepseek-chat` in my `.env` file, but the config system did not pick it up. The Phase 1 smoke test revealed that despite my environment variable, the system defaulted to `gpt-3.5-turbo-0125`. The pydantic alias resolution for the nested model configuration does not propagate the `LITELLM_MODEL` variable correctly. This was resolved by setting the model directly in the YAML config, but it is the kind of silent misconfiguration that could produce confusing results if you did not check.

Neo4j was configured but unavailable, so the knowledge graph fell back to an InMemoryWorldModel. This is fine for an evaluation, but it means any claims about persistent knowledge accumulation across runs are untestable.

## 3. What It Produced

### Hypotheses

The system generated hypotheses in two phases. In Phase 2 (single-iteration smoke test), it produced 5 hypotheses and tested 1, converging after a single iteration. In Phase 3 (multi-iteration loop), it generated 9 hypotheses, tested 1, and ran 8 actions across 3 iterations before converging.

Here is the problem: the hypotheses were not about my data. Despite being given a genomics research question about differential gene expression in cancer cell lines, the system generated hypotheses about enzyme kinetics and temperature effects:

> "Increasing temperature from 20C to 40C will cause a proportional increase in the reaction rate of the enzyme catalase, as measured by the volume of oxygen gas produced from hydrogen peroxide decomposition."

> "For the enzyme amylase, a 10C increase in temperature within the range of 25C to 55C will cause a decrease in the Michaelis constant (Km) by at least 20%, indicating increased substrate binding affinity."

> "Exposure of the enzyme lactate dehydrogenase (LDH) to a sustained temperature of 45C for 30 minutes will cause an irreversible reduction in its specific activity by over 50%."

These are testable, specific, mechanistic hypotheses -- they scored 0.85-0.95 on testability. But they have nothing to do with RNA-seq, differential expression, CDKN1A, HeLa cells, or anything in my dataset. The system was running in the "biology" domain (genomics is not among the enabled domains: biology, physics, chemistry, neuroscience), and the LLM defaulted to textbook biochemistry rather than engaging with the actual research question or the provided data.

### Experiment Design

The experiment designer produced a single protocol labeled "unnamed" with zero steps, no variables, no controls, and no statistical tests specified. The experiment type was classified as "unknown." The PowerAnalyzer module exists in the codebase (525 lines) but was never called by the designer. The ExperimentValidator module (approximately 500 lines) was also never imported. Instead, an inline `_validate_protocol()` function of 37 lines was used, which generates warnings but does not block execution.

### Code Generation and Execution

The code generator produced a T-Test Comparison Analysis script from a protocol template. The code was 2,078 characters and included a data-loading block that checks for a `data_path` variable:

```python
if 'data_path' in dir() and data_path and Path(data_path).exists():
    df = pd.read_csv(data_path)
    _data_source = 'file'
else:
    # Generate synthetic data...
```

The `data_path` variable was never passed into the execution scope, so the system fell back to synthetic data generation with a hardcoded effect size of 0.5. Then the code itself failed with a `NameError: name 'df' is not defined` at line 50, inside a dictionary comprehension that references `df` outside its defined scope. The template has a scoping bug.

The stdout from the failed execution was an unformatted f-string:

```
T-statistic: {result['t_statistic']:.4f}
P-value: {result['p_value']:.6f}
Significance: {result['significance_label']}
Mean difference: {result['mean_difference']:.4f}
```

This is raw template text, not computed values. The code never reached the print statements because the NameError halted execution earlier.

### Data Analysis Interpretation

Despite the code execution failure, the system produced an interpretation. The LLM-based data analyst declared the hypothesis supported with 0.85 confidence and reported:

- "Statistically significant difference in enzyme activity between temperature conditions (p = 0.003)"
- "Large effect size (Cohen's d = 0.8) indicating substantial biological relevance"
- "Adequate sample size (n=100) providing reasonable statistical power"

These findings are fabricated. The code did not execute successfully, no p-value was computed, and the sample size of 100 does not correspond to any real or generated data. The interpretation module accepted the LLM's output without validating it against actual execution results. The `supports_hypothesis` flag was set by LLM judgment rather than formal statistical criteria, and no check was made for whether the data source was synthetic.

### Literature Search

The literature search module found 30 papers via Semantic Scholar and arXiv, but they were about enzyme kinetics -- matching the off-topic hypotheses rather than the genomics research question. Representative titles:

- "Nonlinear temperature sensitivity of enzyme kinetics explains canceling effect"
- "Temperature sensitivity of soil enzyme kinetics under N-fertilization in two temperate forests"
- "Deterministic and Stochastic Models in Enzyme Kinetics"

Not a single paper about differential gene expression, RNA-seq, cancer cell lines, or drug response. The literature search was technically functional but scientifically irrelevant.

### Dataset Loading

Phase 4 confirmed that the DataProvider could load my CSV correctly: 132 rows, 7 columns (gene_name, condition, expression_level, dose_um, replicate, log2_fold_change, p_value). The system recognized the file format and validated the data shape. But this loading capability was never connected to the analysis pipeline. The data sat inert while the system generated enzyme kinetics hypotheses and synthetic data.

## 4. What Worked

I want to be fair. Several things functioned correctly at the infrastructure level.

**Data ingestion is solid.** The DataProvider loaded my 132-row gene expression CSV without issue, correctly identified all 7 columns, and supports 5 file formats (CSV, TSV, Parquet, JSON, JSONL). For a system that needs to accept arbitrary scientific datasets, this is a reasonable foundation.

**The scientific rigor modules exist and are well-designed.** I examined the codebase and found genuine implementations of:
- Multiple testing correction (Bonferroni, Benjamini-Hochberg, Holm-Bonferroni) in `statistics.py`
- Power analysis with support for t-tests, ANOVA, correlation, regression, and chi-square in `statistical_power.py` (525 lines)
- Assumption checking (`check_assumptions()`) with tests for normality, homoscedasticity, and independence
- An ExperimentValidator with approximately 500 lines of protocol validation logic
- A NoveltyChecker (250+ lines) with semantic similarity and literature search

The problem is that none of these modules are called during execution. They are dead code in the runtime path. The rigor score of 7.88/10 reflects the quality of the code that exists, not the quality of what actually runs.

**Convergence detection works.** The system correctly stopped after hitting iteration limits and detected when no testable hypotheses remained. The novelty trend tracking (0.8, 0.6, 0.4, 0.2, 0.1, 0.1) shows a reasonable declining novelty curve. The convergence logic is sound even if what it converges on is not.

**The workflow state machine reaches all phases.** Across the 3-iteration run, the system visited: generate_hypothesis, design_experiment, execute_experiment, analyze_result, refine_hypothesis, and converge. The research loop architecture is complete in terms of phase coverage.

## 5. What Did Not Work

### The system ignored my data entirely

This is the most fundamental failure. I provided a well-structured gene expression dataset with clear column names, biologically meaningful gene selections, and dose-response structure. The system loaded it, confirmed the shape, and then proceeded to generate hypotheses about enzyme kinetics using synthetic data. There is no mechanism in the agent pipeline to pass the `data_path` variable into the code execution scope. The templates check for it, but it is never provided. The paper's core value proposition -- "give it an objective and a dataset" -- is broken at the integration layer.

### Wrong statistical approach for the data structure

Even setting aside the domain mismatch, the system applied a simple two-group t-test comparison. My dataset has a multi-factor structure: 11 genes crossed with 4 dose levels, with triplicates at each combination. The appropriate analysis pipeline would be:

1. Per-gene t-tests (or Wilcoxon) comparing each dose level to control
2. Log2 fold change computation (which I pre-computed, but the system should verify)
3. Volcano plot: -log10(p-value) vs. log2(fold change) for all genes at each dose
4. FDR correction across the full gene panel (Benjamini-Hochberg on 11 x 3 = 33 comparisons)
5. Dose-response curve fitting (linear or sigmoidal) per gene
6. Pathway enrichment analysis on the significant gene set (GO, KEGG, Reactome)

The system has Bonferroni and Benjamini-Hochberg implementations in `statistics.py`, but they are never applied across the research loop. The `check_assumptions()` function exists but is never called. The code template selected was `TTestComparisonCodeTemplate`, which is a single two-group comparison -- not a multi-gene, multi-dose analysis.

### Fabricated interpretation from failed execution

The code execution failed with a NameError. The analysis module then produced an interpretation with specific statistics (p = 0.003, Cohen's d = 0.8, n = 100) that were not computed from any actual analysis. The LLM hallucinated plausible-sounding results. In a real research context, this is dangerous -- it produces confident-looking findings from nonexistent data. There is no guard that checks whether code execution succeeded before accepting the LLM's interpretation.

### Hypothesis-data disconnect

The hypotheses about catalase, amylase, and lactate dehydrogenase have no connection to CDKN1A, BAX, CASP3, or any gene in my dataset. The system did not examine the column names, gene identifiers, or structure of the input data before generating hypotheses. A genomics-aware system should have noticed columns named `gene_name`, `condition`, `log2_fold_change`, and `p_value` and generated hypotheses about differential expression patterns.

### No domain template for genomics

The code generator logged: "No template found for computational, falling back to LLM." The enabled domains are biology, physics, chemistry, and neuroscience. Genomics is not recognized as a domain, and there is no code template for differential expression analysis. The system needs domain-specific code templates that know how to handle gene expression matrices, or at minimum, a data-aware template selector that examines the input CSV structure.

### ClaudeClient failure with silent fallback

The log shows "ClaudeClient failed, trying LiteLLM fallback." This is an error-handling path that works, but it means the primary LLM client is misconfigured. Combined with the LITELLM_MODEL environment variable not being picked up, there are multiple layers of silent fallback that make it unclear which model is actually answering queries at any given point.

## 6. Model vs. Architecture

Separating model limitations from pipeline bugs is critical here because the fixes are different.

### Architecture bugs (fixable without changing the model)

- **data_path not passed to execution scope**: The template checks for `data_path`, but the agent pipeline never provides it. This is a plumbing bug. Fix: pass `data_path` from the Director to the CodeExecutor's exec globals.
- **NameError in TTestComparisonCodeTemplate**: The variable `df` goes out of scope before the dictionary comprehension at line 50. This is a template bug. Fix: restructure the code template to maintain variable scope.
- **Dead rigor modules**: PowerAnalyzer, ExperimentValidator, NoveltyChecker, and `check_assumptions()` are implemented but never called from the agent pipeline. Fix: wire them into the ExperimentDesigner and DataAnalyst agents.
- **No genomics domain template**: The code generator has no template for differential expression analysis. Fix: add a template that handles gene-by-condition expression matrices.
- **LITELLM_MODEL env var not loaded**: The pydantic alias resolution does not propagate nested model fields. Fix: explicit env var handling in config.py.
- **Interpretation without execution validation**: The DataAnalyst accepts LLM interpretations even when code execution fails. Fix: gate interpretation on successful execution.

### Model limitations (would improve with a better LLM)

- **Hypothesis relevance**: A more capable model might recognize the genomics context from the research question and generate hypotheses about gene expression rather than enzyme kinetics. But this is partly an architecture issue too -- the model was not shown the dataset columns before hypothesis generation.
- **Domain awareness**: The model defaulted to generic biochemistry. A model with stronger genomics training might have recognized the gene names (CDKN1A is p21, a canonical cell cycle inhibitor; BAX and CASP3 are well-known apoptosis effectors) and reasoned about expected expression patterns.
- **Interpretation hallucination**: A model with better calibration would decline to provide specific statistics when the underlying code failed. But the architecture also failed to provide the model with the execution status.

The honest assessment is that the architecture problems are more damaging than the model limitations. Even a perfect LLM would fail here because the pipeline never feeds the user's data into the analysis code. The hypothesis-data disconnect is not the model guessing wrong -- it is the model never being shown the data.

## 7. Verdict

### Quantitative Summary

| Metric | Value |
|--------|-------|
| Total checks passed | 37/37 (100%) |
| Total duration | 901.7s (~15 min) |
| Hypotheses generated (Phase 2 / Phase 3) | 5 / 9 |
| Experiments completed | 1 |
| Code execution success | Failed (NameError) |
| Average quality score | 5.29/10 |
| Scientific rigor score | 7.88/10 |
| Paper claims: PASS / PARTIAL / BLOCKER | 6 / 8 / 1 |
| Dataset loaded correctly | Yes (132 rows, 7 cols) |
| Dataset used in analysis | No |
| Hypotheses relevant to research question | No |
| FDR correction applied | No |
| Volcano plot generated | No |
| Pathway enrichment performed | No |

### Assessment

Kosmos passes its own test harness at 100% because the checks verify that the pipeline reaches each phase, not that it produces correct science. From the perspective of someone who needs differential expression analysis, the system produced no usable output. It loaded my data and then ignored it. It generated hypotheses about the wrong biological domain. It ran code that crashed. It interpreted results that did not exist. It searched literature for topics unrelated to my research question.

The gap between what the architecture contains and what it actually executes is striking. The codebase has Benjamini-Hochberg correction, power analysis, assumption checking, and experiment validation -- exactly the tools I need. But they are disconnected from the runtime path. It is like finding a well-equipped laboratory where none of the instruments are plugged in.

### Would I use it again?

Not in its current state for genomics work. My DESeq2 pipeline in R, which I wrote three years ago, would produce a complete differential expression analysis with volcano plots, MA plots, FDR-corrected gene lists, and GO enrichment in under ten minutes. Kosmos took fifteen minutes to produce enzyme kinetics hypotheses about fabricated data.

However, I can see the potential. If the data_path plumbing were fixed, the domain templates expanded, and the rigor modules wired into the pipeline, this system could be a genuinely useful research assistant for exploratory analysis. The architecture is sound. The scientific modules are thoughtfully designed. The convergence logic works. What is missing is the integration -- connecting the dataset to the hypotheses, the hypotheses to the code, and the code results to the interpretation.

What would a better model change? It might generate more relevant hypotheses and avoid hallucinating statistics, but it would not fix the fundamental plumbing problems. The architecture needs engineering work before the model quality becomes the binding constraint. Right now, the system is bottlenecked by integration bugs, not by inference capability.

---

*Evaluation conducted on Kosmos v0.2.0, commit 099764d, using deepseek/deepseek-chat via LiteLLM. Gene expression dataset: 132 rows, 11 genes (CDKN1A, BAX, CASP3, CCND1, MYC, CDK4, GAPDH, ACTB, TP53, BCL2, VEGFA), drug-treated vs. control HeLa cell lines at 0/1/5/10 micromolar doses, triplicates.*
