# Deep Crawl Enhancement Specifications

> Additional items that could be derived from an agentic deep crawl of the codebase.
> These complement the existing DEEP_ONBOARD.md with structural metadata.

---

## 1. Configuration & Environment

### 1.1 Complete Environment Variable List
**Derivation Method:** Scan all `os.getenv()`, `os.environ[]`, Pydantic `Field()` with `env=` parameter

**Output Format:**
```
| Variable | File:Line | Default | Required | Description |
|----------|-----------|---------|----------|-------------|
| ANTHROPIC_API_KEY | config.py:245 | None | Yes | LLM provider key |
| NEO4J_URI | config.py:549 | bolt://localhost:7687 | No | Graph database |
```

### 1.2 Required vs Optional Environment Variables
**Derivation Method:** Check for defaults, error handling on missing values, validation logic

**Output Format:**
```
Required (no default, raises on missing):
- ANTHROPIC_API_KEY (config.py:245)
- LLM_PROVIDER (config.py:230)

Optional (has default or graceful fallback):
- NEO4J_URI (default: bolt://localhost:7687)
- DEBUG_LEVEL (default: 0)
```

### 1.3 Version Constraints
**Derivation Method:** Parse pyproject.toml, requirements.txt, Dockerfiles, setup.py

**Output Format:**
```
| Dependency | Constraint | Source |
|------------|------------|--------|
| python | >=3.11 | pyproject.toml |
| pydantic | >=2.0,<3.0 | pyproject.toml |
| neo4j | 5.x | docker-compose.yml |
```

### 1.4 All Config Options with Defaults
**Derivation Method:** Extract Pydantic model fields from config classes

**Output Format:**
```
KosmosConfig:
  research.max_iterations: int = 20
  research.budget_usd: float = 10.0
  llm.temperature: float = 0.7
  llm.max_tokens: int = 4000
```

---

## 2. Code Quality Signals

### 2.1 Test Coverage Per Module
**Derivation Method:** Map test files to source files, count test functions and assertions

**Output Format:**
```
| Source Module | Test File | Test Count | Assertion Count |
|---------------|-----------|------------|-----------------|
| kosmos/agents/research_director.py | tests/unit/agents/test_research_director.py | 36 | 142 |
| kosmos/execution/executor.py | tests/unit/execution/test_executor.py | 28 | 89 |
| kosmos/core/memory.py | None | 0 | 0 |
```

### 2.2 Functions With No Tests
**Derivation Method:** Cross-reference public functions with test imports and calls

**Output Format:**
```
Untested Public Functions:
- kosmos/core/memory.py:MemoryStore.store_pattern (0 test references)
- kosmos/core/feedback.py:FeedbackLoop.learn_from_result (0 test references)
```

### 2.3 Type Hint Coverage
**Derivation Method:** AST parse for missing parameter and return annotations

**Output Format:**
```
| Module | Functions | Fully Typed | Partially Typed | Untyped |
|--------|-----------|-------------|-----------------|---------|
| kosmos/agents/base.py | 45 | 38 | 5 | 2 |
| kosmos/execution/executor.py | 32 | 30 | 2 | 0 |
```

### 2.4 TODO/FIXME/HACK Extraction
**Derivation Method:** Regex scan for inline markers with surrounding context

**Output Format:**
```
| Marker | File:Line | Context |
|--------|-----------|---------|
| TODO | research_director.py:1456 | "TODO: implement parallel execution" |
| FIXME | executor.py:892 | "FIXME: retry logic may infinite loop" |
| HACK | graph.py:445 | "HACK: workaround for py2neo bug" |
```

### 2.5 Deprecated Markers
**Derivation Method:** Find `@deprecated`, `# deprecated`, `warnings.warn("deprecated")`

**Output Format:**
```
Deprecated Code:
- kosmos/agents/research_director.py:1981 _send_to_convergence_detector() - "deprecated but not removed"
- kosmos/core/llm.py:389 generate_with_messages() - @deprecated decorator
```

---

## 3. Dependency Analysis

### 3.1 Import Graph
**Derivation Method:** Full module dependency tree via AST import extraction

