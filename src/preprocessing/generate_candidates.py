import json
import os
import re
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DASHBOARDS_DIR = os.path.join(BASE_DIR, "dataset", "dashboards")
OUTPUT_DIR = os.path.join(BASE_DIR, "dataset", "candidates")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CONTAINER_TYPES = {"FRAME", "COMPONENT", "COMPONENT_SET", "INSTANCE", "GROUP", "SECTION"}

ROOT_NAMES = {
    "page 1", "page 2", "dashboard", "healthcare dashboard", "health dashboard",
    "medical dashboard", "medical dashboard design",
    "01 dashboard landing page", "01 dashboard - landing page",
    "13 configurations", "additional dashboard components light theme",
}

INTERNAL_NAMES = {
    "chart", "bars", "bar", "points", "map", "legend", "plot area",
    "grid lines", "grid line", "x axis", "y axis", "axis", "axes",
    "table header", "table header title", "table body", "table footer",
    "pagination", "table pagination", "dept list", "department list",
    "demographics body", "demographics legend", "nav list", "navigation list",
    "sidebar footer", "sidebar header",
}

INTERNAL_WORDS = (
    "grid line", "plot area", "axis", "legend", "pagination",
    "table header", "table body", "table footer", "mask group",
)

UI_WORDS = (
    "sidebar", "side nav", "navigation", "navbar", "topbar", "logo",
    "notification icon", "search bar", "settings", "log out", "logout",
    "support", "technical help", "download report", "language",
    "application settings", "contact management", "chat with visitors",
)

SEMANTIC_WORDS = (
    "kpi", "metric", "patient", "patients", "doctor", "doctors",
    "appointment", "appointments", "admission", "admissions", "revenue",
    "payment", "payments", "inventory", "pharmacy", "medicine", "medicines",
    "customer", "customers", "diagnostic", "diagnostics", "health index",
    "causes range", "overview", "statistics", "analytics", "performance",
    "demographics", "gender", "survey", "report", "reports", "activity",
    "activities", "schedule", "calendar", "table", "chart", "graph",
    "surgery", "surgeries", "covid", "disease", "symptom",
)

NUMBER_RE = re.compile(r"^[\$₹€£]?\s*[\d,.]+\s*%?\s*[KkMmBb]?$")
DATE_RE = re.compile(
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
)

def norm(value):
    value = str(value or "").lower().strip()
    value = re.sub(r"[_-]+", " ", value)
    return re.sub(r"\s+", " ", value)

def is_container(node):
    return node.get("type") in CONTAINER_TYPES

def is_internal(node):
    name = norm(node.get("name"))
    return (
        name in INTERNAL_NAMES
        or name.startswith("row ")
        or any(word in name for word in INTERNAL_WORDS)
    )

def is_ui(node):
    name = norm(node.get("name"))
    return (
        name in UI_WORDS
        or any(name.startswith(w + " ") for w in UI_WORDS)
        or "sidebar" in name
        or "side nav" in name
    )

def make_maps(nodes):
    node_map = {n["id"]: n for n in nodes if n.get("id")}
    children = defaultdict(list)
    for n in nodes:
        p = n.get("parent_id")
        if p in node_map:
            children[p].append(n["id"])
    return node_map, children

def descendants(node_id, children):
    out = []
    stack = list(children.get(node_id, []))
    while stack:
        cid = stack.pop()
        out.append(cid)
        stack.extend(children.get(cid, []))
    return out

def stats(node_id, node_map, children):
    ids = descendants(node_id, children)
    all_nodes = [node_map[i] for i in ids]
    texts = [
        str(n.get("text", "")).strip()
        for n in all_nodes if n.get("type") == "TEXT" and str(n.get("text", "")).strip()
    ]
    direct = [node_map[i] for i in children.get(node_id, [])]
    numeric = [t for t in texts if NUMBER_RE.match(t) or re.search(r"\d", t)]
    vectors = sum(n.get("type") == "VECTOR" for n in all_nodes)
    lines = sum(n.get("type") == "LINE" for n in all_nodes)
    ellipses = sum(n.get("type") == "ELLIPSE" for n in all_nodes)
    rectangles = sum(n.get("type") == "RECTANGLE" for n in all_nodes)
    width = float(node_map[node_id].get("width") or 0)
    height = float(node_map[node_id].get("height") or 0)
    return {
        "texts": texts,
        "text_count": len(texts),
        "numeric_count": len(numeric),
        "date_count": sum(bool(DATE_RE.search(t.lower())) for t in texts),
        "vector_count": vectors,
        "line_count": lines,
        "ellipse_count": ellipses,
        "rectangle_count": rectangles,
        "graphic_count": vectors + lines + ellipses + rectangles,
        "direct_count": len(direct),
        "direct_container_count": sum(is_container(n) for n in direct),
        "descendant_count": len(all_nodes),
        "width": width,
        "height": height,
        "area": width * height,
        "aspect_ratio": width / height if height else 0,
    }

def looks_like_layout_wrapper(node, info):
    name = norm(node.get("name"))
    if name in ROOT_NAMES:
        return True
    if name in {
        "main content", "content area", "dashboard content", "kpis row",
        "split row", "main row", "content row", "dashboard row", "top row", "bottom row"
    }:
        return True
    if info["width"] >= 1200 and info["height"] >= 650:
        return True
    # A section containing many sibling components is a layout wrapper.
    if info["direct_container_count"] >= 4 and info["area"] >= 60000:
        return True
    if info["direct_container_count"] >= 3 and info["area"] >= 180000:
        return True
    return False

def semantic_strength(node, info):
    haystack = norm(node.get("name")) + " " + " ".join(info["texts"]).lower()
    return sum(word in haystack for word in SEMANTIC_WORDS)

