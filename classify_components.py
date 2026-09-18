"""
classify_components.py

Reads figma_data.json (flat list of Figma nodes extracted via the Figma REST API)
and produces dashboard_config.json — a structured, classified representation of
the dashboard's components (kpi_card, chart, table, filter, button, unknown).

USAGE:
    python classify_components.py
    (expects figma_data.json in the same folder; writes dashboard_config.json)

ASSUMPTIONS ABOUT INPUT SHAPE:
    figma_data.json = {
        "nodes": [
            {
                "id": "25:5",
                "name": "Breakpoints",
                "type": "TEXT" | "RECTANGLE" | "FRAME" | "VECTOR" | "INSTANCE" | ...,
                "x": float, "y": float, "width": float, "height": float,
                # TEXT nodes only:
                "text": str, "font_family": str, "font_size": float, "font_weight": int
            },
            ...
        ]
    }

Since this flattened export has NO parent/child nesting, this script:
  1. Picks "container" candidates (FRAME / RECTANGLE / INSTANCE nodes above a
     minimum size) as potential components.
  2. Finds which other nodes (mostly TEXT) spatially fall INSIDE each container's
     bounding box.
  3. Extracts features from that group (child count, text content/shape, layout
     pattern) and classifies the container as kpi_card / chart / table / filter /
     button / unknown using simple heuristic rules.
  4. Writes out dashboard_config.json with each component's type, position, and
     a placeholder data_binding field.
"""

import json
import re
from pathlib import Path

INPUT_FILE = "figma_data.json"
OUTPUT_FILE = "dashboard_config.json"

# ---- tunable thresholds -----------------------------------------------------
MIN_CONTAINER_AREA = 2000       # ignore tiny decorative rects as "containers"
CONTAINMENT_MARGIN = 2          # px tolerance when checking if a node is "inside" another


