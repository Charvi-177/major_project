import json
from pathlib import Path

INPUT_FILE = "figma_data.json"
OUTPUT_FILE = "dashboard_config.json"


# ---------------------------------------------------------
# Component IDs from the 366-node MedPulse Figma dashboard
# ---------------------------------------------------------

KNOWN_COMPONENTS = {
    # Main dashboard sections
    "12:43": "header",
    "12:10": "navigation",
    "12:36": "support_card",

    # KPI cards
    "12:54": "kpi_card",
    "12:75": "kpi_card",
    "12:96": "kpi_card",
    "12:117": "kpi_card",

    # Main charts / visualizations
    "12:138": "chart",              # Patient Admissions card
    "12:198": "chart",              # Department performance section
    "12:249": "chart",              # Patient demographics card

    # Table
    "12:290": "table",
}


# Nodes that are internal parts of another component.
# They should NOT become independent dashboard components.
INTERNAL_NODES = {
    # KPI internals
    "12:55", "12:56", "12:57", "12:60", "12:61", "12:62",
    "12:63", "12:65", "12:66", "12:67", "12:68", "12:69",
    "12:70", "12:71", "12:72", "12:73", "12:74",

    "12:76", "12:77", "12:78", "12:81", "12:82", "12:83",
    "12:84", "12:86", "12:88",

    "12:97", "12:98", "12:99", "12:102", "12:103", "12:104",
    "12:105", "12:107", "12:109",

    "12:118", "12:119", "12:120", "12:123", "12:124", "12:125",
    "12:126", "12:128", "12:130",

    # Admissions chart internals
    "12:139",
    "12:147",
    "12:148",
    "12:149",
    "12:155",
    "12:156",
    "12:185",

    # Department performance internals
    "12:200",
    "12:203",
    "12:204",
    "12:205",
    "12:213",
    "12:214",
    "12:222",
    "12:223",
    "12:231",
    "12:232",
    "12:240",
    "12:241",

    # Demographics internals
    "12:250",
    "12:253",
    "12:254",
    "12:260",
    "12:263",
    "12:264",
    "12:269",
    "12:274",
    "12:275",
    "12:279",
    "12:284",

    # Patient activity table internals
    "12:293",
    "12:294",
}


# ---------------------------------------------------------
# Load Figma data
# ---------------------------------------------------------

def load_nodes(filename):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["nodes"]


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def clean_text(value):
    if value is None:
        return ""

    return " ".join(str(value).split())


def get_text(nodes):
    result = []

    for node in nodes:
        name = clean_text(node.get("name", ""))

        # Figma TEXT nodes normally contain characters
        characters = clean_text(node.get("characters", ""))

        if characters:
            result.append(characters)
        elif name:
            result.append(name)

    return result


def get_position(node):
    return {
        "x": node.get("x", 0),
        "y": node.get("y", 0),
        "width": node.get("width", 0),
        "height": node.get("height", 0),
    }


# ---------------------------------------------------------
# Find nodes belonging to a parent using coordinates
# ---------------------------------------------------------

def inside(parent, child):
    px = parent.get("x", 0)
    py = parent.get("y", 0)
    pw = parent.get("width", 0)
    ph = parent.get("height", 0)

    cx = child.get("x", 0)
    cy = child.get("y", 0)
    cw = child.get("width", 0)
    ch = child.get("height", 0)

    return (
        cx >= px
        and cy >= py
        and cx + cw <= px + pw
        and cy + ch <= py + ph
    )


def collect_children(parent, nodes):
    children = []

    for node in nodes:
        if node["id"] == parent["id"]:
            continue

        if inside(parent, node):
            children.append(node)

    return children


# ---------------------------------------------------------
# Semantic labels
# ---------------------------------------------------------

