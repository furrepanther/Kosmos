# Technical Diagnostic Report

<!--
CLEAN-ROOM PROTOCOL: This report must be written using ONLY data from the
current run (tier1/EVALUATION_REPORT.md, tier1/eval.log, tier1/artifacts/).
Do NOT reference scores, findings, or outcomes from any previous version.
Do NOT compare against prior runs anywhere except the "Comparison to Previous
Run" section at the bottom, which is populated SEPARATELY from regression
data after the rest of the report is complete.

Input files for the writing agent:
  - tier1/EVALUATION_REPORT.md  (required)
  - tier1/eval.log              (optional, for error details)
  - tier1/artifacts/            (optional, for generated code/plots)
  - persona YAML definition     (for persona context)
  - this template               (for structure)

Do NOT provide: prior version reports, comparison JSON, or prior narratives.
-->

**Persona**: {{persona_name}} ({{persona_role}})
**Run**: {{version}} — {{timestamp}}
**Model**: {{model}}

## Executive Summary

<!-- 2-3 sentences: overall system health, critical findings, recommended priority -->

## Automated Evaluation Results

- **Checks passed**: {{checks_passed}}/{{checks_total}}
- **Duration**: {{duration_seconds}}s
- **Scientific rigor score**: {{rigor_score}}/10

### Phase Results

| Phase | Status | Checks | Notes |
|-------|--------|--------|-------|
| 1. Pre-flight | | | |
| 2. Smoke Test | | | |
| 3. Multi-Iteration | | | |
| 4. Dataset Input | | | |
| 5. Output Quality | | | |
| 6. Scientific Rigor | | | |
| 7. Paper Compliance | | | |

## Dimension Scores

| Dimension | Score | Evidence |
|-----------|-------|----------|
| Hypothesis Quality | /10 | |
| Experiment Design | /10 | |
| Code Execution | /10 | |
| Analysis Interpretation | /10 | |
| Novelty Assessment | /10 | |
| Statistical Rigor | /10 | |

## Critical Findings

### Finding 1: [Title]

- **Severity**: BLOCKER / CRITICAL / HIGH / MEDIUM
- **Location**: `file:line`
- **Symptom**: What happens
- **Root Cause**: Why it happens
- **Fix**: Recommended change

### Finding 2: [Title]

<!-- Repeat as needed -->

## Dead Code Audit

| Module | Location | Purpose | Status |
|--------|----------|---------|--------|
| | | | Wired / Dead / Partial |

## Paper Claims Assessment

| # | Claim | Status | Gap |
|---|-------|--------|-----|
| 1 | | PASS / PARTIAL / FAIL | |

## Recommendations

### Blockers (must fix)

1.

### Critical (should fix next)

1.

### Improvements (nice to have)

1.

## Comparison to Previous Run

<!--
This section is populated AFTER the rest of the report is written, using
output from compare_runs.py (regression JSON). It is the ONLY section
that may reference prior run data. Fill in the table below from the
regression JSON; do not retroactively edit earlier sections to add
comparisons.
-->

<!-- If v002+: paste regression summary table here -->
