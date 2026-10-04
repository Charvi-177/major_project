import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = ROOT / "dataset" / "dashboards"
OUTPUT_DIR = ROOT / "dataset" / "candidates"


def build_hierarchy(nodes):

    node_map = {
        node["id"]: node
        for node in nodes
        if "id" in node
    }

    children_map = {
        node_id: []
        for node_id in node_map
    }

    roots = []

    for node in nodes:

        node_id = node.get("id")
        parent_id = node.get("parent_id")

        if not parent_id or parent_id not in node_map:
            roots.append(node_id)

        else:
            children_map[parent_id].append(node_id)

    return node_map, children_map, roots


def main():

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_dirs = sorted(
        p for p in DATASET_DIR.iterdir()
        if p.is_dir()
    )

    for dashboard_dir in dashboard_dirs:

        input_file = dashboard_dir / "figma_data.json"

        if not input_file.exists():
            continue

        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        nodes = data.get("nodes", [])

        node_map, children_map, roots = build_hierarchy(nodes)

        result = {
            "dashboard": dashboard_dir.name,
            "file_name": data.get("file_name"),
            "total_nodes": len(nodes),
            "roots": roots,
            "nodes": node_map,
            "children": children_map
        }

        output_file = (
            OUTPUT_DIR /
            f"{dashboard_dir.name}_hierarchy.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                result,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(
            f"Created: {output_file.name}"
        )


if __name__ == "__main__":
    main()