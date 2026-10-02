import os
import json
import re


# ============================================================
# CONFIG
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DASHBOARD_DIRS = [
    os.path.join(BASE_DIR, "training_dataset", "dashboard_01"),
    os.path.join(BASE_DIR, "training_dataset", "dashboard_02"),
    os.path.join(BASE_DIR, "training_dataset", "dashboard_03"),
    os.path.join(BASE_DIR, "training_dataset", "dashboard_04"),
    os.path.join(BASE_DIR, "training_dataset", "dashboard_05"),
]

KPI_WORDS = [
    "kpi",
    "metric",
    "stat",
    "statistics",
    "total doctor",
    "total staff",
    "total patient",
    "new appointment",
    "total patients",
    "appointments today",
    "bed occupancy",
    "revenue this month",
]

CHART_WORDS = [
    "chart",
    "graph",
    "trend",
    "analytics",
    "overview",
    "demographics",
    "gender",
    "admissions",
    "performance",
]

TABLE_WORDS = [
    "table",
    "patient data",
    "patient activity",
    "recent patient",
    "data table",
]

SECTION_WORDS = [
    "card",
    "section",
    "panel",
    "overview",
    "schedule",
    "calendar",
    "sidebar",
    "header",
    "navigation",
    "support",
]

CONTROL_WORDS = [
    "button",
    "btn",
    "input",
    "text input",
    "slider",
    "rating",
    "dropdown",
    "select",
    "filter",
    "switch",
    "checkbox",
    "radio",
    "pagination",
]

