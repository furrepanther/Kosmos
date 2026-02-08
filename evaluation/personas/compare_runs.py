#!/usr/bin/env python3
"""
Regression comparison tool for persona-based evaluations.

Compares two versioned runs of the same persona and produces a JSON diff
of checks, quality scores, rigor scores, and paper claims.

Usage:
    python evaluation/personas/compare_runs.py \
        --persona 001_enzyme_kinetics_biologist \
        --v1 v001_20260207 \
        --v2 v002_20260210
"""

import argparse
import json
import re
import sys
from pathlib import Path

PERSONAS_DIR = Path(__file__).parent
RUNS_DIR = PERSONAS_DIR / "runs"


def load_meta(run_dir: Path) -> dict:
    """Load meta.json from a run directory."""
    meta_path = run_dir / "meta.json"
    if not meta_path.exists():
        print(f"ERROR: meta.json not found in {run_dir}")
        sys.exit(1)
    with open(meta_path) as f:
        return json.load(f)


def parse_evaluation_report(run_dir: Path) -> dict:
    """Parse an evaluation report markdown into structured data."""
    report_path = run_dir / "tier1" / "EVALUATION_REPORT.md"
    if not report_path.exists():
        return {"checks": {}, "quality_scores": {}, "rigor_scores": {},
                "paper_claims": {}, "summary": {}}

    content = report_path.read_text()
    result = {
        "checks": {},
        "quality_scores": {},
        "rigor_scores": {},
        "paper_claims": {},
        "summary": {},
    }

    # Parse summary line: "Checks passed: 36/37" or "36/37 checks passed"
    match = re.search(r"Checks passed.*?(\d+)/(\d+)", content)
    if not match:
        match = re.search(r"(\d+)/(\d+)\s+checks?\s+passed", content)
    if match:
        result["summary"]["checks_passed"] = int(match.group(1))
        result["summary"]["checks_total"] = int(match.group(2))

    # Parse duration
    match = re.search(r"Total duration.*?(\d+\.?\d*)\s*s", content)
    if match:
        result["summary"]["duration_seconds"] = float(match.group(1))

    # Parse check table rows: "| check_name | PASS/FAIL | detail |"
    check_pattern = re.compile(
        r"\|\s*(\w+)\s*\|\s*(PASS|FAIL)\s*\|([^|]*)\|"
    )
    for match in check_pattern.finditer(content):
        name = match.group(1).strip()
        passed = match.group(2).strip() == "PASS"
        result["checks"][name] = passed

    # Parse quality scores: "| dimension | N/10 | details |"
    quality_pattern = re.compile(
        r"\|\s*(phase\d+_\w+)\s*\|\s*(\d+)/10\s*\|([^|]*)\|"
    )
    for match in quality_pattern.finditer(content):
        dimension = match.group(1).strip()
        score = int(match.group(2))
        result["quality_scores"][dimension] = score

    # Parse average quality score
    match = re.search(r"Average Quality Score.*?(\d+\.?\d*)/10", content)
    if match:
        result["summary"]["quality_score"] = float(match.group(1))

    # Parse rigor scores: "| feature | N/10 | notes |"
    rigor_pattern = re.compile(
        r"\|\s*(\w+)\s*\|\s*(\d+)/10\s*\|\s*([^|]+)\|"
    )
    # Only capture rigor scores from the rigor section
    rigor_section = ""
    rigor_match = re.search(
        r"Scientific Rigor Scorecard.*?\n(.*?)(?=\n##|\Z)",
        content, re.DOTALL,
    )
    if rigor_match:
        rigor_section = rigor_match.group(1)
        for match in rigor_pattern.finditer(rigor_section):
            feature = match.group(1).strip()
            # Skip if it looks like a quality score (phase2_, phase3_)
            if feature.startswith("phase"):
                continue
            score = int(match.group(2))
            result["rigor_scores"][feature] = score

    # Parse average rigor score
    match = re.search(r"Average Rigor Score.*?(\d+\.?\d*)/10", content)
    if match:
        result["summary"]["rigor_score"] = float(match.group(1))

    # Parse paper claims: "| N | claim | STATUS | detail |"
    claims_pattern = re.compile(
        r"\|\s*(\d+)\s*\|\s*([^|]+)\|\s*(PASS|PARTIAL|FAIL|BLOCKER)\s*\|([^|]*)\|"
    )
    for match in claims_pattern.finditer(content):
        claim_num = int(match.group(1))
        status = match.group(3).strip()
        result["paper_claims"][claim_num] = status

    # Parse paper claims summary
    claims_summary = re.search(
        r"PASS=(\d+),\s*PARTIAL=(\d+),\s*FAIL=(\d+),\s*BLOCKER=(\d+)",
        content,
    )
    if claims_summary:
        result["summary"]["paper_claims_pass"] = int(claims_summary.group(1))
        result["summary"]["paper_claims_partial"] = int(claims_summary.group(2))
        result["summary"]["paper_claims_fail"] = int(claims_summary.group(3))
        result["summary"]["paper_claims_blocker"] = int(claims_summary.group(4))

    return result


def compute_delta(v1_val, v2_val):
    """Compute delta between two numeric values."""
    if v1_val is None or v2_val is None:
        return "N/A"
    delta = v2_val - v1_val
    if delta > 0:
        return f"+{delta}"
    elif delta == 0:
        return "0"
    else:
        return str(delta)


