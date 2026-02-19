#!/usr/bin/env python3
"""
test_radar.py -- Acceptance tests for the Transition Radar

Verifies that the radar correctly prioritizes AI/ML transition skills
over legacy engineering skills. These tests encode the core promise:
"RAG is #1, not Java. Trial drives learning investment, not Adopt."

Run: python test_radar.py [path/to/radar.json]
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# =============================================================================
# LOAD RADAR DATA
# =============================================================================
def load_radar(path=None):
    if path is None:
        path = Path(__file__).parent.parent / "radar.json"
    else:
        path = Path(path)
    with open(path) as f:
        return json.load(f)


# =============================================================================
# TRANSITION SCORE REFERENCE (must match generate-radar.py)
# =============================================================================
CATEGORY_WEIGHT = {"ai_core": 10, "bridge": 8, "enabler": 4, "legacy": 1, "irrelevant": 0}
GAP_BONUS = {"LEARNING": 5, "NO": 2, "YES": 0}

def expected_score(category, demand_count, you_have_it):
    return CATEGORY_WEIGHT[category] + (demand_count * 3) + GAP_BONUS.get(you_have_it, 0)


# =============================================================================
# TEST RUNNER
# =============================================================================
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def ok(self, name):
        self.passed += 1
        print(f"  PASS  {name}")

    def fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  FAIL  {name}")
        print(f"        {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"  {self.passed}/{total} tests passed", end="")
        if self.failed > 0:
            print(f"  ({self.failed} FAILED)")
            for name, reason in self.errors:
                print(f"    - {name}: {reason}")
        else:
            print("  -- ALL PASS")
        print(f"{'='*60}")
        return self.failed == 0


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def by_ring(blips):
    rings = defaultdict(list)
    for b in blips:
        rings[b["ring"]].append(b)
    return rings

def find_blip(blips, name):
    for b in blips:
        if b["name"].lower() == name.lower():
            return b
    return None


# =============================================================================
# ACCEPTANCE TESTS
# =============================================================================

def test_1_rag_is_number_one(blips, results):
    """Test 1: RAG is #1 (the headline test)"""
    name = "Test 1: RAG is #1 overall"

    rag = find_blip(blips, "RAG pipeline")
    if rag is None:
        results.fail(name, "RAG pipeline not found in radar")
        return

    errors = []
    if rag["ring"] != "Trial":
        errors.append(f"ring={rag['ring']}, expected Trial")
    if rag["transition_score"] < 35:
        errors.append(f"score={rag['transition_score']}, expected >= 35")

    # Check it's actually first when sorted by score
    sorted_blips = sorted(blips, key=lambda b: -b["transition_score"])
    if sorted_blips[0]["name"] != "RAG pipeline":
        errors.append(f"#1 by score is '{sorted_blips[0]['name']}', not RAG pipeline")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_2_trial_is_transition_worthy(blips, results):
    """Test 2: Trial ring contains only transition-worthy skills"""
    name = "Test 2: Trial ring is transition-worthy"
    rings = by_ring(blips)
    trial = rings.get("Trial", [])

    if not trial:
        results.fail(name, "Trial ring is empty")
        return

    errors = []
    for b in trial:
        # Every Trial item must be ai_core or bridge
        if b["category"] not in ("ai_core", "bridge"):
            errors.append(f"'{b['name']}' has category={b['category']} (need ai_core/bridge)")

        # Every Trial item should not be YES (you should be learning/gap)
        # Exception: strategic overrides might exist
        if b["name"] not in ("MCP (Model Context Protocol)",):  # known override
            if b["you_have_it"] == "YES":
                errors.append(f"'{b['name']}' has you_have_it=YES (Trial should have gaps)")

        # Demand >= 2 (unless override)
        if b["name"] not in ("MCP (Model Context Protocol)",):
            if b["demand_count"] < 2:
                errors.append(f"'{b['name']}' has demand={b['demand_count']} (need >= 2)")

    # Trial should be sorted by transition_score DESC
    scores = [b["transition_score"] for b in trial]
    sorted_scores = sorted(scores, reverse=True)
    if scores != sorted_scores:
        errors.append(f"Trial not sorted by score DESC: {scores}")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_3_zero_demand_legacy_not_in_adopt(blips, results):
    """Test 3: Zero-demand legacy skills are NOT in Adopt"""
    name = "Test 3: 0-demand legacy -> Hold"

    errors = []
    must_be_hold = ["Java", "Spring Boot", "REST API design"]

    for skill_name in must_be_hold:
        b = find_blip(blips, skill_name)
        if b is None:
            errors.append(f"'{skill_name}' not found")
            continue
        if b["ring"] != "Hold":
            errors.append(f"'{skill_name}' in {b['ring']}, expected Hold")

    # General check: no legacy + 0 demand in Adopt
    for b in blips:
        if b["category"] == "legacy" and b["demand_count"] == 0 and b["ring"] == "Adopt":
            errors.append(f"'{b['name']}' is legacy/0-demand but in Adopt")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_4_adopt_is_marketable_ai_relevant(blips, results):
    """Test 4: Adopt contains only marketable AI-relevant skills"""
    name = "Test 4: Adopt is marketable + AI-relevant"
    rings = by_ring(blips)
    adopt = rings.get("Adopt", [])

    errors = []
    for b in adopt:
        if b["you_have_it"] != "YES":
            errors.append(f"'{b['name']}' has you_have_it={b['you_have_it']} (Adopt needs YES)")
        if b["demand_count"] < 1:
            errors.append(f"'{b['name']}' has demand={b['demand_count']} (Adopt needs >= 1)")
        if b["category"] == "irrelevant":
            errors.append(f"'{b['name']}' has category=irrelevant (shouldn't be in Adopt)")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_5_focus_board_actionable(blips, results):
    """Test 5: Focus Board (top 5 by score) is answerable in 3 seconds"""
    name = "Test 5: Focus Board drives action"
    rings = by_ring(blips)
    trial = sorted(rings.get("Trial", []), key=lambda b: -b["transition_score"])
    top5 = trial[:5]

    if len(top5) < 3:
        results.fail(name, f"Focus Board has only {len(top5)} items (need at least 3)")
        return

    errors = []
    # All from Trial ring (guaranteed by selection)
    # All ai_core or bridge
    for b in top5:
        if b["category"] not in ("ai_core", "bridge"):
            errors.append(f"'{b['name']}' in Focus Board but category={b['category']}")

    # #1 must be RAG Pipeline
    if top5[0]["name"] != "RAG pipeline":
        errors.append(f"#1 is '{top5[0]['name']}', expected 'RAG pipeline'")

    # Scores must decrease monotonically (allow ties)
    for i in range(1, len(top5)):
        if top5[i]["transition_score"] > top5[i-1]["transition_score"]:
            errors.append(f"Score increases at position {i+1}: {top5[i]['transition_score']} > {top5[i-1]['transition_score']}")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_6_transition_score_formula(blips, results):
    """Test 6: Transition score formula is correct for known skills"""
    name = "Test 6: Score formula verified"

    test_cases = [
        ("RAG pipeline", "ai_core", 11, "LEARNING", 48),
        ("Agentic AI systems", "ai_core", 5, "LEARNING", 30),
        ("Java", "legacy", 0, "YES", 1),
        ("C++", "irrelevant", 2, "NO", 8),
    ]

    errors = []
    for skill_name, exp_cat, exp_demand, exp_have, exp_score in test_cases:
        b = find_blip(blips, skill_name)
        if b is None:
            errors.append(f"'{skill_name}' not found")
            continue

        # Verify category
        if b["category"] != exp_cat:
            errors.append(f"'{skill_name}' category={b['category']}, expected {exp_cat}")

        # Verify score matches formula
        calc = expected_score(b["category"], b["demand_count"], b["you_have_it"])
        if b["transition_score"] != calc:
            errors.append(f"'{skill_name}' score={b['transition_score']}, formula gives {calc}")

        # Verify against expected
        if b["transition_score"] != exp_score:
            errors.append(f"'{skill_name}' score={b['transition_score']}, expected {exp_score}")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_7_ring_distribution_healthy(blips, results):
    """Test 7: Ring distribution is transition-healthy"""
    name = "Test 7: Ring distribution balanced"
    rings = by_ring(blips)

    trial_count = len(rings.get("Trial", []))
    adopt_count = len(rings.get("Adopt", []))
    assess_count = len(rings.get("Assess", []))
    hold_count = len(rings.get("Hold", []))

    errors = []
    if trial_count < 5:
        errors.append(f"Trial has {trial_count} items (need 5-10 for focused investment)")
    if trial_count > 12:
        errors.append(f"Trial has {trial_count} items (too many, focus means saying no)")
    if adopt_count < 3:
        errors.append(f"Adopt has {adopt_count} items (need 3-15 marketable strengths)")
    if adopt_count > 15:
        errors.append(f"Adopt has {adopt_count} items (too many, dilutes signal)")

    dist = f"Trial={trial_count}, Adopt={adopt_count}, Assess={assess_count}, Hold={hold_count}"
    if errors:
        results.fail(name, f"{'; '.join(errors)} [{dist}]")
    else:
        results.ok(name + f" [{dist}]")


