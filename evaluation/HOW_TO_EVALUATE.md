# How to Evaluate Kosmos

Previous evaluation reports have been archived into the persona framework at `evaluation/personas/runs/`. This document explains how to run a fresh evaluation against the current state of the codebase.

## Quick Start: Automated Evaluation Only (Tier 1)

Run the automated 7-phase scientific evaluation:

```bash
python evaluation/scientific_evaluation.py
```

This takes ~12 minutes and produces:
- `evaluation/SCIENTIFIC_EVALUATION_REPORT.md` — checks passed, quality scores, rigor scorecard, paper compliance
- `evaluation/logs/evaluation_YYYYMMDD_HHMMSS.log` — detailed execution log

## Full Persona Evaluation (Tiers 1-3)

The persona framework runs a structured evaluation from the perspective of a researcher persona, producing three tiers of output in a versioned, immutable directory.

### Step 1: Run Tier 1 (Automated)

```bash
python evaluation/personas/run_persona_eval.py \
  --persona 001_enzyme_kinetics_biologist \
  --tier 1
```

This creates a versioned run directory (e.g., `personas/runs/001_.../v002_20260208/`) with automated evaluation artifacts.

Use `--dry-run` to preview the command without executing.

### Step 2: Run Tier 2 (Technical Diagnostic)

Ask Claude Code to analyze the Tier 1 output and write a technical diagnostic:

> Analyze the Tier 1 evaluation output in `evaluation/personas/runs/001_enzyme_kinetics_biologist/v00N_YYYYMMDD/tier1/` along with the relevant Kosmos source code. Write a technical diagnostic report to `tier2/TECHNICAL_REPORT.md` in that same run directory, following the template in `evaluation/personas/templates/technical_report.md`. Identify root causes, file locations, and fix recommendations.

### Step 3: Run Tier 3 (Narrative)

Ask Claude Code to write a first-person narrative from the persona's perspective:

> Read the persona definition in `evaluation/personas/definitions/001_enzyme_kinetics_biologist.yaml`, the Tier 1 and Tier 2 outputs, and write a first-person narrative from the persona's perspective to `tier3/NARRATIVE.md`. Follow the template in `evaluation/personas/templates/narrative_report.md`. Use the previous narrative at `personas/runs/001_.../v001_20260207/tier3/NARRATIVE.md` as a quality reference.

### Step 4: Compare Runs (Regression)

```bash
python evaluation/personas/compare_runs.py \
  --persona 001_enzyme_kinetics_biologist \
  --v1 v001_20260207 \
  --v2 v00N_YYYYMMDD
```

Outputs a JSON diff showing which checks improved, regressed, or stayed the same.

## What the Evaluation Measures

| Phase | What It Tests |
|-------|---------------|
| 1. Pre-flight | Config, LLM connectivity, DB, type compatibility |
| 2. Smoke Test | Single-iteration end-to-end research cycle |
| 3. Multi-Iteration | 3 full iterations, convergence behavior |
| 4. Dataset Input | CSV loading via `--data-path` |
| 5. Output Quality | Hypothesis quality, experiment design, code execution |
| 6. Scientific Rigor | Novelty, power analysis, assumptions, reproducibility |
| 7. Paper Compliance | 15 claims from arXiv:2511.02824v2 |

## Previous Results

The v001 baseline evaluation (2026-02-07, post-fix) scored:
- **36/37 checks passed** (97%)
- **4.67/10 output quality**
- **7.88/10 scientific rigor**
- **6/15 paper claims PASS, 8 PARTIAL, 1 BLOCKER**

Archived at: `evaluation/personas/runs/001_enzyme_kinetics_biologist/v001_20260207/`

Note: v001 has Tier 1 (automated) and Tier 3 (narrative) but no Tier 2 (technical diagnostic). An earlier technical report existed but was written against a pre-fix codebase and excluded to avoid stale data. Run Tier 2 against the current Tier 1 output to fill this gap.

## Reference

- Framework details: `evaluation/personas/BLUEPRINT.md`
- Persona definition schema: `evaluation/personas/definitions/001_enzyme_kinetics_biologist.yaml`
- Report templates: `evaluation/personas/templates/`
