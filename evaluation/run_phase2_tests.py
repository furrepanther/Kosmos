"""Phase 2: Component Testing Script
Tests each KOSMOS agent/component independently and captures results.
"""
import json
import time
import traceback
import sys
import os
from pathlib import Path
from datetime import datetime

os.chdir("/mnt/c/python/Kosmos")
from dotenv import load_dotenv
load_dotenv(override=True)

results = {}

def test_component(name, func):
    """Run a component test and capture results."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        result["status"] = "PASS"
        result["duration_seconds"] = round(elapsed, 2)
        print(f"  PASS ({elapsed:.1f}s)")
    except Exception as e:
        elapsed = time.time() - start
        result = {
            "status": "FAIL",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "duration_seconds": round(elapsed, 2)
        }
        print(f"  FAIL ({elapsed:.1f}s): {e}")
    results[name] = result
    return result


# ============================================================
# Test 2.1: Hypothesis Generation
# ============================================================
def test_hypothesis_generation():
    from kosmos.agents.hypothesis_generator import HypothesisGeneratorAgent

    agent = HypothesisGeneratorAgent(config={
        "use_literature_context": False,
        "num_hypotheses": 3
    })

    response = agent.generate_hypotheses(
        research_question="How does temperature affect enzyme activity?",
        domain="biology",
        num_hypotheses=3,
        store_in_db=False
    )

    # Response is a HypothesisGenerationResponse
    hypotheses = getattr(response, 'hypotheses', response) if not isinstance(response, list) else response
    if not isinstance(hypotheses, list):
        hypotheses = [hypotheses]

    result = {
        "count": len(hypotheses),
        "response_type": type(response).__name__,
        "hypotheses": []
    }

    for h in hypotheses:
        h_data = {
            "statement": getattr(h, 'statement', str(h))[:200],
            "has_rationale": bool(getattr(h, 'rationale', None)),
            "has_domain": bool(getattr(h, 'domain', None)),
            "novelty_score": getattr(h, 'novelty_score', None),
            "testability_score": getattr(h, 'testability_score', None),
            "confidence_score": getattr(h, 'confidence_score', None),
        }
        result["hypotheses"].append(h_data)
        print(f"  H: {h_data['statement'][:100]}...")
        print(f"    novelty={h_data['novelty_score']}, testability={h_data['testability_score']}")

    result["novelty_checker_integrated"] = False
    result["novelty_checker_note"] = "NoveltyChecker exists but never called from HypothesisGeneratorAgent"
    result["require_novelty_check_config"] = agent.require_novelty_check
    result["min_novelty_score_config"] = agent.min_novelty_score

    return result


# ============================================================
# Test 2.2: Literature Search
# ============================================================
def test_literature_search():
    from kosmos.literature.unified_search import UnifiedLiteratureSearch

    searcher = UnifiedLiteratureSearch()
    papers = searcher.search("enzyme kinetics temperature", max_results=5)

    result = {
        "count": len(papers),
        "papers": []
    }

    for p in papers[:5]:
        p_data = {
            "title": getattr(p, 'title', str(p))[:150],
            "source": str(getattr(p, 'source', 'unknown')),
            "year": getattr(p, 'year', None),
            "has_abstract": bool(getattr(p, 'abstract', None)),
        }
        result["papers"].append(p_data)
        print(f"  Paper: {p_data['title'][:80]}... ({p_data['source']})")

    return result


# ============================================================
# Test 2.3: Experiment Design
# ============================================================
def test_experiment_design():
    from kosmos.agents.experiment_designer import ExperimentDesignerAgent
    from kosmos.models.hypothesis import Hypothesis
    from kosmos.models.experiment import ExperimentType

    agent = ExperimentDesignerAgent(config={
        "use_templates": True,
        "use_llm_enhancement": True,
    })

    hypothesis = Hypothesis(
        research_question="How does temperature affect enzyme activity?",
        statement="Higher temperature increases enzyme activity up to an optimal point of 37C, after which activity decreases due to denaturation",
        rationale="Enzyme kinetics theory predicts a bell-shaped curve for temperature-activity relationship",
        domain="biology",
        novelty_score=0.7,
        testability_score=0.8,
        confidence_score=0.6
    )

    protocol = agent.design_experiment(
        hypothesis=hypothesis,
        hypothesis_id="test-hyp-001",
        preferred_experiment_type=ExperimentType.COMPUTATIONAL,
        store_in_db=False
    )

    protocols = [protocol] if not isinstance(protocol, list) else protocol

    result = {
        "count": len(protocols),
        "protocols": []
    }

    for p in protocols:
        p_data = {
            "name": getattr(p, 'name', 'unnamed')[:100],
            "has_steps": bool(getattr(p, 'steps', None)),
            "step_count": len(getattr(p, 'steps', [])),
            "has_variables": bool(getattr(p, 'variables', None)),
            "has_controls": bool(getattr(p, 'control_groups', None)),
            "has_statistical_tests": bool(getattr(p, 'statistical_tests', None)),
            "experiment_type": str(getattr(p, 'experiment_type', 'unknown')),
        }
        result["protocols"].append(p_data)
        print(f"  Protocol: {p_data['name']}")
        print(f"    Steps: {p_data['step_count']}, Controls: {p_data['has_controls']}, Stats: {p_data['has_statistical_tests']}")

    result["power_analyzer_integrated"] = False
    result["experiment_validator_integrated"] = False
    result["gap_notes"] = [
        "PowerAnalyzer exists but never called by designer",
        "ExperimentValidator exists but never imported by designer",
        "Inline _validate_protocol() used instead (~37 lines vs ~500 line validator)"
    ]

    return result


# ============================================================
# Test 2.4: Code Generation & Execution
# ============================================================
def test_code_execution():
    from kosmos.execution.code_generator import TTestComparisonCodeTemplate
    from kosmos.execution.executor import CodeExecutor
    from kosmos.models.experiment import (
        ExperimentProtocol, ExperimentType, ProtocolStep,
        Variable, VariableType, ControlGroup, StatisticalTestSpec,
        StatisticalTest, ResourceRequirements
    )

    # Build a proper ExperimentProtocol object with all required fields
    protocol = ExperimentProtocol(
        name="Temperature Effect T-Test",
        hypothesis_id="test-hyp-001",
        experiment_type=ExperimentType.DATA_ANALYSIS,
        domain="biology",
        description="Compare enzyme activity at different temperatures using independent samples t-test",
        objective="Determine if temperature significantly affects enzyme activity",
        steps=[
            ProtocolStep(step_number=1, title="Generate data", description="Generate synthetic temperature and enzyme activity data", action="Generate synthetic data"),
            ProtocolStep(step_number=2, title="Run t-test", description="Perform independent samples t-test comparing groups", action="Perform independent samples t-test"),
            ProtocolStep(step_number=3, title="Effect size", description="Calculate Cohen's d effect size for the comparison", action="Calculate Cohen's d effect size"),
        ],
        variables={
            "temperature": Variable(name="temperature", type=VariableType.INDEPENDENT, description="Temperature in Celsius"),
            "enzyme_activity": Variable(name="enzyme_activity", type=VariableType.DEPENDENT, description="Enzyme activity rate"),
        },
        statistical_tests=[
            StatisticalTestSpec(
                test_type=StatisticalTest.T_TEST,
                description="Independent t-test comparing temperature groups",
                null_hypothesis="No difference in enzyme activity between temperature groups",
                variables=["temperature", "enzyme_activity"]
            )
        ],
        sample_size=100,
        control_groups=[
            ControlGroup(name="control", description="Room temperature 25C baseline", variables={"temperature": 25}, rationale="Standard room temperature as baseline comparison")
        ],
        resource_requirements=ResourceRequirements(
            estimated_duration_minutes=5,
            estimated_cost_usd=0.01,
            compute_hours=0.1
        )
    )

    template = TTestComparisonCodeTemplate()
    code = template.generate(protocol)

    result = {
        "code_generated": bool(code),
        "code_length": len(code),
        "code_preview": code[:500] if code else "No code generated",
        "has_data_source_flag": "_data_source" in code,
        "uses_synthetic_data": "synthetic" in code.lower() or "np.random" in code,
        "hardcoded_effect_size": "0.5" in code,
    }

    # Execute the code
    executor = CodeExecutor()
    try:
        exec_result = executor.execute(code)
        result["execution"] = {
            "success": exec_result.success,
            "stdout": str(getattr(exec_result, 'stdout', ''))[:500],
            "stderr": str(getattr(exec_result, 'stderr', ''))[:500],
            "error": str(getattr(exec_result, 'error', ''))[:500] if exec_result.error else None,
            "return_value": str(getattr(exec_result, 'return_value', ''))[:500],
        }
        print(f"  Code length: {result['code_length']} chars")
        print(f"  Execution success: {result['execution']['success']}")
        print(f"  Has _data_source flag: {result['has_data_source_flag']}")
        print(f"  Hardcoded effect_size=0.5: {result['hardcoded_effect_size']}")
        if not exec_result.success:
            print(f"  Error: {result['execution']['error'][:200]}")
    except Exception as e:
        result["execution"] = {"success": False, "error": str(e)[:500]}
        print(f"  Execution failed: {e}")

    result["gap_notes"] = [
        f"Synthetic data flag in code: {result['has_data_source_flag']}",
        f"Uses synthetic data: {result['uses_synthetic_data']}",
        f"Hardcoded effect_size=0.5: {result['hardcoded_effect_size']}",
        "Direct exec() used (no Docker sandbox by default)"
    ]

    return result


# ============================================================
# Test 2.5: Data Analysis
# ============================================================
def test_data_analysis():
    from kosmos.agents.data_analyst import DataAnalystAgent
    from kosmos.models.result import ExperimentResult, ResultStatus, ExecutionMetadata, StatisticalTestResult

    agent = DataAnalystAgent()

    # Create a proper ExperimentResult with required fields
    mock_result = ExperimentResult(
        experiment_id="test-exp-001",
        protocol_id="test-proto-001",
        hypothesis_id="test-hyp-001",
        status=ResultStatus.SUCCESS,
        primary_p_value=0.003,
        primary_effect_size=0.8,
        statistical_tests=[
            StatisticalTestResult(
                test_type="t_test",
                test_name="independent_t_test",
                statistic=-12.5,
                p_value=0.003,
                effect_size=0.8,
                effect_size_type="cohens_d",
                significant_0_05=True,
                significant_0_01=True,
                significant_0_001=False,
                significance_label="**",
                is_primary=True,
                sample_size=100,
            )
        ],
        primary_test="independent_t_test",
        metadata=ExecutionMetadata(
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow(),
            duration_seconds=5.0,
            python_version="3.11",
            platform="linux",
            experiment_id="test-exp-001",
            protocol_id="test-proto-001",
        ),
        summary="T-test comparing enzyme activity at 25C vs 37C: significant difference (p=0.003, d=0.8)",
        raw_data={"control_mean": 45.0, "treatment_mean": 98.0}
    )

    from kosmos.models.hypothesis import Hypothesis
    hypothesis = Hypothesis(
        research_question="How does temperature affect enzyme activity?",
        statement="Higher temperature increases enzyme activity",
        rationale="Enzyme kinetics theory predicts activity increases with temperature",
        domain="biology"
    )

    interpretation = agent.interpret_results(
        result=mock_result,
        hypothesis=hypothesis,
        literature_context=None
    )

    result = {
        "interpretation_received": bool(interpretation),
        "interpretation_type": type(interpretation).__name__,
    }

    # Extract key fields from interpretation
    if hasattr(interpretation, 'hypothesis_supported'):
        result["hypothesis_supported"] = interpretation.hypothesis_supported
        result["confidence"] = getattr(interpretation, 'confidence', None)
        result["summary"] = getattr(interpretation, 'summary', '')[:300]
        result["key_findings"] = getattr(interpretation, 'key_findings', [])[:3]
        result["anomalies_detected"] = getattr(interpretation, 'anomalies_detected', [])
    else:
        result["interpretation_preview"] = str(interpretation)[:500]

    print(f"  Interpretation received: {result['interpretation_received']}")
    print(f"  Type: {result['interpretation_type']}")
    if 'hypothesis_supported' in result:
        print(f"  Hypothesis supported: {result['hypothesis_supported']}")
        print(f"  Confidence: {result.get('confidence')}")

    result["supports_hypothesis_method"] = "LLM-based (not formal statistical criteria)"
    result["gap_notes"] = [
        "supports_hypothesis set by LLM interpretation, not formal criteria",
        "No check for _data_source (synthetic vs real)",
        "No check_assumptions() called before interpretation"
    ]

    return result


# ============================================================
# Test 2.6: Convergence Detection
# ============================================================
def test_convergence_detection():
    from kosmos.core.convergence import ConvergenceDetector
    from kosmos.models.hypothesis import Hypothesis
    from kosmos.core.workflow import ResearchPlan

    detector = ConvergenceDetector(config={"max_iterations": 5})

    plan = ResearchPlan(
        research_question="How does temperature affect enzyme activity?",
        domain="biology",
        max_iterations=5,
        iteration_count=5  # At the limit
    )

    decision1 = detector.check_convergence(
        research_plan=plan,
        hypotheses=[],
        results=[]
    )

    result = {
        "test_max_iterations": {
            "should_stop": decision1.should_stop,
            "reason": str(decision1.reason),
            "details": getattr(decision1, 'details', '')
        }
    }
    print(f"  Max iterations test: stop={decision1.should_stop}, reason={decision1.reason}")

    # Test 2: Declining novelty
    detector2 = ConvergenceDetector(config={"max_iterations": 20})
    plan2 = ResearchPlan(
        research_question="Test",
        domain="biology",
        max_iterations=20,
        iteration_count=6
    )

    hypotheses = []
    for i, score in enumerate([0.8, 0.6, 0.4, 0.2, 0.1]):
        h = Hypothesis(
            research_question="How does temperature affect enzyme activity?",
            statement=f"Hypothesis {i} about enzyme activity and temperature effects on catalysis",
            rationale="Test rationale for testing convergence detection system",
            domain="biology",
            novelty_score=score,
            testability_score=0.5
        )
        hypotheses.append(h)

    for score in [0.8, 0.6, 0.4, 0.2, 0.1]:
        detector2.metrics.novelty_trend.append(score)

    decision2 = detector2.check_convergence(
        research_plan=plan2,
        hypotheses=hypotheses,
        results=[]
    )

    result["test_novelty_decline"] = {
        "should_stop": decision2.should_stop,
        "reason": str(decision2.reason),
        "novelty_trend": list(detector2.metrics.novelty_trend),
        "details": getattr(decision2, 'details', '')
    }
    print(f"  Novelty decline test: stop={decision2.should_stop}, reason={decision2.reason}")

    result["cost_tracking"] = {
        "total_cost": detector2.metrics.total_cost,
        "is_always_zero": detector2.metrics.total_cost == 0.0,
        "note": "total_cost is never propagated from LLM calls"
    }
    print(f"  Cost tracking: total_cost={detector2.metrics.total_cost} (always 0.0)")

    return result


# ============================================================
# Run all tests
# ============================================================
if __name__ == "__main__":
    print(f"Phase 2 Component Tests - {datetime.now().isoformat()}")
    print(f"{'='*60}")

    tests = [
        ("2.1_hypothesis_generation", test_hypothesis_generation),
        ("2.2_literature_search", test_literature_search),
        ("2.3_experiment_design", test_experiment_design),
        ("2.4_code_execution", test_code_execution),
        ("2.5_data_analysis", test_data_analysis),
        ("2.6_convergence_detection", test_convergence_detection),
    ]

    for name, func in tests:
        test_component(name, func)

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results.values() if r.get("status") == "PASS")
    failed = sum(1 for r in results.values() if r.get("status") == "FAIL")
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    for name, r in results.items():
        status = r.get("status", "UNKNOWN")
        duration = r.get("duration_seconds", 0)
        print(f"  {status}: {name} ({duration:.1f}s)")
        if status == "FAIL":
            print(f"    Error: {r.get('error', 'unknown')[:200]}")

    output_path = "/mnt/c/python/Kosmos/evaluation/artifacts/phase2_components"
    os.makedirs(output_path, exist_ok=True)

    for name, r in results.items():
        filepath = os.path.join(output_path, f"{name}.json")
        with open(filepath, "w") as f:
            json.dump(r, f, indent=2, default=str)

    with open(os.path.join(output_path, "all_components.json"), "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults saved to {output_path}/")
