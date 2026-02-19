#!/usr/bin/env python3
"""
generate-radar.py -- Transform skills-demand.md into a Transition Radar

This is NOT a ThoughtWorks org radar. This is a TRANSITION radar that answers:
"Where should Jurek spend his 15 hrs/week to land a €150k+ AI/ML role?"

Key concept: every skill gets a CATEGORY (ai_core/bridge/enabler/legacy/irrelevant)
and a TRANSITION SCORE that determines priority. The radar is opinionated --
it deliberately deprioritizes legacy engineering skills and highlights AI/ML gaps.

Usage:
    python generate-radar.py [path/to/skills-demand.md] [output/radar.json]
"""

import json
import re
import sys
from datetime import datetime, date
from collections import defaultdict
from pathlib import Path


# =============================================================================
# SKILL CATEGORIES -- The opinion layer
# =============================================================================
# Every skill must be classified. This is the most important configuration.
# ai_core: Pure AI/ML. Learning this IS the transition.
# bridge: Combines engineering + AI. Jurek's unique angle.
# enabler: Foundation that enables AI work. Worth marketing if you have it.
# legacy: Pure engineering. Doesn't differentiate from other Java devs.
# irrelevant: Wrong direction. Don't invest.

CATEGORY_MAP = {
    # --- ai_core (weight: 10) ---
    # Canonical names (post-normalization)
    "rag pipeline": "ai_core",
    "agentic ai systems": "ai_core",
    "llm apis (production)": "ai_core",
    "llm prompt engineering": "ai_core",
    "vector databases": "ai_core",
    "ai model evaluation / rlhf": "ai_core",
    "nlp (embeddings, ranking)": "ai_core",  # canonical name after normalization
    "mlops / ml infrastructure": "ai_core",
    "ml frameworks (pytorch/tensorflow)": "ai_core",
    "distributed ml systems": "ai_core",
    "llm inference infrastructure": "ai_core",
    "ai training data engineering": "ai_core",
    "data science / analytics": "ai_core",
    "search / ranking systems": "ai_core",
    "langchain / llamaindex": "ai_core",
    # Raw input variants (pre-normalization)
    "ai agent development": "ai_core",
    "ai prompt engineering": "ai_core",
    "vector databases (pinecone, weaviate)": "ai_core",
    "llm evaluation pipelines": "ai_core",
    "nlp (embeddings, ranking, classification)": "ai_core",
    "nlu / conversational ai": "ai_core",
    "llm inference infrastructure (vllm)": "ai_core",
    "ml model inference systems": "ai_core",
    "multi-modal models": "ai_core",

    # --- bridge (weight: 8) ---
    # Canonical names (post-normalization)
    "mcp (model context protocol)": "bridge",
    "llm integration": "bridge",
    "ai-assisted development": "bridge",  # canonical name after normalization
    "llm email drafting": "bridge",
    "chatbot integration": "bridge",
    "banking/payments domain": "bridge",  # bridge because banking+AI is the unique niche
    # Raw input variants (pre-normalization)
    "llm integration architecture": "bridge",
    "ai-assisted development (llm tools)": "bridge",
    "ai solution implementation": "bridge",
    "legacy system refactoring (ai)": "bridge",
    "credit risk modeling": "bridge",
    "finance data governance": "bridge",

    # --- enabler (weight: 4) ---
    "python": "enabler",
    "python (5+ yrs production)": "enabler",
    "fastapi": "enabler",
    "docker": "enabler",
    "docker/containers": "enabler",
    "kubernetes": "enabler",
    "kubernetes / docker / terraform": "enabler",
    "terraform": "enabler",
    "aws": "enabler",
    "aws (solutions architect cert)": "enabler",
    "azure": "enabler",
    "azure cloud": "enabler",
    "azure openai service": "enabler",
    "azure ai search": "enabler",
    "azure document intelligence": "enabler",
    "gcp": "enabler",
    "mlflow": "enabler",
    "mlflow / huggingface": "enabler",
    "databricks": "enabler",
    "make.com/n8n": "enabler",
    "n8n / zapier automation": "enabler",
    "huggingface": "enabler",
    "claude/openai api": "enabler",
    "aws bedrock": "enabler",

    # --- legacy (weight: 1) ---
    "java": "legacy",
    "spring/spring boot": "legacy",
    "javascript": "legacy",
    "typescript": "legacy",
    "sql/postgresql": "legacy",
    "microservices architecture": "legacy",
    "rest api design": "legacy",
    "ci/cd": "legacy",
    "devops": "legacy",
    "solution architecture": "legacy",
    "hld/lld docs": "legacy",
    "architecture diagrams / documentation": "legacy",
    "strangler fig / microservices migration": "legacy",
    "gitops (flux, github actions)": "legacy",

    # --- irrelevant (weight: 0) ---
    "c++": "irrelevant",
    "c/c++ (memory mgmt, build systems)": "irrelevant",
    "react / node.js": "irrelevant",
    "tcp/ip / ssl/tls / vpn": "irrelevant",
    "ehr / health data integration": "irrelevant",
    "hubspot api": "irrelevant",
    "xero / hubspot crm integration": "irrelevant",
    "google workspace api": "irrelevant",
    "ocr / document processing": "irrelevant",
    "kubeflow": "irrelevant",
    "dialogflow cx": "irrelevant",
    "ml platform components": "irrelevant",
    "airflow / etl orchestration": "irrelevant",
}