def test_8_data_fidelity(blips, results):
    """Test 8: Data fidelity -- no missing fields, valid categories"""
    name = "Test 8: Data fidelity"

    valid_rings = {"Trial", "Adopt", "Assess", "Hold"}
    valid_quadrants = {"Languages & Frameworks", "Tools", "Techniques", "Platforms"}
    valid_categories = {"ai_core", "bridge", "enabler", "legacy", "irrelevant"}

    errors = []
    names_seen = set()

    for i, b in enumerate(blips):
        # Required fields
        for field in ["name", "quadrant", "ring", "category", "transition_score",
                      "demand_count", "you_have_it"]:
            if field not in b:
                errors.append(f"Blip #{i} missing field '{field}'")

        # Valid values
        if b.get("ring") not in valid_rings:
            errors.append(f"'{b.get('name')}' has invalid ring: {b.get('ring')}")
        if b.get("quadrant") not in valid_quadrants:
            errors.append(f"'{b.get('name')}' has invalid quadrant: {b.get('quadrant')}")
        if b.get("category") not in valid_categories:
            errors.append(f"'{b.get('name')}' has invalid category: {b.get('category')}")

        # No duplicates
        n = b.get("name", "")
        if n in names_seen:
            errors.append(f"Duplicate blip: '{n}'")
        names_seen.add(n)

    # Minimum total blips
    if len(blips) < 40:
        errors.append(f"Only {len(blips)} blips (expected 40+)")

    if errors:
        results.fail(name, "; ".join(errors[:5]))  # cap at 5 errors
    else:
        results.ok(name + f" [{len(blips)} blips, all valid]")