def score(node, info):
    name = norm(node.get("name"))
    s = min(4, semantic_strength(node, info))
    if info["text_count"] >= 2: s += 2
    if info["numeric_count"] >= 1: s += 1
    if info["numeric_count"] >= 3: s += 1
    if info["graphic_count"] >= 3: s += 1
    if info["graphic_count"] >= 8: s += 1
    if info["ellipse_count"] >= 2: s += 1
    if info["line_count"] >= 4: s += 1
    if info["direct_container_count"] >= 2: s += 1
    if info["area"] >= 20000: s += 1
    if info["area"] >= 50000: s += 1
    if name.startswith("element "): s += 3
    return s

def is_component_candidate(node, info):
    name = norm(node.get("name"))
    if is_internal(node) or is_ui(node):
        return False
    if info["width"] < 70 or info["height"] < 40:
        return False
    if looks_like_layout_wrapper(node, info):
        return False

    sem = semantic_strength(node, info)
    s = score(node, info)

    if name.startswith("element ") and info["area"] >= 15000:
        return info["text_count"] > 0 or info["graphic_count"] >= 3
    if name.startswith("kpi") and info["area"] >= 5000:
        return True

    # Named component: name/text itself is useful, but structure still matters.
    if sem >= 1 and info["area"] >= 8000 and (
        info["text_count"] >= 1 or info["graphic_count"] >= 2
    ):
        return True

    # Generic groups/frames: rely on structure instead of names.
    if info["area"] >= 18000 and s >= 6 and (
        info["text_count"] >= 2 or info["graphic_count"] >= 5
    ):
        return True

    return False

def ancestor_ids(node_id, node_map):
    out = []
    p = node_map[node_id].get("parent_id")
    while p:
        out.append(p)
        p = node_map.get(p, {}).get("parent_id")
    return out

def build_candidate(node, info, dashboard):
    name = norm(node.get("name"))
    texts = info["texts"]
    return {
        "candidate_id": node.get("id"),
        "name": node.get("name"),
        "type": node.get("type"),
        "parent_id": node.get("parent_id"),
        "x": node.get("x", 0), "y": node.get("y", 0),
        "width": info["width"], "height": info["height"],
        "area": info["area"], "aspect_ratio": info["aspect_ratio"],
        "child_count": info["direct_count"],
        "text_count": info["text_count"],
        "numeric_text_count": info["numeric_count"],
        "has_percentage": any("%" in t for t in texts),
        "has_date_text": info["date_count"] > 0,
        "vector_count": info["vector_count"],
        "line_count": info["line_count"],
        "ellipse_count": info["ellipse_count"],
        "rectangle_count": info["rectangle_count"],
        "graphical_count": info["graphic_count"],
        "text_preview": texts[:10],
        "dashboard": dashboard,
        "candidate_score": score(node, info),
        "has_chart_word": any(w in name for w in ("chart", "graph", "trend", "overview", "analytics")),
        "has_table_word": any(w in name for w in ("table", "list", "records", "activity", "payment")),
        "has_kpi_word": any(w in name for w in ("kpi", "metric")),
        "has_filter_word": any(w in name for w in ("filter", "dropdown", "select", "date picker")),
    }

def remove_nested(candidates, node_map, children):
    ids = {c["candidate_id"] for c in candidates}
    kept = []
    for c in candidates:
        ancestors = ancestor_ids(c["candidate_id"], node_map)
        parent_candidates = [a for a in ancestors if a in ids]
        if not parent_candidates:
            kept.append(c)
            continue

        nearest = parent_candidates[0]
        parent = node_map[nearest]
        pinfo = stats(nearest, node_map, children)
        pname = norm(parent.get("name"))

        # Layout sections should expose their child components.
        if pname in {"kpis row", "split row"}:
            kept.append(c)
        elif pinfo["direct_container_count"] >= 3 and pinfo["area"] >= 60000:
            kept.append(c)
        elif "table" in norm(node_map[c["candidate_id"]].get("name")) and "activity" in pname:
            kept.append(c)
        # Otherwise prefer the highest-level meaningful component.
        else:
            continue
    return kept

def generate_dashboard(dashboard_dir):
    dashboard = os.path.basename(dashboard_dir)
    path = os.path.join(dashboard_dir, "figma_data.json")
    if not os.path.exists(path):
        print(f"[SKIP] {dashboard}: figma_data.json not found")
        return

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    node_map, children = make_maps(nodes)
    candidates = []

    for node in nodes:
        if not is_container(node):
            continue
        info = stats(node["id"], node_map, children)
        if is_component_candidate(node, info):
            candidates.append(build_candidate(node, info, dashboard))

    candidates = remove_nested(candidates, node_map, children)
    candidates = list({c["candidate_id"]: c for c in candidates}.values())
    candidates.sort(key=lambda c: (float(c.get("y") or 0), float(c.get("x") or 0)))

    output = {"dashboard": dashboard, "candidate_count": len(candidates), "candidates": candidates}
    out = os.path.join(OUTPUT_DIR, f"{dashboard}_candidates.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[DONE] {dashboard}: {len(candidates)} candidates")
    for c in candidates:
        print(f"   - {c['candidate_id']} | {c['name']} | score={c['candidate_score']}")

def main():
    print("=" * 60)
    print("GENERATING DASHBOARD COMPONENT CANDIDATES")
    print("=" * 60)
    dashboards = sorted(
        d for d in os.listdir(DASHBOARDS_DIR)
        if os.path.isdir(os.path.join(DASHBOARDS_DIR, d))
    )
    print(f"Found {len(dashboards)} dashboards.")
    for dashboard in dashboards:
        generate_dashboard(os.path.join(DASHBOARDS_DIR, dashboard))
    print("=" * 60)
    print("CANDIDATE GENERATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
