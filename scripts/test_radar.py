#!/usr/bin/env python3
"""test_radar.py — Acceptance tests for Transition Radar v2."""

import json
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).parent.parent
RADAR_JSON = ROOT / "radar.json"

# Load generate-radar module (filename has hyphen, use spec)
spec = importlib.util.spec_from_file_location("gen", Path(__file__).parent / "generate-radar.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def chk(name, cond, detail=""):
    icon = "✅" if cond else "❌"
    suffix = f" — {detail}" if not cond and detail else ""
    print(f"  {icon} {name}{suffix}")
    return cond


def run():
    print("Running Transition Radar acceptance tests…\n")
    radar = json.load(open(RADAR_JSON))
    blips = radar["blips"]
    results = []

    # 1. RAG Pipeline is #1 Trial with score 36
    rag = next((b for b in blips if b["name"] == "RAG Pipeline"), None)
    results.append(chk(
        "RAG Pipeline: ring=trial, score=36",
        rag and rag["ring"] == "trial" and rag["transition_score"] == 36,
        f"ring={rag['ring'] if rag else None}, score={rag['transition_score'] if rag else None}"
    ))

    # 2. All scores match formula
    mismatches = [b["name"] for b in blips if gen.compute_score(b) != b.get("transition_score", -1)]
    results.append(chk("All transition_score values match formula", not mismatches, str(mismatches[:3])))

    # 3. RAG Pipeline is top-scored Trial item
    trial = sorted([b for b in blips if b["ring"] == "trial"], key=lambda b: b["transition_score"], reverse=True)
    results.append(chk("Top Trial blip = RAG Pipeline", bool(trial) and trial[0]["name"] == "RAG Pipeline"))

    # 4–7. Ring distribution
    by_ring = {r: len([b for b in blips if b["ring"] == r]) for r in ["trial", "adopt", "assess", "hold"]}
    results.append(chk(f"Trial ring blip count correct ({by_ring['trial']})", by_ring["trial"] >= 10))
    results.append(chk(f"Adopt ring = 13 ({by_ring['adopt']})", by_ring["adopt"] == 13, f"got {by_ring['adopt']}"))
    results.append(chk(f"Assess ring blip count correct ({by_ring['assess']})", by_ring["assess"] >= 10))
    results.append(chk(f"Hold ring = 17 ({by_ring['hold']})", by_ring["hold"] == 17, f"got {by_ring['hold']}"))

    # 8. Java in Hold (not Adopt or Trial)
    java = next((b for b in blips if b["name"] == "Java"), None)
    results.append(chk("Java is in Hold ring", java and java["ring"] == "hold",
                        f"ring={java['ring'] if java else None}"))

    # 9. MCP in Trial (strategic override)
    mcp = next((b for b in blips if "MCP" in b["name"]), None)
    results.append(chk("MCP in Trial ring (strategic override)", mcp and mcp["ring"] == "trial",
                        f"ring={mcp['ring'] if mcp else None}"))

    # 10. MLflow in Assess with category=enabler
    mlflow = next((b for b in blips if b["name"] == "MLflow"), None)
    results.append(chk("MLflow: ring=assess, category=enabler",
                        mlflow and mlflow["ring"] == "assess" and mlflow["category"] == "enabler",
                        f"ring={mlflow['ring'] if mlflow else None}, cat={mlflow['category'] if mlflow else None}"))

    # 11. No fabricated demand (Java/REST API/SQL = 0)
    demand_checks = {"Java": 0, "REST API Design": 0, "SQL": 0}
    for name, expected in demand_checks.items():
        b = next((x for x in blips if x["name"] == name), None)
        results.append(chk(f"{name} demand = {expected} (not fabricated)",
                            b and b.get("demand", -1) == expected,
                            f"got {b.get('demand') if b else 'not found'}"))

    # 12. Max score sanity check
    max_score = max(b.get("transition_score", 0) for b in blips)
    results.append(chk(f"Max score ≤ 50 (max={max_score})", max_score <= 50))

    # 13. All required fields present
    required = ["name", "quadrant", "ring", "category", "demand", "gap", "transition_score"]
    missing = [b["name"] for b in blips if not all(f in b for f in required)]
    results.append(chk("All blips have required fields", not missing, str(missing[:3])))

    # 14. index.html uses fetch() not inline data
    idx = (ROOT / "index.html").read_text()
    results.append(chk("index.html uses fetch('radar.json')", "fetch('radar.json')" in idx))

    # 15. LLM Integration Patterns in Trial
    lp = next((b for b in blips if "LLM Integration" in b["name"]), None)
    results.append(chk("LLM Integration Patterns in Trial ring",
                        lp and lp["ring"] == "trial",
                        f"ring={lp['ring'] if lp else None}"))

    passed = sum(results)
    total = len(results)
    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} tests passed")
    return passed == total


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