def test_9_nlp_and_bridge_categories(blips, results):
    """Test 9: Specific category assignments are correct (regression test for lookup bugs)"""
    name = "Test 9: Category assignments correct"

    # These were buggy before: normalized names didn't match CATEGORY_MAP keys
    expected = {
        "NLP (embeddings, ranking)": "ai_core",
        "AI-assisted development": "bridge",
        "Banking/payments domain": "bridge",
        "LLM APIs (production)": "ai_core",
        "Python": "enabler",
        "Java": "legacy",
        "C++": "irrelevant",
        "MCP (Model Context Protocol)": "bridge",
    }

    errors = []
    for skill_name, exp_cat in expected.items():
        b = find_blip(blips, skill_name)
        if b is None:
            errors.append(f"'{skill_name}' not found")
            continue
        if b["category"] != exp_cat:
            errors.append(f"'{skill_name}' category={b['category']}, expected {exp_cat}")

    if errors:
        results.fail(name, "; ".join(errors))
    else:
        results.ok(name)


def test_10_pipeline_end_to_end(blips, results):
    """Test 10: Pipeline produces valid output with new schema"""
    name = "Test 10: Pipeline end-to-end"

    errors = []

    # New schema fields present
    for b in blips:
        if "category" not in b:
            errors.append(f"'{b.get('name')}' missing 'category' field")
        if "transition_score" not in b:
            errors.append(f"'{b.get('name')}' missing 'transition_score' field")

    # Global sort is by transition_score DESC
    scores = [b["transition_score"] for b in blips]
    for i in range(1, len(scores)):
        if scores[i] > scores[i-1]:
            errors.append(f"Global sort broken at position {i}: {scores[i]} > {scores[i-1]}")
            break

    # First item should be RAG (highest score)
    if blips and blips[0]["name"] != "RAG pipeline":
        errors.append(f"First blip is '{blips[0]['name']}', expected 'RAG pipeline'")

    # Last items should be low-score Hold items
    if blips and blips[-1]["ring"] != "Hold":
        errors.append(f"Last blip '{blips[-1]['name']}' is in {blips[-1]['ring']}, expected Hold")

    if errors:
        results.fail(name, "; ".join(errors[:5]))
    else:
        results.ok(name)


# =============================================================================
# MAIN
# =============================================================================
def main():
    radar_path = sys.argv[1] if len(sys.argv) > 1 else None
    blips = load_radar(radar_path)

    print(f"\n{'='*60}")
    print(f"  TRANSITION RADAR -- Acceptance Tests")
    print(f"  Testing {len(blips)} blips")
    print(f"{'='*60}\n")

    results = TestResults()

    test_1_rag_is_number_one(blips, results)
    test_2_trial_is_transition_worthy(blips, results)
    test_3_zero_demand_legacy_not_in_adopt(blips, results)
    test_4_adopt_is_marketable_ai_relevant(blips, results)
    test_5_focus_board_actionable(blips, results)
    test_6_transition_score_formula(blips, results)
    test_7_ring_distribution_healthy(blips, results)
    test_8_data_fidelity(blips, results)
    test_9_nlp_and_bridge_categories(blips, results)
    test_10_pipeline_end_to_end(blips, results)

    all_pass = results.summary()
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