# =============================================================================
# QUADRANT CLASSIFICATION -- Category of technology (unchanged from v1)
# =============================================================================
QUADRANT_MAP = {
    # Languages & Frameworks
    "java": "Languages & Frameworks",
    "python": "Languages & Frameworks",
    "python (5+ yrs production)": "Languages & Frameworks",
    "typescript": "Languages & Frameworks",
    "javascript": "Languages & Frameworks",
    "c++": "Languages & Frameworks",
    "c/c++ (memory mgmt, build systems)": "Languages & Frameworks",
    "spring boot": "Languages & Frameworks",  # canonical name
    "spring/spring boot": "Languages & Frameworks",
    "fastapi": "Languages & Frameworks",
    "langchain / llamaindex": "Languages & Frameworks",
    "react / node.js": "Languages & Frameworks",
    "sql/postgresql": "Languages & Frameworks",
    "ml frameworks (pytorch/tensorflow)": "Languages & Frameworks",
    "multi-modal models": "Techniques",

    # Tools
    "docker/containers": "Tools",
    "docker": "Tools",
    "kubernetes": "Tools",
    "kubernetes / docker / terraform": "Tools",
    "terraform": "Tools",
    "mlflow": "Tools",
    "mlflow / huggingface": "Tools",
    "databricks": "Tools",
    "kubeflow": "Tools",
    "airflow / etl orchestration": "Tools",
    "make.com/n8n": "Tools",
    "n8n / zapier automation": "Tools",
    "hubspot api": "Tools",
    "dialogflow cx": "Tools",
    "vector databases": "Tools",
    "vector databases (pinecone, weaviate)": "Tools",
    "llm inference infrastructure": "Tools",
    "llm inference infrastructure (vllm)": "Tools",
    "gitops (flux, github actions)": "Tools",
    "ml model inference systems": "Tools",
    "xero / hubspot crm integration": "Tools",
    "google workspace api": "Tools",

    # Techniques
    "rag pipeline": "Techniques",
    "agentic ai systems": "Techniques",
    "ai agent development": "Techniques",
    "llm prompt engineering": "Techniques",
    "ai prompt engineering": "Techniques",
    "ai model evaluation / rlhf": "Techniques",
    "llm evaluation pipelines": "Techniques",
    "llm integration": "Techniques",
    "llm integration architecture": "Techniques",
    "llm email drafting": "Techniques",
    "mcp (model context protocol)": "Techniques",
    "microservices architecture": "Techniques",
    "rest api design": "Techniques",
    "ci/cd": "Techniques",
    "devops": "Techniques",
    "mlops / ml infrastructure": "Techniques",
    "nlp (embeddings, ranking, classification)": "Techniques",
    "nlu / conversational ai": "Techniques",
    "chatbot integration": "Techniques",
    "ai-assisted development (llm tools)": "Techniques",
    "ai solution implementation": "Techniques",
    "ai training data engineering": "Techniques",
    "banking/payments domain": "Techniques",
    "credit risk modeling": "Techniques",
    "finance data governance": "Techniques",
    "solution architecture": "Techniques",  # canonical name
    "hld/lld docs": "Techniques",
    "architecture diagrams / documentation": "Techniques",
    "legacy system refactoring (ai)": "Techniques",
    "strangler fig / microservices migration": "Techniques",
    "distributed ml systems": "Techniques",
    "ml platform components": "Techniques",
    "ocr / document processing": "Techniques",
    "tcp/ip / ssl/tls / vpn": "Techniques",
    "ehr / health data integration": "Techniques",
    "data science / analytics": "Techniques",
    "search / ranking systems": "Techniques",

    # Platforms
    "aws": "Platforms",
    "aws (solutions architect cert)": "Platforms",
    "azure": "Platforms",
    "azure cloud": "Platforms",
    "azure openai service": "Platforms",
    "azure ai search": "Platforms",
    "azure document intelligence": "Platforms",
    "gcp": "Platforms",
    "claude/openai api": "Platforms",
    "llm apis (production)": "Platforms",
    "llm apis (claude, openai)": "Platforms",
    "aws bedrock": "Platforms",
    "huggingface": "Platforms",
}


