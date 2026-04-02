# DEEP_ONBOARD.md Value Analysis

> Assessment of which sections provide the most value for an AI coder working on this codebase.

---

## Ranking by Value

### 1. Gotchas Section (Most Valuable)

**Why:** The 139 gotchas with severity rankings and file:line references are immediately actionable. Before touching any code, I can check "are there gotchas here?"

**High-Impact Examples:**
| Gotcha | Why It Matters |
|--------|----------------|
| #5 (sandbox return value loss) | Would cause silent data loss if modifying executor |
| #15 (convergence passes empty results) | Explains why code works despite looking broken |
| #19 (LLM enhancement is no-op) | Prevents wasted time investigating dead code |
| #1 (reset_eval_state drops all tables) | Critical to know before running evaluation |
| #6-8 (exec security) | Must understand before touching execution code |

**Usage Pattern:** Search gotchas by file path before modifying any module.

---

### 2. Shared State Index (Very Valuable)

**Why:** The 16 singletons with thread-safety analysis tells me exactly what's safe to touch and what has hidden coupling.

**Key Insights:**
| Singleton | Critical Knowledge |
|-----------|-------------------|
| `_world_model` | NOT thread-safe - must be careful with concurrent access |
| `_default_client` | Uses double-checked locking - safe |
| `_config` | CLI mutates global state - hidden side effect |
| `MemoryStore` | Dead infrastructure - don't try to use it |
| `_knowledge_graph` | Auto-starts Docker, 120s blocking - explains slow startup |

**Usage Pattern:** Check shared state index when debugging unexpected behavior or adding new singletons.

---

### 3. Critical Path 1: CLI to Terminal Side Effects (Very Valuable)

**Why:** Complete function trace from `kosmos run` to every side effect. Essential for understanding the main execution flow.

**What It Provides:**
- Every function hop with file:line references
- Branching points clearly marked
- State machine transitions documented
- Side effects explicitly listed

**Terminal Side Effects Table:**
```
| Side Effect | Location | Frequency |
|-------------|----------|-----------|
| LLM API call | research_director.py:2372 | 1x at start |
| DB commit | hypothesis_generator.py:491 | N per iteration |
| exec() | executor.py:617 | 1 per experiment |
| Neo4j write | research_director.py:250,1433,... | Many per iteration |
```

**Usage Pattern:** Trace through when debugging "why did X happen?" or understanding impact of changes.

---

### 4. Terminal Side Effects Tables (Valuable)

**Why:** Each critical path ends with a table of every side effect. This is essentially a blast radius map.

**Value:** Before making changes, I can see:
- What external systems are affected (DB, Neo4j, files, APIs)
- How often each side effect occurs
- Exact file:line where it happens

**Usage Pattern:** Consult before modifying any function in a critical path to understand downstream impact.

---

### 5. Error Handling Patterns (Valuable)

**Why:** Documents how errors propagate and where they're swallowed.

**Key Patterns Documented:**
- Catch-log-degrade (silent fallback)
- Retry with backoff locations
- Circuit breaker behavior
- Which exceptions propagate vs get caught

**Usage Pattern:** Check before adding new error handling to maintain consistency.

---

### 6. Data Transformations Between Hops (Moderate Value)

**Why:** Useful but often inferable from reading code directly.

**When It Helps:**
- Understanding serialization boundaries
- Knowing where type changes occur (Pydantic -> dict -> DB)
- Identifying lossy transformations

**Usage Pattern:** Reference when debugging data corruption or serialization issues.

---

### 7. Sub-Paths (Persona Eval, Run Comparison) (Lower Value)

**Why:** Specialized workflows that may never be touched. Still useful if working in those areas.

**When Valuable:**
- Setting up evaluation pipelines
- Debugging CI/CD failures
- Understanding test infrastructure

**Usage Pattern:** Reference only when specifically working on evaluation or comparison tooling.

---

## Summary Matrix

| Section | Immediate Value | Reference Value | Update Frequency Needed |
|---------|-----------------|-----------------|------------------------|
| Gotchas | High | High | On every major change |
| Shared State Index | High | High | When singletons change |
| Critical Path 1 | Medium | High | When main loop changes |
| Side Effects Tables | Medium | High | When I/O patterns change |
| Error Handling | Medium | Medium | When error strategy changes |
| Data Transformations | Low | Medium | Rarely |
| Sub-Paths | Low | Low | When eval tooling changes |

---

## Recommended Reading Order for New AI Coder

1. **First:** Shared State Index - understand the global architecture
2. **Second:** Critical Path 1 - understand the main execution flow
3. **Third:** Gotchas (Critical + High severity only) - know the landmines
4. **As Needed:** Relevant gotchas for specific files being modified
5. **As Needed:** Sub-paths when working on those specific areas

---

## What Makes This Document Effective

1. **[FACT] tags** - Distinguishes verified claims from inference
2. **file:line references** - Enables direct navigation
3. **Severity rankings** - Enables prioritization
4. **Tables over prose** - Scannable, parseable
5. **Commit hash timestamp** - Enables staleness detection
