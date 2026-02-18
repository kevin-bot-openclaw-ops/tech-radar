#!/usr/bin/env python3
"""
generate-radar.py v2 — Transition-focused radar generator.

Reads radar.json, outputs self-contained index.html.
Formula: CATEGORY_WEIGHT + (demand * 3) + GAP_BONUS

Usage:
    python3 scripts/generate-radar.py
"""

import json
import sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).parent.parent
RADAR_JSON = ROOT / "radar.json"
INDEX_HTML = ROOT / "index.html"
HISTORY_DIR = ROOT / "history"

CATEGORY_WEIGHTS = {"ai_core": 10, "bridge": 8, "enabler": 4, "legacy": 1, "irrelevant": 0}
GAP_BONUS = {"LEARNING": 5, "NO": 2, "YES": 0}
RING_ORDER = ["trial", "adopt", "assess", "hold"]
RING_LABELS = {
    "trial": "INVEST HERE",
    "adopt": "MARKET THIS",
    "assess": "WATCH",
    "hold": "IGNORE"
}
CATEGORY_COLORS = {
    "ai_core": "#58a6ff",      # blue
    "bridge": "#bc8cff",       # purple
    "enabler": "#3fb950",      # green
    "legacy": "#f0883e",       # orange
    "irrelevant": "#6e7681"    # gray
}


def compute_score(blip: dict) -> int:
    """Compute transition score: CATEGORY_WEIGHT + (demand * 3) + GAP_BONUS"""
    cat_weight = CATEGORY_WEIGHTS.get(blip.get("category", "irrelevant"), 0)
    demand_score = blip.get("demand", 0) * 3
    gap = GAP_BONUS.get(blip.get("gap", "YES"), 0)
    return cat_weight + demand_score + gap


def load_and_validate(path: Path) -> dict:
    with open(path) as f:
        data = json.load(f)

    # Validate and recompute scores
    for blip in data["blips"]:
        computed = compute_score(blip)
        stored = blip.get("transition_score", 0)
        if computed != stored:
            print(f"  SCORE MISMATCH: {blip['name']} stored={stored} computed={computed} — updating")
            blip["transition_score"] = computed

    return data


def save_history(radar: dict):
    HISTORY_DIR.mkdir(exist_ok=True)
    snapshot_date = radar.get("date", str(date.today()))
    path = HISTORY_DIR / f"{snapshot_date}.json"
    with open(path, "w") as f:
        json.dump(radar, f, indent=2)
    print(f"  Snapshot → {path}")


def focus_board_html(blips: list) -> str:
    """Top 5 Trial items by transition score."""
    trial_blips = [b for b in blips if b["ring"] == "trial"]
    top5 = sorted(trial_blips, key=lambda b: b["transition_score"], reverse=True)[:5]
    max_score = top5[0]["transition_score"] if top5 else 1

    items = ""
    for i, b in enumerate(top5, 1):
        pct = int((b["transition_score"] / max_score) * 100)
        cat_color = CATEGORY_COLORS.get(b.get("category", "irrelevant"), "#6e7681")
        gap_badge = f'<span class="gap-badge gap-{b.get("gap","YES").lower()}">{b.get("gap","YES")}</span>'
        items += f"""
        <div class="focus-item">
          <div class="focus-rank">#{i}</div>
          <div class="focus-body">
            <div class="focus-name">
              <span style="color:{cat_color}">●</span> {b['name']} {gap_badge}
            </div>
            <div class="focus-bar-wrap">
              <div class="focus-bar" style="width:{pct}%"></div>
              <span class="focus-score">{b['transition_score']}</span>
            </div>
            <div class="focus-meta">{b.get('demand',0)} job signal{'s' if b.get('demand',0)!=1 else ''} · {b.get('description','')[:80]}...</div>
          </div>
        </div>"""
    return items


def generate_html(radar: dict) -> str:
    blips = radar["blips"]
    radar_json = json.dumps(radar, indent=2)

    # Stats
    by_ring = {r: [b for b in blips if b["ring"] == r] for r in RING_ORDER}

    focus_items = focus_board_html(blips)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Transition Radar — Jerzy Plocha</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0d1117;color:#e6edf3;min-height:100vh}}