# =============================================================================
# SKILL NORMALIZATION -- Map variants to canonical names
# =============================================================================
NORMALIZE = {
    "python (5+ yrs production)": "Python",
    "spring/spring boot": "Spring Boot",
    "aws (solutions architect cert)": "AWS",
    "docker/containers": "Docker",
    "kubernetes / docker / terraform": "Kubernetes",
    "vector databases (pinecone, weaviate)": "Vector databases",
    "llm inference infrastructure (vllm)": "LLM inference infrastructure",
    "n8n / zapier automation": "Make.com/n8n",
    "mlflow / huggingface": "MLflow",
    "claude/openai api": "LLM APIs (production)",
    "llm apis (claude, openai)": "LLM APIs (production)",
    "llm apis (production)": "LLM APIs (production)",
    "ai prompt engineering": "LLM Prompt Engineering",
    "llm integration architecture": "LLM integration",
    "llm evaluation pipelines": "AI model evaluation / RLHF",
    "azure cloud": "Azure",
    "azure openai service": "Azure",
    "azure ai search": "Azure",
    "azure document intelligence": "Azure",
    "sql/postgresql": "SQL/PostgreSQL",
    "c/c++ (memory mgmt, build systems)": "C++",
    "gitops (flux, github actions)": "CI/CD",
    "ai agent development": "Agentic AI systems",
    "ai solution implementation": "AI-assisted development",
    "ai-assisted development (llm tools)": "AI-assisted development",
    "legacy system refactoring (ai)": "AI-assisted development",
    "nlp (embeddings, ranking, classification)": "NLP (embeddings, ranking)",
    "nlu / conversational ai": "NLP (embeddings, ranking)",
    "hld/lld docs": "Solution Architecture",
    "architecture diagrams / documentation": "Solution Architecture",
    "strangler fig / microservices migration": "Microservices architecture",
    "xero / hubspot crm integration": "HubSpot API",
    "ml model inference systems": "LLM inference infrastructure",
    "credit risk modeling": "Banking/payments domain",
    "finance data governance": "Banking/payments domain",
}