**Output Format:**
```
kosmos/agents/research_director.py imports:
  - kosmos/core/llm.py (get_client)
  - kosmos/db/__init__.py (get_session, init_from_config)
  - kosmos/world_model/factory.py (get_world_model)
  - kosmos/agents/hypothesis_generator.py (HypothesisGeneratorAgent)
  ...

Dependency Depth:
  research_director.py -> llm.py -> providers/base.py -> config.py (depth: 4)
```

### 3.2 Circular Import Risks
**Derivation Method:** Detect cycles in import graph

**Output Format:**
```
Circular Import Cycles:
- config.py -> llm.py -> config.py (via get_config lazy import)

Near-Cycles (broken by lazy import):
- research_director.py -> hypothesis_generator.py -> research_director.py
  Broken at: hypothesis_generator.py:45 (import inside function)
```

### 3.3 Dead Code Detection
**Derivation Method:** Functions/classes never imported or called anywhere

**Output Format:**
```
Potentially Dead Code:
| Location | Type | Name | Last Modified |
|----------|------|------|---------------|
| core/memory.py:66 | class | MemoryStore | 2025-11-15 |
| core/feedback.py:76 | class | FeedbackLoop | 2025-11-15 |
| agents/registry.py:70 | method | _route_message | 2025-12-08 |
```

### 3.4 Hidden Consumers (Reverse Dependencies)
**Derivation Method:** "Who calls this?" for each public function

**Output Format:**
```
get_client() (llm.py:613) called by:
  - research_director.py:135
  - hypothesis_generator.py:78
  - experiment_designer.py:92
  - scientific_evaluation.py:176
  ... (45 total callers)

MemoryStore.store_pattern() (memory.py:72) called by:
  - (none)
```

---

## 4. Runtime Behavior

### 4.1 All External API Calls
**Derivation Method:** Find HTTP client usage (requests, httpx, aiohttp), extract endpoints

**Output Format:**
```
| Endpoint Pattern | File:Line | Method | Auth Required |
|------------------|-----------|--------|---------------|
| api.anthropic.com/v1/messages | providers/anthropic.py:309 | POST | Yes (API key) |
| api.semanticscholar.org/graph/v1/paper/search | literature/semantic_scholar.py:156 | GET | Optional |
| export.arxiv.org/api/query | literature/arxiv_client.py:89 | GET | No |
```

### 4.2 File I/O Locations
**Derivation Method:** All `open()`, `Path.write_*`, `Path.read_*`, `shutil` calls

**Output Format:**
```
File Writes:
| File:Line | Target Pattern | Mode |
|-----------|----------------|------|
| artifacts.py:234 | artifacts/cycle_{n}/*.json | w |
| scientific_evaluation.py:1432 | EVALUATION_REPORT.md | w |
| run_persona_eval.py:142 | meta.json | w |

File Reads:
| File:Line | Target Pattern |
|-----------|----------------|
| skill_loader.py:216 | kosmos-claude-scientific-skills/**/*.md |
| data_provider.py:310 | *.csv, *.parquet, *.json |
```

### 4.3 Subprocess Calls
**Derivation Method:** All `subprocess.run`, `subprocess.Popen`, `os.system`, `os.popen`

**Output Format:**
```
| File:Line | Command Pattern | Shell | Timeout |
|-----------|-----------------|-------|---------|
| graph.py:155 | docker-compose up -d neo4j | No | 60s |
| run_persona_eval.py:87 | git rev-parse HEAD | No | None |
| r_executor.py:145 | Rscript {script_path} | No | 300s |
```

### 4.4 Database Query Patterns
**Derivation Method:** SQLAlchemy query patterns, raw SQL strings

**Output Format:**
```
Query Patterns:
| File:Line | Type | Tables | Complexity |
|-----------|------|--------|------------|
| operations.py:156 | SELECT | Hypothesis | Simple (by ID) |
| operations.py:289 | SELECT | Experiment JOIN Hypothesis | Join |
| novelty_checker.py:273 | SELECT | Hypothesis | Filter (domain=) |

Raw SQL/Cypher:
| File:Line | Query |
|-----------|-------|
| graph.py:761 | f"MATCH path = (n)-[*1..{depth}]-(m)..." |
```