a{{color:#58a6ff;text-decoration:none}}

/* Header */
header{{padding:20px 28px;border-bottom:1px solid #21262d;display:flex;justify-content:space-between;align-items:center}}
.header-title{{font-size:18px;font-weight:700}}
.header-sub{{font-size:12px;color:#8b949e;margin-top:3px}}
.header-meta{{font-size:12px;color:#8b949e;text-align:right}}

/* Focus Board */
.focus-board{{margin:20px 28px;background:#161b22;border:1px solid #21262d;border-radius:8px;overflow:hidden}}
.focus-board-header{{padding:12px 16px;background:#1c2128;border-bottom:1px solid #21262d;font-size:13px;font-weight:600;color:#58a6ff;letter-spacing:0.04em}}
.focus-item{{display:flex;gap:12px;padding:12px 16px;border-bottom:1px solid #21262d}}
.focus-item:last-child{{border-bottom:none}}
.focus-rank{{font-size:16px;font-weight:700;color:#484f58;width:24px;flex-shrink:0;padding-top:1px}}
.focus-body{{flex:1;min-width:0}}
.focus-name{{font-size:13px;font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:6px}}
.focus-bar-wrap{{display:flex;align-items:center;gap:8px;margin-bottom:4px}}
.focus-bar{{height:6px;background:#58a6ff;border-radius:3px;transition:width 0.3s}}
.focus-score{{font-size:12px;font-weight:700;color:#58a6ff;min-width:28px}}
.focus-meta{{font-size:11px;color:#8b949e;line-height:1.4}}

/* Gap badges */
.gap-badge{{font-size:10px;padding:1px 6px;border-radius:10px;font-weight:600}}
.gap-learning{{background:rgba(88,166,255,0.15);color:#58a6ff;border:1px solid rgba(88,166,255,0.3)}}
.gap-no{{background:rgba(248,81,73,0.1);color:#f85149;border:1px solid rgba(248,81,73,0.3)}}
.gap-yes{{background:rgba(63,185,80,0.1);color:#3fb950;border:1px solid rgba(63,185,80,0.3)}}

/* Filters */
.filters{{padding:12px 28px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid #21262d}}
.filter-btn{{padding:5px 12px;border-radius:20px;border:1px solid #30363d;background:#161b22;color:#8b949e;cursor:pointer;font-size:12px;transition:all 0.15s}}
.filter-btn:hover,.filter-btn.active{{border-color:#58a6ff;color:#58a6ff;background:rgba(88,166,255,0.1)}}

/* Category legend */
.legend{{padding:8px 28px;display:flex;gap:16px;border-bottom:1px solid #21262d;font-size:11px;color:#8b949e}}
.legend-item{{display:flex;align-items:center;gap:4px}}

/* Radar grid */
.radar-grid{{padding:20px 28px;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}

/* Ring sections */
.ring-section{{background:#161b22;border:1px solid #21262d;border-radius:8px;overflow:hidden}}
.ring-header{{padding:12px 14px;border-bottom:1px solid #21262d;display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none}}
.ring-name{{font-size:13px;font-weight:700;letter-spacing:0.05em}}
.ring-meaning{{font-size:11px;color:#8b949e}}
.ring-count{{font-size:11px;color:#8b949e;background:#21262d;padding:2px 8px;border-radius:10px}}

/* Blips */
.blip{{padding:9px 14px;border-bottom:1px solid #1c2128;cursor:pointer;transition:background 0.1s}}
.blip:last-child{{border-bottom:none}}
.blip:hover{{background:#1c2128}}
.blip-row{{display:flex;align-items:center;gap:8px}}
.blip-indicator{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.blip-indicator.new{{border-radius:0;width:0;height:0;background:transparent !important;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:10px solid currentColor}}
.blip-name{{font-size:13px;font-weight:500;flex:1}}
.blip-score{{font-size:11px;font-weight:700;color:#8b949e}}
.blip-signals{{font-size:10px;color:#6e7681;margin-left:18px;margin-top:2px}}
.blip-desc{{display:none;font-size:12px;color:#8b949e;margin-top:6px;margin-left:18px;line-height:1.5;padding-bottom:2px}}
.blip.open .blip-desc{{display:block}}
.blip-jobs{{font-size:11px;color:#3fb950;margin-top:4px}}

/* Hold section collapsed */
.hold-body{{display:none}}
.hold-body.visible{{display:block}}
.expand-hint{{font-size:11px;color:#6e7681;padding:8px 14px;text-align:center;cursor:pointer}}
.expand-hint:hover{{color:#8b949e}}

/* Stats bar */
.stats{{padding:12px 28px;border-top:1px solid #21262d;display:flex;gap:20px;font-size:12px;color:#8b949e}}
.stat-val{{font-weight:700;color:#e6edf3}}
</style>
</head>
<body>

<header>
  <div>
    <div class="header-title">⚡ Transition Radar v2</div>
    <div class="header-sub">Where should 15 hrs/week go to land a senior AI/ML role?</div>
  </div>
  <div class="header-meta">
    {radar.get('date','2026-02-18')} · {len(blips)} technologies<br>
    <span style="color:#6e7681">Jerzy Plocha · AI/ML Engineering</span>
  </div>
</header>

<div class="focus-board">
  <div class="focus-board-header">🎯 FOCUS BOARD — Top 5 Investment Priorities (Trial ring)</div>
  {focus_items}
</div>

<div class="filters">
  <span style="font-size:12px;color:#8b949e;margin-right:4px">Quadrant:</span>
  <button class="filter-btn active" data-q="all">All</button>
  <button class="filter-btn" data-q="techniques">Techniques</button>
  <button class="filter-btn" data-q="platforms">Platforms</button>
  <button class="filter-btn" data-q="languages-frameworks">Languages</button>
</div>

<div class="legend">
  <span style="color:#6e7681;margin-right:4px">Category:</span>
  <div class="legend-item"><span style="color:#58a6ff">●</span> AI Core</div>
  <div class="legend-item"><span style="color:#bc8cff">●</span> Bridge</div>
  <div class="legend-item"><span style="color:#3fb950">●</span> Enabler</div>
  <div class="legend-item"><span style="color:#f0883e">●</span> Legacy</div>
  <div class="legend-item"><span style="color:#6e7681">●</span> Irrelevant</div>
  <span style="color:#6e7681;margin-left:12px">▲ = new this scan</span>
</div>

<div class="radar-grid" id="radar-grid"></div>

<div class="stats" id="stats"></div>

<script>
const RADAR = {radar_json};
const RING_COLORS = {{trial:'#58a6ff',adopt:'#3fb950',assess:'#f0ad4e',hold:'#6e7681'}};
const RING_LABELS = {{trial:'INVEST HERE',adopt:'MARKET THIS',assess:'WATCH',hold:'IGNORE'}};
const CAT_COLORS = {{ai_core:'#58a6ff',bridge:'#bc8cff',enabler:'#3fb950',legacy:'#f0883e',irrelevant:'#6e7681'}};
const RINGS = ['trial','adopt','assess','hold'];

let activeQ = 'all';

function renderGrid() {{
  const grid = document.getElementById('radar-grid');
  grid.innerHTML = '';

  RINGS.forEach(ring => {{
    let blips = RADAR.blips.filter(b => b.ring === ring);
    if (activeQ !== 'all') blips = blips.filter(b => b.quadrant === activeQ);
    if (!blips.length) return;

    blips.sort((a,b) => b.transition_score - a.transition_score);

    const sec = document.createElement('div');
    sec.className = 'ring-section';

    const rColor = RING_COLORS[ring];
    sec.innerHTML = `<div class="ring-header" data-ring="${{ring}}">
      <div>
        <span class="ring-name" style="color:${{rColor}}">${{ring.toUpperCase()}}</span>
        <span class="ring-meaning" style="margin-left:8px">— ${{RING_LABELS[ring]}}</span>
      </div>
      <span class="ring-count">${{blips.length}}</span>
    </div>`;

    const body = document.createElement('div');
    body.className = ring === 'hold' ? 'hold-body' : 'ring-body';

    blips.forEach(blip => {{
      const catColor = CAT_COLORS[blip.category] || '#6e7681';
      const indClass = blip.isNew ? 'blip-indicator new' : 'blip-indicator';
      const indStyle = blip.isNew ? `color:${{catColor}}` : `background:${{catColor}}`;
      const gapCls = `gap-badge gap-${{(blip.gap||'YES').toLowerCase()}}`;
      const jobs = blip.job_examples?.length
        ? `<div class="blip-jobs">Seen in: ${{blip.job_examples.slice(0,2).join(', ')}}</div>` : '';

      const el = document.createElement('div');
      el.className = 'blip';
      el.innerHTML = `
        <div class="blip-row">
          <div class="${{indClass}}" style="${{indStyle}}"></div>
          <span class="blip-name">${{blip.name}}</span>
          ${{blip.isNew ? '<span style="font-size:10px;color:#58a6ff">NEW</span>' : ''}}
          <span class="blip-score">${{blip.transition_score}}</span>
          <span class="${{gapCls}}">${{blip.gap||'YES'}}</span>
        </div>
        ${{blip.demand ? `<div class="blip-signals">${{blip.demand}} job signal${{blip.demand!==1?'s':''}}</div>` : ''}}
        <div class="blip-desc">${{blip.description}}${{jobs}}</div>`;
      el.addEventListener('click', () => el.classList.toggle('open'));
      body.appendChild(el);
    }});

    sec.appendChild(body);

    if (ring === 'hold') {{
      const hint = document.createElement('div');
      hint.className = 'expand-hint';
      hint.textContent = `▼ Show ${{blips.length}} deprioritised skills`;
      hint.addEventListener('click', () => {{
        body.classList.toggle('visible');
        hint.textContent = body.classList.contains('visible')
          ? '▲ Hide hold ring' : `▼ Show ${{blips.length}} deprioritised skills`;
      }});
      sec.appendChild(hint);
    }}

    sec.querySelector('.ring-header').addEventListener('click', (e) => {{
      if (ring !== 'hold') body.style.display = body.style.display === 'none' ? '' : '';
    }});

    grid.appendChild(sec);
  }});

  // Stats
  const stats = document.getElementById('stats');
  const counts = RINGS.map(r => {{
    const n = RADAR.blips.filter(b=>b.ring===r && (activeQ==='all'||b.quadrant===activeQ)).length;
    return `<div><span class="stat-val">${{n}}</span> ${{r}}</div>`;
  }});
  stats.innerHTML = counts.join('') + `<div style="margin-left:auto;color:#6e7681">Score = CATEGORY_WEIGHT + (demand×3) + GAP_BONUS</div>`;
}}

document.querySelectorAll('.filter-btn[data-q]').forEach(btn => {{
  btn.addEventListener('click', () => {{
    activeQ = btn.dataset.q;
    document.querySelectorAll('[data-q]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    renderGrid();
  }});
}});

renderGrid();
</script>
</body>
</html>"""


def main():
    print(f"Loading {RADAR_JSON}...")
    radar = load_and_validate(RADAR_JSON)

    blips = radar["blips"]
    by_ring = {r: [b for b in blips if b["ring"] == r] for r in RING_ORDER}
    print(f"  Blips: {len(blips)} total — " + " | ".join(f"{r}: {len(by_ring[r])}" for r in RING_ORDER))

    print(f"Generating {INDEX_HTML}...")
    html = generate_html(radar)
    with open(INDEX_HTML, "w") as f:
        f.write(html)

    save_history(radar)

    top5 = sorted([b for b in blips if b["ring"] == "trial"], key=lambda b: b["transition_score"], reverse=True)[:5]
    print("\nFocus Board:")
    for i, b in enumerate(top5, 1):
        print(f"  #{i} {b['name']:35s} score={b['transition_score']} demand={b['demand']} gap={b['gap']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