# =============================================================================
# MANUAL OVERRIDES -- Strategic bets that override the algorithm
# =============================================================================
RING_OVERRIDES = {
    # Strategic Trial: demand is low but strategic importance is high
    "MCP (Model Context Protocol)": "Trial",  # Anthropic standard, early-mover advantage
}


# =============================================================================
# TRANSITION SCORE -- The core innovation
# =============================================================================
CATEGORY_WEIGHT = {
    "ai_core": 10,
    "bridge": 8,
    "enabler": 4,
    "legacy": 1,
    "irrelevant": 0,
}

GAP_BONUS = {
    "LEARNING": 5,   # Actively closing gap = highest ROI
    "NO": 2,         # Could learn but haven't started
    "YES": 0,        # No gap to close
}


def calc_transition_score(category, demand_count, you_have_it):
    """Calculate how important this skill is for the career transition."""
    return CATEGORY_WEIGHT[category] + (demand_count * 3) + GAP_BONUS.get(you_have_it, 0)


# =============================================================================
# RING PLACEMENT -- Transition-aware algorithm
# =============================================================================
def assign_ring(category, you_have_it, demand_count):
    """Assign ring based on transition relevance, not just possession."""

    # Rule 1: Irrelevant skills always Hold
    if category == "irrelevant":
        return "Hold"

    # Rule 2: Legacy skills with 0 demand = Hold (no transition value)
    if category == "legacy" and demand_count == 0:
        return "Hold"

    # Rule 3: TRIAL -- AI-core or bridge skills you need to learn, with demand
    if category in ("ai_core", "bridge") and you_have_it != "YES" and demand_count >= 2:
        return "Trial"

    # Rule 4: ADOPT -- skills you have that matter for AI/ML applications
    if you_have_it == "YES" and category in ("ai_core", "bridge", "enabler") and demand_count >= 1:
        return "Adopt"

    # Rule 5: Legacy with demand -- still Adopt (Java modernization roles exist)
    if you_have_it == "YES" and category == "legacy" and demand_count >= 1:
        return "Adopt"

    # Rule 6: ASSESS -- some AI signal but not enough to invest yet
    if category in ("ai_core", "bridge") and demand_count >= 1:
        return "Assess"
    if category == "enabler" and you_have_it != "YES" and demand_count >= 1:
        return "Assess"

    # Rule 7: Enabler you have but 0 demand = Hold (don't clutter the radar)
    if category == "enabler" and demand_count == 0:
        return "Hold"

    # Rule 8: Everything else = Hold
    return "Hold"


# =============================================================================
# PARSING -- Same as v1, works correctly
# =============================================================================
def normalize_skill(name):
    """Normalize skill name to canonical form."""
    lower = name.strip().lower()
    for key, val in NORMALIZE.items():
        if lower == key.lower():
            return val
    return name.strip()


def get_quadrant(skill_name):
    """Get quadrant for a skill. Default to Techniques if unknown."""
    lower = skill_name.strip().lower()
    if lower in QUADRANT_MAP:
        return QUADRANT_MAP[lower]
    normalized = normalize_skill(skill_name).lower()
    if normalized in QUADRANT_MAP:
        return QUADRANT_MAP[normalized]
    return "Techniques"


def get_category(skill_name):
    """Get transition category for a skill. Default to legacy if unknown."""
    lower = skill_name.strip().lower()
    if lower in CATEGORY_MAP:
        return CATEGORY_MAP[lower]
    # Check normalized name
    normalized = normalize_skill(skill_name).lower()
    if normalized in CATEGORY_MAP:
        return CATEGORY_MAP[normalized]
    # Unknown skills default to legacy (conservative -- won't pollute Trial)
    return "legacy"


