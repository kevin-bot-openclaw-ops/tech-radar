#!/usr/bin/env python3
"""
generate-radar.py — Reads radar.json, outputs updated index.html.

Usage:
    python3 scripts/generate-radar.py

Input:  radar.json
Output: index.html (self-contained, no external dependencies)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RADAR_JSON = ROOT / "radar.json"
INDEX_HTML = ROOT / "index.html"
HISTORY_DIR = ROOT / "history"


def load_radar() -> dict:
    with open(RADAR_JSON) as f:
        return json.load(f)


def save_history(radar: dict):
    """Archive current radar as dated snapshot."""
    HISTORY_DIR.mkdir(exist_ok=True)
    date = radar.get("date", "unknown")
    snapshot_path = HISTORY_DIR / f"{date}.json"
    with open(snapshot_path, "w") as f:
        json.dump(radar, f, indent=2)
    print(f"Snapshot saved: {snapshot_path}")


def generate_html(radar: dict) -> str:
    radar_json_str = json.dumps(radar, indent=2)
    
    quadrant_labels = {
        "languages-frameworks": "Languages & Frameworks",
        "platforms": "Platforms & Tools",
        "techniques": "Techniques",
        "tools": "Tools"
    }
    ring_order = {"adopt": 0, "trial": 1, "assess": 2, "hold": 3}
    ring_colors = {
        "adopt": "#5cb85c",
        "trial": "#5bc0de",
        "assess": "#f0ad4e",
        "hold": "#d9534f"
    }

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Jerzy Plocha — Technology Radar</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #e6edf3; min-height: 100vh; }}
  header {{ padding: 24px 32px; border-bottom: 1px solid #21262d; display: flex; justify-content: space-between; align-items: center; }}
  header h1 {{ font-size: 20px; font-weight: 600; }}
  header .meta {{ font-size: 13px; color: #8b949e; }}
  .filters {{ padding: 16px 32px; display: flex; gap: 8px; flex-wrap: wrap; border-bottom: 1px solid #21262d; }}
  .filter-btn {{ padding: 6px 14px; border-radius: 20px; border: 1px solid #30363d; background: #161b22; color: #8b949e; cursor: pointer; font-size: 13px; transition: all 0.15s; }}
  .filter-btn:hover, .filter-btn.active {{ border-color: #58a6ff; color: #58a6ff; background: rgba(88,166,255,0.1); }}
  .content {{ padding: 24px 32px; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; }}
  .quadrant {{ background: #161b22; border: 1px solid #21262d; border-radius: 8px; overflow: hidden; }}
  .quadrant-header {{ padding: 14px 16px; background: #1c2128; border-bottom: 1px solid #21262d; font-weight: 600; font-size: 14px; }}
  .ring-section {{ padding: 4px 0; }}
  .ring-label {{ padding: 8px 16px 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; }}
  .blip {{ padding: 8px 16px; display: flex; align-items: flex-start; gap: 10px; border-bottom: 1px solid #21262d; cursor: pointer; transition: background 0.1s; }}
  .blip:last-child {{ border-bottom: none; }}
  .blip:hover {{ background: #1c2128; }}
  .blip-dot {{ width: 8px; height: 8px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }}
  .blip-new {{ width: 0; height: 0; border-left: 5px solid transparent; border-right: 5px solid transparent; border-bottom: 9px solid currentColor; margin-top: 3px; flex-shrink: 0; border-radius: 0; background: none !important; }}
  .blip-content {{ flex: 1; min-width: 0; }}
  .blip-name {{ font-size: 13px; font-weight: 500; }}
  .blip-appearances {{ font-size: 11px; color: #8b949e; margin-top: 2px; }}
  .blip-desc {{ font-size: 12px; color: #8b949e; margin-top: 4px; display: none; line-height: 1.5; }}
  .blip.expanded .blip-desc {{ display: block; }}
  .badge {{ display: inline-block; font-size: 10px; padding: 1px 6px; border-radius: 10px; margin-left: 6px; vertical-align: middle; }}
  .badge-new {{ background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }}
  .stats {{ padding: 16px 32px; display: flex; gap: 24px; border-top: 1px solid #21262d; font-size: 13px; color: #8b949e; }}
  .stat-value {{ font-weight: 600; color: #e6edf3; }}
</style>
</head>
<body>

<header>
  <div>
    <h1>⚡ Technology Radar</h1>
    <div style="font-size:13px;color:#8b949e;margin-top:4px;">Jerzy Plocha · AI/ML Engineering Transition</div>
  </div>
  <div class="meta">v{radar.get('version','1.0')} · {radar.get('date','2026-02-18')} · {len(radar.get('blips',[]))} technologies</div>
</header>

<div class="filters">
  <button class="filter-btn active" data-ring="all">All</button>
  <button class="filter-btn" data-ring="adopt" style="color:#5cb85c">● Adopt</button>
  <button class="filter-btn" data-ring="trial" style="color:#5bc0de">● Trial</button>
  <button class="filter-btn" data-ring="assess" style="color:#f0ad4e">● Assess</button>
  <button class="filter-btn" data-ring="hold" style="color:#d9534f">● Hold</button>
</div>

<div class="content" id="radar-content"></div>

<div class="stats" id="stats"></div>

<script>
const RADAR_DATA = {radar_json_str};

const RING_COLORS = {{
  adopt: '#5cb85c', trial: '#5bc0de', assess: '#f0ad4e', hold: '#d9534f'
}};
const RING_ORDER = ['adopt', 'trial', 'assess', 'hold'];
const QUADRANT_LABELS = {{
  'languages-frameworks': 'Languages & Frameworks',
  'platforms': 'Platforms & Tools',
  'techniques': 'Techniques',
  'tools': 'Tools'
}};

let activeRing = 'all';

function render() {{
  const blips = RADAR_DATA.blips.filter(b => activeRing === 'all' || b.ring === activeRing);
  
  // Group by quadrant
  const byQuadrant = {{}};
  blips.forEach(b => {{
    if (!byQuadrant[b.quadrant]) byQuadrant[b.quadrant] = [];
    byQuadrant[b.quadrant].push(b);
  }});

  const content = document.getElementById('radar-content');
  content.innerHTML = '';

  Object.entries(byQuadrant).forEach(([q, qBlips]) => {{
    const div = document.createElement('div');
    div.className = 'quadrant';

    const header = document.createElement('div');
    header.className = 'quadrant-header';
    header.textContent = QUADRANT_LABELS[q] || q;
    div.appendChild(header);

    // Group by ring
    RING_ORDER.forEach(ring => {{
      const ringBlips = qBlips.filter(b => b.ring === ring);
      if (!ringBlips.length) return;

      const section = document.createElement('div');
      section.className = 'ring-section';

      const label = document.createElement('div');
      label.className = 'ring-label';
      label.style.color = RING_COLORS[ring];
      label.textContent = ring.toUpperCase();
      section.appendChild(label);

      ringBlips.sort((a,b) => (b.appearances||0) - (a.appearances||0)).forEach(blip => {{
        const el = document.createElement('div');
        el.className = 'blip';
        el.innerHTML = `
          <div class="${{blip.isNew ? 'blip-new' : 'blip-dot'}}" style="background:${{RING_COLORS[ring]}};color:${{RING_COLORS[ring]}}"></div>
          <div class="blip-content">
            <div class="blip-name">
              ${{blip.name}}
              ${{blip.isNew ? '<span class="badge badge-new">NEW</span>' : ''}}
            </div>
            ${{blip.appearances ? `<div class="blip-appearances">${{blip.appearances}} job signal${{blip.appearances>1?'s':''}}</div>` : ''}}
            <div class="blip-desc">${{blip.description}}</div>
          </div>
        `;
        el.addEventListener('click', () => el.classList.toggle('expanded'));
        section.appendChild(el);
      }});

      div.appendChild(section);
    }});

    content.appendChild(div);
  }});

  // Stats
  const counts = RING_ORDER.map(r => `<div><span class="stat-value">${{blips.filter(b=>b.ring===r).length}}</span> ${{r}}</div>`);
  document.getElementById('stats').innerHTML = `<div><span class="stat-value">${{blips.length}}</span> total</div>` + counts.join('');
}}

// Filter buttons
document.querySelectorAll('.filter-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    activeRing = btn.dataset.ring;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    render();
  }});
}});

render();
</script>
</body>
</html>
"""

def main():
    print("Loading radar.json...")
    radar = load_radar()
    
    print(f"Generating HTML for {len(radar['blips'])} blips...")
    html = generate_html(radar)
    
    with open(INDEX_HTML, "w") as f:
        f.write(html)
    print(f"Generated: {INDEX_HTML}")
    
    save_history(radar)
    print("Done.")


if __name__ == "__main__":
    main()