IGNORE_WORDS = [
    "plot-area",
    "plot area",
    "grid-lines",
    "grid lines",
    "x-axis",
    "y-axis",
    "axis",
    "legend",
    "tooltip",
    "months",
    "days",
    "lines",
    "graphs",
    "pagination",
    "icon",
    "vector",
    "horizontal container",
    "vertical container",
    "text input",
    "text input container",
    "paragraph container",
    "button container",
    "container",
    "row",
    "column",
    "circle",
    "rectangle",
    "frame 1",
    "frame 606",
    "frame 1267",
    "frame 1268",
    "frame 1269",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize(text):
    if not text:
        return ""

    text = str(text).lower()
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def node_area(node):
    return float(node.get("width", 0) or 0) * float(node.get("height", 0) or 0)


def node_name(node):
    return normalize(node.get("name", ""))


def node_type(node):
    return str(node.get("type", "")).upper()


def get_text(node):
    text = node.get("text", "")

    if text is None:
        return ""

    return str(text).strip()


def has_word(name, words):
    name = normalize(name)

    return any(word in name for word in words)


def is_control_name(name):
    return has_word(name, CONTROL_WORDS)


def is_ignored_name(name):
    name = normalize(name)

    if not name:
        return False

    return any(word in name for word in IGNORE_WORDS)


def is_root_wrapper(node):
    name = node_name(node)

    if not name:
        return False

    root_words = [
        "medical dashboard",
        "healthcare dashboard",
        "overview",
        "frame 1",
        "frame 606",
        "frame 1267",
        "frame 1268",
        "frame 1269",
    ]

    return name in root_words


# ============================================================
# LOAD FIGMA DATA
# ============================================================

def load_figma_data(folder):

    path = os.path.join(folder, "figma_data.json")

    if not os.path.exists(path):
        print(f"  Missing: {path}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Plugin extractor format
    if isinstance(data, dict) and "nodes" in data:
        return data["nodes"]

    # Older extractor format
    if isinstance(data, list):
        return data

    # REST API format
    if isinstance(data, dict) and "document" in data:
        result = []

        def walk(node, parent_id=None):

            item = {
                "id": node.get("id"),
                "name": node.get("name", ""),
                "type": node.get("type", ""),
                "parent_id": parent_id,
            }

            if "absoluteBoundingBox" in node:
                box = node["absoluteBoundingBox"]

                item["x"] = box.get("x", 0)
                item["y"] = box.get("y", 0)
                item["width"] = box.get("width", 0)
                item["height"] = box.get("height", 0)

            if node.get("type") == "TEXT":
                item["text"] = node.get("characters", "")

            result.append(item)

            for child in node.get("children", []):
                walk(child, node.get("id"))

        walk(data["document"])

        return result

    return []


# ============================================================
# HIERARCHY
# ============================================================

def build_hierarchy(nodes):

    children = {}
    parents = {}

    for node in nodes:

        node_id = node.get("id")
        parent_id = node.get("parent_id")

        parents[node_id] = parent_id

        if parent_id not in children:
            children[parent_id] = []

        children[parent_id].append(node)

    return children, parents


def get_children(node_id, children):

    return children.get(node_id, [])


def get_descendants(node_id, children):

    result = []

    stack = list(children.get(node_id, []))

    while stack:

        node = stack.pop()

        result.append(node)

        stack.extend(children.get(node.get("id"), []))

    return result


def get_ancestor_ids(node_id, parents):

    result = []

    current = parents.get(node_id)

    while current:

        result.append(current)
        current = parents.get(current)

    return result


# ============================================================
# TEXT ANALYSIS
# ============================================================

def collect_text(node, children):

    texts = []

    descendants = [node] + get_descendants(node.get("id"), children)

    for item in descendants:

        text = get_text(item)

        if text:
            texts.append(text)

    return texts


def numeric_texts(texts):

    result = []

    for text in texts:

        clean = text.replace(",", "").replace("$", "").replace("%", "")

        if re.fullmatch(r"-?\d+(\.\d+)?", clean.strip()):
            result.append(text)

    return result


# ============================================================
# STRUCTURAL DETECTION
# ============================================================

def looks_like_kpi(node, children):

    name = node_name(node)

    # Explicit KPI/card naming
    if any(word in name for word in [
        "kpi",
        "metric",
        "stat",
        "total patients",
        "appointments today",
        "bed occupancy",
        "revenue this month",
        "total doctor",
        "total staff",
        "total patient",
        "new appointment",
    ]):
        return True, 0.95

    # Specific dashboard-03 KPI labels
    if name in [
        "doctors",
        "patients",
        "balance",
    ]:
        return True, 0.90

    # Explicitly NOT KPIs
    if name in [
        "status",
        "appointment",
        "total",
        "user account",
        "new patients",
        "opd patients",
        "assigned doctor",
    ]:
        return False, 0

    # Navigation items are never KPIs
    if name.startswith("nav-item"):
        return False, 0

    return False, 0

def looks_like_chart(node, children):

    name = node_name(node)

    # Never classify generic layout containers
    generic_names = [
        "sidebar",
        "main content",
        "main-content",
        "header",
        "schedule",
        "card",
        "container",
        "frame",
        "group",
        "section",
        "overview",
        "hospital overview section",
    ]

    if name in generic_names:
        return False, 0

    # Explicit chart names
    if any(word in name for word in [
        "chart",
        "graph",
        "trend",
    ]):
        return True, 0.95

    # Semantic chart names
    if any(word in name for word in [
        "admissions",
        "demographics",
        "gender",
        "patient overview",
    ]):
        return True, 0.90

    return False, 0

def looks_like_table(node, children):

    name = node_name(node)

    # Internal table elements are not tables
    if name in [
        "table header",
        "table header title",
        "header title",
        "table-header-title",
    ]:
        return False, 0

    if has_word(name, TABLE_WORDS) or "table" in name:
        return True, 0.95

    return False, 0

def looks_like_control(node):

    name = node_name(node)

    if not name:
        return False

    return is_control_name(name)


# ============================================================
# SEMANTIC COMPONENT DETECTION
# ============================================================
def has_semantic_component_child(node, children):

    descendants = get_descendants(
        node.get("id"),
        children
    )

    for child in descendants:

        child_name = node_name(child)

        if (
            "table" in child_name
            or "chart" in child_name
            or "graph" in child_name
            or "kpi" in child_name
        ):
            return True

    return False

def detect_component(node, children):

    name = node_name(node)
    ntype = node_type(node)

    # --------------------------------------------------------
    # NEVER CLASSIFY PAGE / DOCUMENT ROOTS
    # --------------------------------------------------------

    if ntype in ["PAGE", "DOCUMENT"]:
        return None

    # --------------------------------------------------------
    # NEVER CLASSIFY ROOT DASHBOARD WRAPPERS
    # --------------------------------------------------------

    if is_root_wrapper(node):
        return None

    # --------------------------------------------------------
    # INTERNAL FIGMA NODES
    # --------------------------------------------------------

    if is_ignored_name(name):
        return None

    # UI controls are not dashboard components
    if is_control_name(name):
        return None

    # --------------------------------------------------------
    # DON'T CLASSIFY A PARENT WHEN IT CONTAINS A
    # MORE SPECIFIC SEMANTIC COMPONENT
    # --------------------------------------------------------

    if has_semantic_component_child(node, children):

        if (
            "activity" in name
            or "section" in name
            or "card" in name
            or "overview" in name
        ):
            return None

    # --------------------------------------------------------
    # VERY SMALL NODES ARE USUALLY INTERNAL GRAPHICS
    # --------------------------------------------------------

    area = node_area(node)

    if area > 0 and area < 2500:
        return None

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    ok, confidence = looks_like_kpi(
        node,
        children
    )

    if ok:
        return {
            "type": "kpi_card",
            "confidence": confidence
        }

    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    ok, confidence = looks_like_table(
        node,
        children
    )

    if ok:
        return {
            "type": "table",
            "confidence": confidence
        }

    # --------------------------------------------------------
    # CHART
    # --------------------------------------------------------

    ok, confidence = looks_like_chart(
        node,
        children
    )

    if ok:
        return {
            "type": "chart",
            "confidence": confidence
        }

    # --------------------------------------------------------
    # MEANINGFUL SECTIONS
    # --------------------------------------------------------

    if name in [
        "schedule",
        "calendar",
        "department performance",
        "patient activity",
    ]:
        return {
            "type": "section",
            "confidence": 0.82
        }
    return None

# ============================================================
# NESTING / SUPPRESSION
# ============================================================

def has_component_ancestor(node, selected_ids, parents):

    ancestors = get_ancestor_ids(
        node.get("id"),
        parents
    )

    return any(
        ancestor in selected_ids
        for ancestor in ancestors
    )


def remove_nested_components(components, parents):

    selected_ids = {
        component["id"]
        for component in components
    }

    result = []

    for component in components:

        node_id = component["id"]

        ancestors = get_ancestor_ids(
            node_id,
            parents
        )

        # If an ancestor is already selected,
        # keep the higher-level semantic component.
        has_selected_ancestor = any(
            ancestor in selected_ids
            for ancestor in ancestors
        )

        if has_selected_ancestor:
            continue

        result.append(component)

    return result

# ============================================================
# LABEL EXTRACTION
# ============================================================

def get_component_label(node, children):

    name = node.get("name", "").strip()

    texts = collect_text(node, children)

    # Prefer explicit meaningful node name
    if name:

        ignored_names = [
            "frame",
            "group",
            "container",
            "card",
            "table",
            "chart",
        ]

        normalized = normalize(name)

        if normalized not in ignored_names:
            return name

    # Otherwise use first useful text
    for text in texts:

        text_clean = text.strip()

        if len(text_clean) >= 2:

            return text_clean

    return name or "Unnamed component"


# ============================================================
# DATA BINDING
# ============================================================

def get_data_binding(component, children):

    node_id = component["id"]
    node = component["_node"]

    texts = collect_text(node, children)

    nums = numeric_texts(texts)

    component_type = component["type"]

    if component_type == "kpi_card":

        label = None

        for text in texts:

            if text not in nums:
                label = text
                break

        return {
            "label": label,
            "value": nums[0] if nums else None
        }

    if component_type == "chart":

        return {
            "texts": texts[:20]
        }

    if component_type == "table":

        return {
            "columns": texts[:10]
        }

    return {}


# ============================================================
# POSITION
# ============================================================

def get_position(node):

    return {
        "x": node.get("x", 0),
        "y": node.get("y", 0),
        "width": node.get("width", 0),
        "height": node.get("height", 0),
    }


# ============================================================
# BUILD CONFIG
# ============================================================

def build_dashboard_config(nodes):

    children, parents = build_hierarchy(nodes)

    candidates = []

    # --------------------------------------------------------
    # First pass
    # --------------------------------------------------------

    for node in nodes:

        detected = detect_component(
            node,
            children
        )

        if detected is None:
            continue

        component = {
            "id": node.get("id"),
            "name": node.get("name", ""),
            "type": detected["type"],
            "confidence": detected["confidence"],
            "_node": node,
        }

        candidates.append(component)

    # --------------------------------------------------------
    # Remove nested components
    # --------------------------------------------------------

    candidates = remove_nested_components(
        candidates,
        parents
    )

    # --------------------------------------------------------
    # Sort by visual position
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: (
            x["_node"].get("y", 0),
            x["_node"].get("x", 0)
        )
    )

    # --------------------------------------------------------
    # Build final output
    # --------------------------------------------------------

    final_components = []

    for component in candidates:

        node = component["_node"]

        final = {
            "id": component["id"],
            "type": component["type"],
            "name": component["name"],
            "label": get_component_label(
                node,
                children
            ),
            "confidence": round(
                component["confidence"],
                2
            ),
            "position": get_position(node),
            "data_binding": get_data_binding(
                component,
                children
            ),
        }

        final_components.append(final)

    return final_components


# ============================================================
# MAIN
# ============================================================

def process_dashboard(folder):

    dashboard_name = os.path.basename(folder)

    print("\n" + "=" * 60)
    print(f"PROCESSING {dashboard_name}")
    print("=" * 60)

    nodes = load_figma_data(folder)

    if nodes is None:
        return

    print(f"Nodes: {len(nodes)}")

    components = build_dashboard_config(nodes)

    output = {
        "dashboard": dashboard_name,
        "total_nodes": len(nodes),
        "detected_components": len(components),
        "components": components
    }

    output_path = os.path.join(
        folder,
        "dashboard_config.json"
    )

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Detected components: {len(components)}"
    )

    for i, component in enumerate(
        components,
        start=1
    ):

        print(
            f"{i}. "
            f"{component['type'].upper():12} "
            f"{component['name']} "
            f"{component['id']} "
            f"confidence={component['confidence']}"
        )

    print(
        f"\nSaved: {output_path}"
    )


def main():

    print("\n")
    print("=" * 60)
    print("FIGMA DASHBOARD COMPONENT CLASSIFIER")
    print("=" * 60)

    for folder in DASHBOARD_DIRS:
        process_dashboard(folder)

    if not DASHBOARD_DIRS:
        print("\nNo figma_data.json files found.")
        print("Expected location:")
        print(DASHBOARDS_DIR)

    print("\n")
    print("=" * 60)
    print("CLASSIFICATION COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()