def parse_demand_log(content):
    """Parse the Demand Log table from skills-demand.md."""
    entries = []
    in_demand_log = False

    for line in content.split("\n"):
        if "## Demand Log" in line:
            in_demand_log = True
            continue
        if in_demand_log and line.startswith("## "):
            break
        if not in_demand_log:
            continue
        if not line.startswith("|") or "Date" in line or "---" in line:
            continue

        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 6:
            entries.append({
                "date": parts[0],
                "skill": parts[1],
                "job_title": parts[2],
                "platform": parts[3],
                "score": int(parts[4]) if parts[4].isdigit() else 0,
                "you_have_it": parts[5],
            })

    return entries


def parse_baseline_skills(content):
    """Parse the Current Skills You Have table."""
    skills = []
    in_baseline = False

    for line in content.split("\n"):
        if "## Current Skills You Have" in line:
            in_baseline = True
            continue
        if in_baseline and line.startswith("## "):
            break
        if not in_baseline:
            continue
        if not line.startswith("|") or "Skill" in line or "---" in line:
            continue

        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 3:
            skills.append({
                "skill": parts[0],
                "level": parts[1],
                "years": parts[2],
            })

    return skills


# =============================================================================
# BUILD RADAR
# =============================================================================
def build_radar(content):
    """Build transition radar blips from skills-demand.md content."""
    demand_entries = parse_demand_log(content)
    baseline_skills = parse_baseline_skills(content)
    today = date.today().isoformat()

    # Aggregate demand by normalized skill name
    skill_data = defaultdict(lambda: {
        "demand_count": 0,
        "you_have_it": "NO",
        "first_seen": None,
        "last_seen": None,
        "job_examples": [],
        "platforms": set(),
    })

    for entry in demand_entries:
        canonical = normalize_skill(entry["skill"])
        sd = skill_data[canonical]
        sd["demand_count"] += 1

        # Upgrade status: NO -> LEARNING -> YES (never downgrade)
        priority = {"NO": 0, "LEARNING": 1, "YES": 2}
        if priority.get(entry["you_have_it"], 0) > priority.get(sd["you_have_it"], 0):
            sd["you_have_it"] = entry["you_have_it"]

        if sd["first_seen"] is None or entry["date"] < sd["first_seen"]:
            sd["first_seen"] = entry["date"]
        if sd["last_seen"] is None or entry["date"] > sd["last_seen"]:
            sd["last_seen"] = entry["date"]

        job_short = entry["job_title"].split("(")[0].strip()[:40]
        if job_short not in sd["job_examples"] and len(sd["job_examples"]) < 5:
            sd["job_examples"].append(job_short)
        sd["platforms"].add(entry["platform"])

    # Add baseline skills
    for bs in baseline_skills:
        canonical = normalize_skill(bs["skill"])
        if canonical not in skill_data:
            skill_data[canonical] = {
                "demand_count": 0,
                "you_have_it": "YES",
                "first_seen": "2026-02-01",
                "last_seen": today,
                "job_examples": [],
                "platforms": set(),
            }
        else:
            skill_data[canonical]["you_have_it"] = "YES"

    # Build blips with transition scoring
    blips = []
    for name, sd in skill_data.items():
        category = get_category(name)
        score = calc_transition_score(category, sd["demand_count"], sd["you_have_it"])

        # Ring: apply overrides first, then algorithm
        ring = RING_OVERRIDES.get(name, assign_ring(category, sd["you_have_it"], sd["demand_count"]))

        quadrant = get_quadrant(name)
        movement = "new"  # All "new" on first generation

        # Build rationale
        parts = []
        if sd["demand_count"] > 0:
            parts.append(f"{sd['demand_count']} job appearance{'s' if sd['demand_count'] != 1 else ''}")
        if sd["you_have_it"] == "YES":
            parts.append("you have this skill")
        elif sd["you_have_it"] == "LEARNING":
            parts.append("actively learning")
        if sd["platforms"]:
            parts.append(f"seen on {', '.join(sorted(sd['platforms']))}")
        rationale = ". ".join(parts) + "." if parts else "Baseline skill."

        blips.append({
            "name": name,
            "quadrant": quadrant,
            "ring": ring,
            "category": category,
            "transition_score": score,
            "movement": movement,
            "demand_count": sd["demand_count"],
            "you_have_it": sd["you_have_it"],
            "rationale": rationale,
            "first_seen": sd["first_seen"] or today,
            "last_seen": sd["last_seen"] or today,
            "job_examples": sd["job_examples"],
            "portfolio_link": None,
            "updated": today,
        })

    # Sort by transition_score DESC (the most important skill comes first)
    blips.sort(key=lambda b: (-b["transition_score"], b["name"]))

    return blips


