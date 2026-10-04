import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DASHBOARDS_DIR = BASE_DIR / "dataset" / "dashboards"


CONTAINER_TYPES = {
    "FRAME",
    "COMPONENT",
    "COMPONENT_SET",
    "INSTANCE",
    "GROUP",
    "SECTION",
}


for json_file in sorted(DASHBOARDS_DIR.glob("*/figma_data.json")):

    dashboard = json_file.parent.name

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])

    print()
    print("=" * 100)
    print(dashboard)
    print("=" * 100)

    for node in nodes:

        if node.get("type") not in CONTAINER_TYPES:
            continue

        node_id = node.get("id")
        node_type = node.get("type")
        name = node.get("name", "")
        parent_id = node.get("parent_id")

        width = node.get("width", 0)
        height = node.get("height", 0)

        children = [
            n
            for n in nodes
            if n.get("parent_id") == node_id
        ]

        text_children = [
            n
            for n in children
            if n.get("type") == "TEXT"
        ]

        texts = []

        for child in text_children:
            text = str(
                child.get("text", "")
            ).strip()

            if text:
                texts.append(text)

        print(
            f"{node_id:>8} | "
            f"{node_type:<12} | "
            f"{name[:40]:<40} | "
            f"parent={str(parent_id):<8} | "
            f"size={width:.0f}x{height:.0f} | "
            f"children={len(children):<3} | "
            f"text={texts[:5]}"
        )