### 4.5 Async/Sync Boundary Violations
**Derivation Method:** `time.sleep()` in async functions, `run_until_complete()` in async context

**Output Format:**
```
Violations:
| File:Line | Issue | Context |
|-----------|-------|---------|
| research_director.py:674 | time.sleep() in async | _handle_error_with_recovery() |
| executor.py:335 | time.sleep() in retry loop | Called from async execute() |
| research_director.py:2171 | run_until_complete() | Sequential fallback in async |
```

---

## 5. Error Handling

### 5.1 Exception Taxonomy
**Derivation Method:** All custom exception classes, inheritance tree

**Output Format:**
```
Exception Hierarchy:
KosmosError (base)
├── ConfigurationError
├── ProviderError
│   ├── ProviderAPIError
│   ├── ProviderRateLimitError
│   └── ProviderAuthError
├── ExecutionError
│   ├── SandboxError
│   └── TimeoutError
└── BudgetExceededError

Defined at:
- KosmosError: kosmos/core/exceptions.py:10
- ProviderAPIError: kosmos/core/providers/base.py:45
```

### 5.2 Unhandled Exception Paths
**Derivation Method:** Raise statements without corresponding catch in call chain

**Output Format:**
```
Potentially Unhandled:
| Exception | Raised At | Nearest Catch | Gap |
|-----------|-----------|---------------|-----|
| BudgetExceededError | metrics.py:63 | None found | Propagates to CLI |
| RuntimeError("DB not init") | db/__init__.py:127 | research_director.py:131 | Caught |
```

### 5.3 Silent Failure Patterns
**Derivation Method:** `except: pass`, `except Exception: log`, bare except

**Output Format:**
```
Silent Failures:
| File:Line | Pattern | Risk |
|-----------|---------|------|
| hypothesis_generator.py:286 | except Exception: return "general" | Domain detection fails silently |
| literature_analyzer.py:114 | except: use_knowledge_graph = False | Neo4j failure hidden |
| research_director.py:435 | except Exception: logger.warning | Graph write failures ignored |
```

---

## 6. Security Surface

### 6.1 All exec/eval Calls
**Derivation Method:** Direct search for `exec(`, `eval(`, `compile(`

**Output Format:**
```
Code Execution Points:
| File:Line | Function | Sandboxed | Notes |
|-----------|----------|-----------|-------|
| executor.py:617 | exec(code, globals, locals) | Optional | Docker or restricted builtins |
| executor.py:476 | DockerSandbox.execute() | Yes | Full isolation |
```

### 6.2 SQL/Cypher Injection Risks
**Derivation Method:** f-string interpolation in query strings

**Output Format:**
```
Potential Injection Points:
| File:Line | Query Type | Interpolated Vars | Risk |
|-----------|------------|-------------------|------|
| graph.py:761 | Cypher | depth (int) | Low - typed |
| graph.py:917 | Cypher | max_hops (int) | Low - typed |
```

### 6.3 Hardcoded Secrets Patterns
**Derivation Method:** Regex for API key patterns, password strings in code

**Output Format:**
```
Potential Hardcoded Secrets:
| File:Line | Pattern | Context |
|-----------|---------|---------|
| .env:16 | sk-925e... | DEEPSEEK_API_KEY (CRITICAL - in git) |
| config.py:549 | "kosmos-password" | NEO4J_PASSWORD default |
| graph.py:155 | neo4j/kosmos-password | Docker health check |
```

---

## Implementation Notes

### Priority Order
1. **Environment variables** - Immediate value for onboarding
2. **Test coverage mapping** - Identifies risk areas
3. **Dead code detection** - Cleanup opportunities
4. **Async/sync violations** - Bug prevention
5. **Security surface** - Critical for code review

### Output Integration
These sections should be appended to DEEP_ONBOARD.md or generated as a companion file that references the same commit hash for consistency.

### Refresh Triggers
Regenerate when:
- Major refactoring commits
- New module additions
- Before major releases
- On request during code review