def load_nodes(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    nodes = data["nodes"]

    # Keep only nodes that actually have usable geometry. Root/canvas/document
    # nodes, or certain Figma node types, can be exported without x/y/width/height.
    valid = []
    skipped = 0
    for n in nodes:
        if all(k in n for k in ("x", "y", "width", "height")):
            valid.append(n)
        else:
            skipped += 1
    if skipped:
        print(f"Skipped {skipped} node(s) with missing geometry (no x/y/width/height).")
    return valid


def bbox(node):
    """Return (x0, y0, x1, y1) for a node."""
    x0, y0 = node["x"], node["y"]
    x1, y1 = x0 + node.get("width", 0), y0 + node.get("height", 0)
    return x0, y0, x1, y1


def area(node):
    return node.get("width", 0) * node.get("height", 0)


def is_inside(inner, outer, margin=CONTAINMENT_MARGIN):
    """True if inner's bbox is contained within outer's bbox (with tolerance)."""
    ix0, iy0, ix1, iy1 = bbox(inner)
    ox0, oy0, ox1, oy1 = bbox(outer)
    return (
        ix0 >= ox0 - margin and iy0 >= oy0 - margin and
        ix1 <= ox1 + margin and iy1 <= oy1 + margin
    )


def find_container_candidates(nodes):
    """Nodes likely to represent a whole component (card/chart/table wrapper)."""
    candidates = []
    for n in nodes:
        if n["type"] in ("FRAME", "RECTANGLE", "INSTANCE", "GROUP"):
            if area(n) >= MIN_CONTAINER_AREA:
                candidates.append(n)
    # Largest first isn't necessarily right, but sorting by area helps us
    # skip nesting a container inside another container of similar size.
    candidates.sort(key=area)
    return candidates


def assign_children(container, all_nodes, claimed_ids):
    """Return nodes (excluding the container itself) that sit inside container
    and haven't already been claimed by a smaller container."""
    children = []
    for n in all_nodes:
        if n["id"] == container["id"] or n["id"] in claimed_ids:
            continue
        if n["type"] == container["type"] and area(n) >= area(container):
            continue  # skip same-or-larger containers
        if is_inside(n, container):
            children.append(n)
    return children


# ---- feature extraction ------------------------------------------------------

NUMBER_RE = re.compile(r"^[\$₹€£]?[\d,]+(\.\d+)?%?[KkMmBb]?$")


def looks_like_number(text: str) -> bool:
    return bool(NUMBER_RE.match(text.strip()))


def extract_features(container, children):
    texts = [c for c in children if c["type"] == "TEXT"]
    rects = [c for c in children if c["type"] == "RECTANGLE"]
    vectors = [c for c in children if c["type"] == "VECTOR"]

    text_values = [t.get("text", "").strip() for t in texts]
    numeric_texts = [t for t in text_values if looks_like_number(t)]

    w, h = container.get("width", 0), container.get("height", 0)
    aspect_ratio = w / h if h else 0

    # crude "grid-likeness": many text nodes roughly aligned in rows/columns
    ys = sorted(t["y"] for t in texts)
    distinct_rows = len(set(round(y / 10) for y in ys)) if ys else 0

    xs = sorted(t["x"] for t in texts)
    distinct_cols = len(set(round(x / 10) for x in xs)) if xs else 0

    return {
        "name": container.get("name", ""),
        "num_text": len(texts),
        "num_rect": len(rects),
        "num_vector": len(vectors),
        "num_numeric_text": len(numeric_texts),
        "aspect_ratio": aspect_ratio,
        "area": area(container),
        "distinct_rows": distinct_rows,
        "distinct_cols": distinct_cols,
        "text_values": text_values,
    }


# ---- classification rules ----------------------------------------------------

def classify(features):
    name = features["name"].lower()

    # 1. Name hints (fast path — but never trusted alone)
    name_hint = None
    if any(k in name for k in ("kpi", "metric", "stat")):
        name_hint = "kpi_card"
    elif any(k in name for k in ("chart", "graph", "trend")):
        name_hint = "chart"
    elif any(k in name for k in ("table", "list", "grid")):
        name_hint = "table"
    elif any(k in name for k in ("filter", "dropdown", "select")):
        name_hint = "filter"
    elif any(k in name for k in ("button", "btn", "cta")):
        name_hint = "button"

    # 2. Structural rules
    # KPI card: small-ish, 1-2 text nodes, one of them numeric, low text density
    if (
        features["num_text"] in (1, 2)
        and features["num_numeric_text"] >= 1
        and features["area"] < 60000
    ):
        return "kpi_card", 0.85

    # Table: multiple rows AND multiple columns of text (grid pattern)
    if features["distinct_rows"] >= 3 and features["distinct_cols"] >= 2:
        return "table", 0.8

    # Chart: many rectangles/vectors, few/no text, wider than tall
    if (
        (features["num_rect"] >= 3 or features["num_vector"] >= 1)
        and features["num_text"] <= 3
        and features["aspect_ratio"] > 1.0
    ):
        return "chart", 0.75

    # Button: single short text, small area, low height
    if features["num_text"] == 1 and features["area"] < 8000:
        text = features["text_values"][0] if features["text_values"] else ""
        if len(text) <= 20 and not looks_like_number(text):
            return "button", 0.6

    # Filter: single text + small width, name hint helps a lot here
    if name_hint == "filter":
        return "filter", 0.6

    # 3. Fall back to name hint if structural rules found nothing
    if name_hint:
        return name_hint, 0.4

    return "unknown", 0.0


# ---- main pipeline -------------------------------------------------------

def build_dashboard_config(nodes, debug=False):
    containers = find_container_candidates(nodes)
    claimed_ids = set()
    components = []

    for container in containers:
        children = assign_children(container, nodes, claimed_ids)
        features = extract_features(container, children)
        comp_type, confidence = classify(features)

        if debug:
            print(f"--- container id={container['id']} name='{container.get('name')}' ---")
            print(f"    texts={features['text_values']}")
            print(f"    num_text={features['num_text']} num_numeric_text={features['num_numeric_text']} "
                  f"num_rect={features['num_rect']} num_vector={features['num_vector']}")
            print(f"    area={features['area']:.0f} aspect_ratio={features['aspect_ratio']:.2f} "
                  f"rows={features['distinct_rows']} cols={features['distinct_cols']}")
            print(f"    -> classified as {comp_type} ({confidence:.2f})")

        if comp_type == "unknown" and not children:
            # skip empty decorative rectangles entirely
            continue

        for c in children:
            claimed_ids.add(c["id"])
        claimed_ids.add(container["id"])

        components.append({
            "id": container["id"],
            "type": comp_type,
            "confidence": confidence,
            "label": features["text_values"][0] if features["text_values"] else container.get("name"),
            "position": {
                "x": container["x"],
                "y": container["y"],
                "width": container.get("width", 0),
                "height": container.get("height", 0),
            },
            "data_binding": None,  # to be filled in manually or by a later mapping step
            "raw_text_content": features["text_values"],
        })

    return {"dashboard": "unnamed", "components": components}


DEBUG = True  # set to False once classification looks right


def main():
    if not Path(INPUT_FILE).exists():
        print(f"ERROR: {INPUT_FILE} not found in current folder.")
        return

    nodes = load_nodes(INPUT_FILE)
    config = build_dashboard_config(nodes, debug=DEBUG)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Classified {len(config['components'])} components -> {OUTPUT_FILE}")
    for c in config["components"]:
        print(f"  [{c['confidence']:.2f}] {c['type']:10s} '{c['label']}'  id={c['id']}")


if __name__ == "__main__":
    main()
