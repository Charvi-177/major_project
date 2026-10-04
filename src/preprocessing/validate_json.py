import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "dataset" / "dashboards"


def validate_file(file_path):
    errors = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Invalid JSON: {e}"]

    if not isinstance(data, dict):
        errors.append("Root must be a JSON object.")
        return errors

    if "nodes" not in data:
        errors.append("Missing 'nodes' field.")
        return errors

    nodes = data["nodes"]

    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list.")
        return errors

    if len(nodes) == 0:
        errors.append("Node list is empty.")

    ids = set()

    for i, node in enumerate(nodes):

        if not isinstance(node, dict):
            errors.append(f"Node {i} is not an object.")
            continue

        if "id" not in node:
            errors.append(f"Node {i} missing id.")

        else:
            node_id = node["id"]

            if node_id in ids:
                errors.append(f"Duplicate node id: {node_id}")

            ids.add(node_id)

        if "type" not in node:
            errors.append(f"Node {i} missing type.")

    # Check parent references
    for node in nodes:
        parent_id = node.get("parent_id")

        if parent_id and parent_id not in ids:
            errors.append(
                f"Node {node.get('id')} references "
                f"missing parent {parent_id}"
            )

    return errors


def main():

    if not DATASET_DIR.exists():
        print("Dataset directory not found:")
        print(DATASET_DIR)
        return

    dashboard_dirs = sorted(
        p for p in DATASET_DIR.iterdir()
        if p.is_dir()
    )

    if not dashboard_dirs:
        print("No dashboard folders found.")
        return

    print("=" * 60)
    print("FIGMA JSON VALIDATION")
    print("=" * 60)

    total = 0
    valid = 0

    for dashboard_dir in dashboard_dirs:

        file_path = dashboard_dir / "figma_data.json"

        if not file_path.exists():
            print(f"\n❌ {dashboard_dir.name}")
            print("   Missing figma_data.json")
            continue

        total += 1

        errors = validate_file(file_path)

        if errors:
            print(f"\n❌ {dashboard_dir.name}")

            for error in errors[:20]:
                print(f"   - {error}")

            if len(errors) > 20:
                print(
                    f"   ... and {len(errors) - 20} more errors"
                )

        else:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(
                f"\n✅ {dashboard_dir.name} "
                f"({len(data['nodes'])} nodes)"
            )

            valid += 1

    print("\n" + "=" * 60)
    print(f"VALID: {valid}/{total}")
    print("=" * 60)


if __name__ == "__main__":
    main()