# =============================================================================
# SUMMARY OUTPUT
# =============================================================================
def print_summary(blips):
    """Print transition radar summary to stdout."""
    by_ring = defaultdict(list)
    for b in blips:
        by_ring[b["ring"]].append(b)

    print(f"\n{'='*70}")
    print(f"  TRANSITION RADAR -- {date.today().isoformat()}")
    print(f"  {len(blips)} skills | Answering: 'Where should my 15 hrs/week go?'")
    print(f"{'='*70}")

    # Focus Board -- top 5 by transition score from Trial ring
    trial_items = sorted(by_ring.get("Trial", []), key=lambda b: -b["transition_score"])
    if trial_items:
        print(f"\n  {'='*50}")
        print(f"  FOCUS BOARD -- Your transition priorities")
        print(f"  {'='*50}")
        for i, b in enumerate(trial_items[:5], 1):
            bar_len = int(b["transition_score"] / 2)
            bar = "█" * bar_len
            status = b["you_have_it"]
            print(f"  {i}. {b['name']:30s} {bar:20s} {b['transition_score']:3d}  ({b['demand_count']} jobs, {status})")
        print()

    # Ring-by-ring (Trial first!)
    for ring in ["Trial", "Adopt", "Assess", "Hold"]:
        items = sorted(by_ring.get(ring, []), key=lambda b: -b["transition_score"])
        print(f"  [{ring.upper()}] ({len(items)} skills)")
        for b in items:
            cat_short = b["category"][:7]
            score_str = f"score:{b['transition_score']:2d}"
            demand_str = f"demand:{b['demand_count']}" if b['demand_count'] > 0 else "baseline"
            status = b["you_have_it"]
            print(f"    {b['name']:40s} [{cat_short:7s}] {score_str}  {demand_str:12s} {status}")
        print()

    # Distribution
    by_cat = defaultdict(int)
    for b in blips:
        by_cat[b["category"]] += 1
    print(f"  Categories: {dict(by_cat)}")
    print(f"  Rings: { {r: len(v) for r, v in by_ring.items()} }")
    print()


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    # Paths
    default_input = Path(__file__).parent.parent.parent / "job-search" / "skills-demand.md"
    default_output = Path(__file__).parent.parent / "radar.json"

    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_input
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else default_output

    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    content = input_path.read_text()
    blips = build_radar(content)

    # Write JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(blips, indent=2))
    print(f"Wrote {len(blips)} blips to {output_path}")

    # Print summary
    print_summary(blips)

    # History snapshot
    history_dir = output_path.parent / "history"
    history_dir.mkdir(exist_ok=True)
    snapshot = history_dir / f"{date.today().isoformat()}.json"
    snapshot.write_text(json.dumps(blips, indent=2))
    print(f"History snapshot: {snapshot}")

    # Embed data into index.html
    index_path = output_path.parent / "index.html"
    if index_path.exists():
        html = index_path.read_text()
        new_data = f"let RADAR_DATA = {json.dumps(blips)};"
        html = re.sub(r'let RADAR_DATA = \[.*?\];', new_data, html, flags=re.DOTALL)
        index_path.write_text(html)
        print(f"Embedded {len(blips)} blips into {index_path}")