def compare_runs(persona_name: str, v1_name: str, v2_name: str) -> dict:
    """Compare two versioned runs and produce a diff."""
    v1_dir = RUNS_DIR / persona_name / v1_name
    v2_dir = RUNS_DIR / persona_name / v2_name

    if not v1_dir.exists():
        print(f"ERROR: Run not found: {v1_dir}")
        sys.exit(1)
    if not v2_dir.exists():
        print(f"ERROR: Run not found: {v2_dir}")
        sys.exit(1)

    meta1 = load_meta(v1_dir)
    meta2 = load_meta(v2_dir)

    report1 = parse_evaluation_report(v1_dir)
    report2 = parse_evaluation_report(v2_dir)

    # Summary comparison
    summary = {}
    for key in ["checks_passed", "checks_total", "quality_score",
                "rigor_score", "paper_claims_pass"]:
        v1_val = report1["summary"].get(key)
        v2_val = report2["summary"].get(key)
        summary[key] = {
            "v1": v1_val,
            "v2": v2_val,
            "delta": compute_delta(v1_val, v2_val),
        }

    # Check changes
    all_checks = set(report1["checks"].keys()) | set(report2["checks"].keys())
    improved = []
    regressed = []
    unchanged = []
    for check in sorted(all_checks):
        v1_passed = report1["checks"].get(check)
        v2_passed = report2["checks"].get(check)
        if v1_passed == v2_passed:
            unchanged.append(check)
        elif v2_passed and not v1_passed:
            improved.append(check)
        elif v1_passed and not v2_passed:
            regressed.append(check)
        else:
            unchanged.append(check)  # Both None or same

    # Quality score changes
    quality_changes = {}
    all_dims = set(report1["quality_scores"].keys()) | set(report2["quality_scores"].keys())
    for dim in sorted(all_dims):
        v1_val = report1["quality_scores"].get(dim)
        v2_val = report2["quality_scores"].get(dim)
        quality_changes[dim] = {
            "v1": v1_val,
            "v2": v2_val,
            "delta": compute_delta(v1_val, v2_val),
        }

    # Rigor score changes
    rigor_changes = {}
    all_rigor = set(report1["rigor_scores"].keys()) | set(report2["rigor_scores"].keys())
    for feature in sorted(all_rigor):
        v1_val = report1["rigor_scores"].get(feature)
        v2_val = report2["rigor_scores"].get(feature)
        rigor_changes[feature] = {
            "v1": v1_val,
            "v2": v2_val,
            "delta": compute_delta(v1_val, v2_val),
        }

    # Paper claims changes
    paper_changes = {}
    all_claims = set(report1["paper_claims"].keys()) | set(report2["paper_claims"].keys())
    for claim in sorted(all_claims):
        v1_status = report1["paper_claims"].get(claim, "N/A")
        v2_status = report2["paper_claims"].get(claim, "N/A")
        if v1_status != v2_status:
            paper_changes[claim] = {"v1": v1_status, "v2": v2_status}

    comparison = {
        "persona": persona_name,
        "baseline": v1_name,
        "current": v2_name,
        "baseline_timestamp": meta1.get("timestamp"),
        "current_timestamp": meta2.get("timestamp"),
        "summary": summary,
        "check_changes": {
            "improved": improved,
            "regressed": regressed,
            "unchanged": unchanged,
        },
        "quality_changes": quality_changes,
        "rigor_changes": rigor_changes,
        "paper_claim_changes": paper_changes,
    }

    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Compare two versioned persona evaluation runs",
    )
    parser.add_argument(
        "--persona", required=True,
        help="Persona name (e.g., 001_enzyme_kinetics_biologist)",
    )
    parser.add_argument(
        "--v1", required=True,
        help="Baseline version directory name (e.g., v001_20260207)",
    )
    parser.add_argument(
        "--v2", required=True,
        help="Current version directory name (e.g., v002_20260210)",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output file path (default: regression/{v1}_vs_{v2}.json)",
    )
    args = parser.parse_args()

    comparison = compare_runs(args.persona, args.v1, args.v2)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        regression_dir = RUNS_DIR / args.persona / "regression"
        regression_dir.mkdir(parents=True, exist_ok=True)
        output_path = regression_dir / f"{args.v1}_vs_{args.v2}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(comparison, f, indent=2)

    print(f"Comparison written to: {output_path}")
    print()

    # Print summary
    s = comparison["summary"]
    print(f"  {'Metric':<20} {'Baseline':>10} {'Current':>10} {'Delta':>10}")
    print(f"  {'-' * 50}")
    for key, vals in s.items():
        v1_str = str(vals["v1"]) if vals["v1"] is not None else "N/A"
        v2_str = str(vals["v2"]) if vals["v2"] is not None else "N/A"
        print(f"  {key:<20} {v1_str:>10} {v2_str:>10} {vals['delta']:>10}")

    changes = comparison["check_changes"]
    if changes["improved"]:
        print(f"\n  Improved: {', '.join(changes['improved'])}")
    if changes["regressed"]:
        print(f"\n  Regressed: {', '.join(changes['regressed'])}")
    print(f"\n  Unchanged: {len(changes['unchanged'])} checks")


if __name__ == "__main__":
    main()
