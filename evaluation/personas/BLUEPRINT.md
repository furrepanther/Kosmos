# Persona-Based Scientific Evaluation Blueprint

## Purpose

This framework formalizes Kosmos scientific evaluation into a repeatable, versioned testing process. Researcher personas test the system, produce structured reports, and track improvement across fix-retest cycles. Every run is an immutable snapshot — nothing gets overwritten.

## Architecture

### Three-Tier Evaluation

| Tier | Name | Method | Output |
|------|------|--------|--------|
| **1** | Automated Evaluation | `scientific_evaluation.py` via `run_persona_eval.py` | JSON artifacts, eval report, log |
| **2** | Technical Diagnostic | Claude agent analyzes Tier 1 output + source code | `TECHNICAL_REPORT.md` |
| **3** | Narrative | Claude agent writes first-person account from persona's perspective | `NARRATIVE.md` |

### Directory Structure

```
evaluation/personas/
├── BLUEPRINT.md                  # This document
├── run_persona_eval.py           # Tier 1 orchestration script
├── compare_runs.py               # Regression comparison tool
├── templates/
│   ├── technical_report.md       # Tier 2 skeleton
│   └── narrative_report.md       # Tier 3 skeleton
├── definitions/                  # Persona YAML files
│   └── 001_enzyme_kinetics_biologist.yaml
└── runs/                         # Versioned, immutable test runs
    └── {persona_id}/
        ├── v{NNN}_{date}/
        │   ├── meta.json         # Run metadata
        │   ├── tier1/            # Automated outputs
        │   │   ├── EVALUATION_REPORT.md
        │   │   ├── artifacts/
        │   │   └── eval.log
        │   ├── tier2/            # Technical diagnostic
        │   │   └── TECHNICAL_REPORT.md
        │   └── tier3/            # Narrative
        │       └── NARRATIVE.md
        └── regression/           # Cross-version comparisons
            └── v{N}_vs_v{M}.json
```

## Persona Definitions

Each persona is a YAML file in `definitions/` with the following schema:

```yaml
persona:
  id: "NNN"                         # Zero-padded 3-digit ID
  name: "Dr. Name"                  # Character name
  role: "Job Title"                 # Professional role
  expertise_level: "mildly_technical"  # non_technical | mildly_technical | expert
  background: >                     # Free-text background

research:
  question: "Research question?"    # The scientific question to investigate
  domain: "biology"                 # Domain for code templates
  dataset: "data/file.csv"          # Path relative to evaluation/
  max_iterations: 3                 # Research cycle iterations
  budget_usd: 1.00                  # Budget cap
  expected_discoveries:             # What a good system should find
    - "Discovery 1"
    - "Discovery 2"

setup:
  model: "deepseek/deepseek-chat"   # LLM model identifier
  provider: "litellm"              # Provider backend
  database: "sqlite"               # Database backend
  neo4j: false                     # Whether Neo4j is required
  docker: false                    # Whether Docker is required

expectations:
  hypothesis_quality_minimum: 5    # Minimum quality score (1-10)
  hypotheses_tested_minimum: 2     # Minimum hypotheses actually tested
  code_should_match_domain: true   # Code should be domain-appropriate
  analysis_should_interpret: true  # Analysis should interpret results
  paper_claims_pass_minimum: 10    # Minimum paper claims passing (of 15)

narrative:
  voice: "first_person"            # Narration style
  tone: "honest, specific"        # Writing tone
  comparison_framing: "..."        # How to frame model comparisons
  sections:                        # Required narrative sections
    - "motivation_and_setup"
    - "getting_it_running"
    - "what_it_produced"
    - "what_worked"
    - "what_didnt"
    - "model_vs_architecture"
    - "verdict"
```

## Running Evaluations

### Tier 1: Automated (scripted)

```bash
# Run Tier 1, creating a new versioned directory automatically
python evaluation/personas/run_persona_eval.py \
  --persona 001_enzyme_kinetics_biologist \
  --tier 1

# Dry run (shows what would execute without running)
python evaluation/personas/run_persona_eval.py \
  --persona 001_enzyme_kinetics_biologist \
  --tier 1 \
  --dry-run
```

### Tier 2: Technical Diagnostic (agent-driven)

After Tier 1 completes, a Claude agent reads the Tier 1 artifacts, persona YAML, relevant source files, and the technical report template. It produces `tier2/TECHNICAL_REPORT.md` in the run directory.

### Tier 3: Narrative (agent-driven)

After Tier 2 completes, a Claude agent reads the persona YAML, all prior tier outputs, and the narrative template. It writes a first-person narrative from the persona's perspective as `tier3/NARRATIVE.md`.

### Agent Team Coordination

| Agent | Type | Depends On | Task |
|-------|------|------------|------|
| **Tier 1 Runner** | Bash | — | Execute `run_persona_eval.py --tier 1` |
| **Technical Analyst** | general-purpose | Tier 1 | Write `TECHNICAL_REPORT.md` |
| **Narrative Writer** | general-purpose | Tier 2 | Write `NARRATIVE.md` |
| **Regression Comparator** | Bash | Tier 1 | Run `compare_runs.py` (if prior version exists) |

## Regression Tracking

Compare any two runs of the same persona:

```bash
python evaluation/personas/compare_runs.py \
  --persona 001_enzyme_kinetics_biologist \
  --v1 v001_20260207 \
  --v2 v002_20260210
```

Output is a JSON file saved to `regression/v001_vs_v002.json` with:
- Check pass/fail deltas
- Quality score deltas
- Paper claims pass deltas
- Lists of improved, regressed, and unchanged checks

## Versioning Rules

1. **Immutable runs**: Once created, a versioned run directory is never modified
2. **Auto-increment**: `run_persona_eval.py` automatically assigns the next version number
3. **Date suffix**: Version directories include the run date (`v001_20260207`)
4. **meta.json**: Every run records timestamp, model, config hash, and Kosmos git SHA

## Creating New Personas

1. Create a YAML file in `definitions/` following the schema above
2. Use the next available ID (e.g., `002_materials_scientist.yaml`)
3. Ensure the dataset exists in `evaluation/data/` if specified
4. Run Tier 1 to validate the persona works

## meta.json Schema

```json
{
  "persona_id": "001",
  "persona_name": "001_enzyme_kinetics_biologist",
  "version": "v001",
  "timestamp": "2026-02-07T17:39:38",
  "model": "deepseek/deepseek-chat",
  "provider": "litellm",
  "kosmos_git_sha": "f9ecf1d...",
  "config_hash": "sha256:...",
  "tier1_completed": true,
  "tier2_completed": true,
  "tier3_completed": true,
  "checks_passed": 36,
  "checks_total": 37,
  "duration_seconds": 749.3
}
```