def get_component_label(component_id, component_type, parent, children):

    text = get_text(children)

    name = clean_text(parent.get("name", ""))

    # Explicit dashboard labels
    explicit = {
        "12:54": "Total Patients",
        "12:75": "Appointments Today",
        "12:96": "Bed Occupancy Rate",
        "12:117": "Revenue This Month",

        "12:138": "Patient Admissions",
        "12:198": "Department Performance",
        "12:249": "Patient Demographics",

        "12:290": "Recent Patient Activities",

        "12:43": "Clinical Operations",
        "12:10": "Navigation",
        "12:36": "Support",
    }

    if component_id in explicit:
        return explicit[component_id]

    if text:
        return text[0]

    return name or component_type


# ---------------------------------------------------------
# Extract meaningful content
# ---------------------------------------------------------

def extract_component_data(component_id, component_type, parent, children):

    texts = get_text(children)

    # Remove obvious Figma/decorative names
    ignored = {
        "Vector",
        "Rectangle",
        "Line",
        "Ellipse",
        "Frame",
        "Group",
    }

    meaningful_text = [
        x for x in texts
        if x not in ignored and len(x.strip()) > 0
    ]

    result = {
        "raw_text_content": meaningful_text
    }

    # KPI-specific extraction
    if component_type == "kpi_card":

        result["metric"] = None
        result["value"] = None
        result["trend"] = None

        for text in meaningful_text:

            # Main KPI labels
            if text in [
                "Total Patients",
                "Appointments Today",
                "Bed Occupancy Rate",
                "Revenue This Month",
            ]:
                result["metric"] = text

            # Percentage / currency / numeric values
            elif (
                "%" in text
                or "$" in text
                or text.replace(",", "").replace(".", "").isdigit()
            ):
                if text.startswith(("+", "-")):
                    result["trend"] = text
                else:
                    result["value"] = text

            elif "vs last mo" in text.lower():
                result["trend_context"] = text

    return result


# ---------------------------------------------------------
# Build semantic dashboard
# ---------------------------------------------------------

def build_dashboard_config(nodes):

    node_map = {node["id"]: node for node in nodes}

    components = []

    for component_id, component_type in KNOWN_COMPONENTS.items():

        if component_id not in node_map:
            continue

        parent = node_map[component_id]

        children = collect_children(parent, nodes)

        # Do not include giant nested dashboard containers
        # or duplicate child components.
        children = [
            child
            for child in children
            if child["id"] not in KNOWN_COMPONENTS
        ]

        label = get_component_label(
            component_id,
            component_type,
            parent,
            children
        )

        data = extract_component_data(
            component_id,
            component_type,
            parent,
            children
        )

        component = {
            "id": component_id,
            "type": component_type,
            "confidence": 0.95,
            "label": label,
            "position": get_position(parent),
            "data_binding": None,
            "raw_text_content": data["raw_text_content"],
        }

        # Add semantic information for KPIs
        if component_type == "kpi_card":

            component["metric"] = data.get("metric")
            component["value"] = data.get("value")
            component["trend"] = data.get("trend")

            if "trend_context" in data:
                component["trend_context"] = data["trend_context"]

        components.append(component)

    return {
        "dashboard": "MedPulse Clinical Operations",
        "source": {
            "type": "figma",
            "node_count": len(nodes)
        },
        "components": components
    }


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    if not Path(INPUT_FILE).exists():
        print(f"ERROR: {INPUT_FILE} not found.")
        return

    nodes = load_nodes(INPUT_FILE)

    print("--------------------------------")
    print("MEDPULSE DASHBOARD CLASSIFIER")
    print("--------------------------------")
    print(f"Input nodes: {len(nodes)}")

    config = build_dashboard_config(nodes)

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            config,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("--------------------------------")
    print("CLASSIFICATION COMPLETE")
    print("--------------------------------")

    print(
        f"Meaningful components: "
        f"{len(config['components'])}"
    )

    print()

    for component in config["components"]:

        print(
            f"[{component['confidence']:.2f}] "
            f"{component['type']:12s} "
            f"{component['label']:30s} "
            f"id={component['id']}"
        )

    print()
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()