# AI/ML Transition Radar

A data-driven, interactive technology radar that answers one question:

> **"Where should I spend my 15 hours/week to land a €150k+ AI/ML engineering role?"**

**[→ View the live radar](https://kevin-bot-openclaw-ops.github.io/tech-radar/)**

This is not a ThoughtWorks-style organizational radar. It is a _transition radar_ — opinionated, personal, and built from real job market signal rather than team consensus.

---

## Why This Exists

Most career transition advice is vague: "learn Python," "get into AI." This project replaces that with a systematic, evidence-based answer derived from scanning actual job postings, extracting skill requirements, scoring demand frequency, and rendering the results as an interactive radar.

Every blip on the radar has a `transition_score` that combines:
- **Market demand** (how often the skill appears in real job ads)
- **Category weight** (how close this skill is to the AI/ML core vs. legacy engineering)
- **Gap bonus** (skills you need to close the gap score higher than skills you already have)

The result: a prioritized, continuously updated view of what to learn next.

---

## Live Demo

**→ [kevin-bot-openclaw-ops.github.io/tech-radar](https://kevin-bot-openclaw-ops.github.io/tech-radar/)**

Features:
- Filter by quadrant: Languages & Frameworks | Platforms | Techniques | Tools
- Hover any blip for demand count, transition score, and example job titles
- Ring legend explains priority tier (Trial > Adopt > Assess > Hold)

---

## How It Works

```
Job postings (Brave Search, LinkedIn, Indeed)
        │
        ▼
skills-demand.md  ←── Manual scan log (skill, job title, platform, you_have_it)
        │
        ▼
generate-radar.py ──► Normalize → Categorize → Score → Assign ring → radar.json
        │
        ▼
index.html (D3.js) ──► Renders radar.json as interactive SVG
        │
        ▼
GitHub Pages (auto-deploy on push)
```

### Step 1: Demand Logging (`skills-demand.md`)

Skills are logged manually after each job scan. Each row in the Demand Log table contains:

| Field | Description |
|-------|-------------|
| `date` | Scan date (YYYY-MM-DD) |
| `skill` | Raw skill name from job ad |
| `job_title` | Role title seen in |
| `platform` | Where found (LinkedIn, Indeed, etc.) |
| `score` | Relevance weight of this instance |
| `you_have_it` | `YES` / `NO` / `LEARNING` |

### Step 2: Pipeline (`generate-radar.py`)

The script runs a 5-stage pipeline:

**2a. Normalize** — maps 60+ raw skill variants to canonical names (e.g., `"ai agent development"` → `"Agentic AI systems"`, `"llm integration architecture"` → `"LLM integration"`).

**2b. Categorize** — assigns each skill a transition category:

| Category | Weight | Meaning |
|----------|--------|---------|
| `ai_core` | 10 | Pure AI/ML: RAG, agentic systems, vector DBs, LLM APIs |
| `bridge` | 8 | Enterprise AI: LLM integration, banking domain + AI, MCP |
| `enabler` | 4 | Foundation: Python, Docker, AWS, FastAPI |
| `legacy` | 1 | Pure engineering: Java, SQL, REST APIs, CI/CD |
| `irrelevant` | 0 | Wrong direction: C++, React, EHR integration |

**2c. Score** — computes `transition_score` for each skill:

```python
transition_score = CATEGORY_WEIGHT[category] + (demand_count × 3) + GAP_BONUS[you_have_it]

# Gap bonus:
# LEARNING = +5  (actively closing gap = highest ROI)
# NO       = +2  (could learn but haven't started)
# YES      = +0  (already have it — no gap to close)
```

**2d. Assign ring** — places skills into radar rings based on category + demand + gap:

| Ring | Rule |
|------|------|
| **Trial** | AI-core or bridge skill, not yet learned, demand ≥ 2 |
| **Adopt** | Have the skill AND it matters for AI/ML, demand ≥ 1 |
| **Assess** | Some AI signal but not enough demand to invest yet |
| **Hold** | Legacy/irrelevant skills, or enablers with zero demand |

Manual overrides exist for strategic bets (e.g., MCP forced to Trial despite demand=1 because it's an early-mover opportunity in agentic tooling).

**2e. Output** — writes `radar.json` (array of blip objects with all metadata) and a history snapshot in `history/YYYY-MM-DD.json`.

### Step 3: Visualization (`index.html`)

D3.js reads `radar.json` at runtime via `fetch()`. No hardcoded data in HTML. The radar SVG positions blips in the correct ring/quadrant sector. Hover tooltips show demand count, transition score, and example job titles from the scan log.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data pipeline | Python 3.10+ |
| NLP (normalization) | Custom rule-based (no model dependency) |
| Demand scanning | Brave Search API + manual review |
| Radar format | JSON (custom schema) |
| Visualization | D3.js v7 |
| Hosting | GitHub Pages |
| Deployment | Git push (auto-deploy via Pages) |
| History | Daily JSON snapshots in `history/` |

---

## Scoring Formula (Worked Example)

**RAG Pipeline** (ring: Trial)
- Category: `ai_core` → weight 10
- Demand count: 8 job appearances → +24
- You have it: `LEARNING` → +5
- **Transition score: 39** — top priority

**Java** (ring: Hold)
- Category: `legacy` → weight 1
- Demand count: 0 (no AI/ML jobs require Java alone) → +0
- You have it: `YES` → +0
- **Transition score: 1** — deprioritized

---

## Repository Structure

```
tech-radar/
├── README.md                  # This file
├── radar.json                 # Generated — source of truth for visualization
├── index.html                 # D3.js radar (fetches radar.json at runtime)
├── descriptions.json          # Rich descriptions overlay (display layer only)
├── skills-demand.md           # Demand log + baseline skills (DO NOT edit radar.json manually)
├── scripts/
│   ├── generate-radar.py      # Pipeline: skills-demand.md → radar.json
│   └── test_radar.py          # 17 tests validating pipeline correctness
└── history/
    └── YYYY-MM-DD.json        # Daily radar snapshots for tracking movement
```

---

## Running Locally

```bash
# Clone
git clone https://github.com/kevin-bot-openclaw-ops/tech-radar.git
cd tech-radar

# Install dependencies (stdlib only, no pip required)
python3 --version  # 3.8+ required

# Generate radar from demand log
python3 scripts/generate-radar.py skills-demand.md radar.json

# Run tests
python3 -m pytest scripts/test_radar.py -v
# Expected: 17 passed

# Serve locally
python3 -m http.server 8080
# Open: http://localhost:8080
```

To update the radar with new job scan data:
1. Add rows to the `## Demand Log` table in `skills-demand.md`
2. Run `python3 scripts/generate-radar.py`
3. `git commit -am "feat: radar sync YYYY-MM-DD" && git push`

GitHub Pages auto-deploys on push. Changes live within ~60 seconds.

---

## Interview Talking Points

This project demonstrates several production engineering patterns:

1. **Data pipeline design** — raw job ad text → structured demand signal → scored radar JSON → visualization. Each stage is independently testable.

2. **Domain-specific NLP** — 60+ skill name normalization rules built without ML models. Explains why rule-based NLP is often the right choice for known-vocabulary problems.

3. **Opinionated data modeling** — `transition_score` is a composite score that makes a specific claim about career priorities. Justifiable, inspectable, and overrideable (see `RING_OVERRIDES`).

4. **Separation of concerns** — `radar.json` is the source of truth. `descriptions.json` adds display-layer content without polluting the data layer. `index.html` is a pure renderer. Classic data/view separation.

5. **Evidence-based decision making** — every skill placement has a traceable rationale: demand count + category + gap status. No gut-feel decisions hidden in the data.

---

## Current Snapshot (2026-02-19)

- **55 technologies** tracked
- **Adopt:** 18 (skills you have that matter for AI/ML)
- **Trial:** 6 (your next learning investments)
- **Assess:** 19 (monitoring, not investing yet)
- **Hold:** 12 (deprioritized — legacy or irrelevant)

Top Trial priorities (by transition score):
1. RAG Pipeline — 8 job appearances, actively learning
2. Agentic AI Systems — 6 appearances, gap to close
3. LLM APIs (production) — 7 appearances, learning
4. Vector Databases — 5 appearances, gap
5. MLOps / ML Infrastructure — 4 appearances, learning

---

## Related Portfolio Projects

| Project | What it demonstrates | Link |
|---------|---------------------|------|
| ml-portfolio | RAG pipeline implementation (the #1 Trial skill in action) | [repo](https://github.com/kevin-bot-openclaw-ops/ml-portfolio) |
| banking-fraud-ml | ML in production — imbalanced data, XGBoost, AUPRC evaluation | [repo](https://github.com/kevin-bot-openclaw-ops/banking-fraud-ml) |
| financial-sentiment-nlp | FinBERT, entity extraction, FastAPI serving | [repo](https://github.com/kevin-bot-openclaw-ops/financial-sentiment-nlp) |
| mlops-pipeline | MLflow tracking, model registry, drift monitoring, CI/CD | [repo](https://github.com/kevin-bot-openclaw-ops/mlops-pipeline) |
