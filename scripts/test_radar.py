#!/usr/bin/env python3
"""test_radar.py — 10 acceptance tests for the Transition Radar."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RADAR_JSON = ROOT / "radar.json"

sys.path.insert(0, str(Path(__file__).parent))
from generate_radar import compute_score, CATEGORY_WEIGHTS, GAP_BONUS, RING_ORDER

PASS = "✅"
FAIL = "❌"


def load():
    with open(RADAR_JSON) as f:
        return json.load(f)


def test(name, condition, detail=""):
    if condition:
        print(f"  {PASS} {name}")
    else:
        print(f"  {FAIL} {name}{' — ' + detail if detail else ''}")
    return condition


def run_tests():
    print("Running Transition Radar acceptance tests...\n")
    radar = load()
    blips = radar["blips"]
    results = []

    # 1. RAG Pipeline is #1 in Trial with score 36
    rag = next((b for b in blips if b["name"] == "RAG Pipeline"), None)
    results.append(test(
        "RAG Pipeline exists in Trial ring with score 36",
        rag and rag["ring"] == "trial" and rag["transition_score"] == 36,
        f"found: ring={rag['ring'] if rag else None}, score={rag['transition_score'] if rag else None}"
    ))

    # 2. Score formula is correct for all blips
    mismatches = []
    for b in blips:
        computed = compute_score(b)
        if computed != b.get("transition_score", -1):
            mismatches.append(f"{b['name']}: stored={b.get('transition_score')}, computed={computed}")
    results.append(test(
        "All transition_score values match formula",
        len(mismatches) == 0,
        "; ".join(mismatches[:3])
    ))

    # 3. Top 5 Trial blips match expected focus board
    trial = sorted([b for b in blips if b["ring"] == "trial"], key=lambda b: b["transition_score"], reverse=True)
    top5_names = [b["name"] for b in trial[:5]]
    expected_1 = "RAG Pipeline"
    results.append(test(
        f"Top Trial blip is '{expected_1}'",
        top5_names[0] == expected_1 if top5_names else False,
        f"actual: {top5_names[0] if top5_names else 'none'}"
    ))

    # 4. Distribution check: 10 Trial
    trial_count = len([b for b in blips if b["ring"] == "trial"])
    results.append(test(
        f"Trial ring has 10 blips (got {trial_count})",
        trial_count == 10,
        f"got {trial_count}"
    ))

    # 5. Distribution check: 13 Adopt
    adopt_count = len([b for b in blips if b["ring"] == "adopt"])
    results.append(test(
        f"Adopt ring has 13 blips (got {adopt_count})",
        adopt_count == 13,
        f"got {adopt_count}"
    ))

    # 6. Java is in Hold (not Adopt)
    java = next((b for b in blips if b["name"] == "Java"), None)
    results.append(test(
        "Java is in Hold ring (legacy, not marketed as primary)",
        java and java["ring"] == "hold",
        f"found ring: {java['ring'] if java else None}"
    ))

    # 7. No blip has score > 40 (sanity cap)
    max_score = max(b.get("transition_score", 0) for b in blips)
    results.append(test(
        f"No blip score exceeds 40 (max found: {max_score})",
        max_score <= 40,
        f"max={max_score}"
    ))

    # 8. All blips have required fields
    required = ["name", "quadrant", "ring", "category", "demand", "gap", "transition_score"]
    missing = [b["name"] for b in blips if not all(f in b for f in required)]
    results.append(test(
        "All blips have required fields",
        len(missing) == 0,
        f"missing in: {missing[:3]}"
    ))

    # 9. Category weights are correct in formula
    # ai_core YES 0 demand → score = 10 + 0 + 0 = 10
    synthetic = {"category": "ai_core", "demand": 0, "gap": "YES"}
    results.append(test(
        "Category weight for ai_core is 10 (score check)",
        compute_score(synthetic) == 10,
        f"got {compute_score(synthetic)}"
    ))

    # 10. LEARNING gap adds 5 points vs NO adds 2
    base = {"category": "ai_core", "demand": 0, "gap": "YES"}
    learning = {**base, "gap": "LEARNING"}
    no = {**base, "gap": "NO"}
    results.append(test(
        "GAP bonus: LEARNING=5, NO=2 (score diff verified)",
        compute_score(learning) - compute_score(base) == 5 and compute_score(no) - compute_score(base) == 2,
        f"LEARNING diff={compute_score(learning)-compute_score(base)}, NO diff={compute_score(no)-compute_score(base)}"
    ))

    passed = sum(results)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    # Fix import name
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "generate_radar",
        Path(__file__).parent / "generate-radar.py"
    )
    mod = importlib.util.load_from_spec = spec
    sys.exit(0 if run_tests() else 1)
