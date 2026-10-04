import json
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = ROOT / "dataset" / "dashboards"
LABEL_FILE = (
    ROOT
    / "dataset"
    / "labels"
    / "component_labels.csv"
)

OUTPUT_DIR = (
    ROOT
    / "outputs"
    / "dashboard_configs"
)


VALID_LABELS = {
    "KPI_CARD",
    "CHART",
    "TABLE",
    "FILTER",
    "OTHER"
}


def load_labels():

    labels = {}

    if not LABEL_FILE.exists():
        return labels

    with open(
        LABEL_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)

        for row in reader:

            dashboard = row[
                "dashboard_id"
            ]

            candidate_id = row[
                "candidate_id"
            ]

            label = row[
                "label"
            ].strip()

            if label in VALID_LABELS:

                labels[
                    (
                        dashboard,
                        candidate_id
                    )
                ] = label

    return labels


def load_raw_nodes(
    dashboard
):

    file_path = (
        DATASET_DIR
        / dashboard
        / "figma_data.json"
    )

    if not file_path.exists():
        return {}

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    return {
        node["id"]: node
        for node in data.get(
            "nodes",
            []
        )
        if "id" in node
    }


def main():

    labels = load_labels()

    if not labels:

        print(
            "No valid labels found."
        )

        print(
            "Fill component_labels.csv first."
        )

        return

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    dashboards = sorted(
        {
            dashboard
            for dashboard, _ in labels
        }
    )

    for dashboard in dashboards:

        nodes = load_raw_nodes(
            dashboard
        )

        components = []

        for (
            (label_dashboard, candidate_id),
            label
        ) in labels.items():

            if label_dashboard != dashboard:
                continue

            node = nodes.get(
                candidate_id,
                {}
            )

            component = {
                "id": candidate_id,
                "type": label,
                "name": node.get(
                    "name",
                    ""
                )
            }

            if "x" in node:
                component["position"] = {
                    "x": node.get("x"),
                    "y": node.get("y")
                }

            if (
                "width" in node
                or "height" in node
            ):

                component["size"] = {
                    "width": node.get(
                        "width"
                    ),
                    "height": node.get(
                        "height"
                    )
                }

            components.append(
                component
            )

        output = {
            "dashboard_id": dashboard,
            "components": components
        }

        dashboard_dir = (
            OUTPUT_DIR / dashboard
        )

        dashboard_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            dashboard_dir
            / "dashboard_config.json"
        )

        with open(
            output_file,
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
            f"Created: {output_file}"
        )


if __name__ == "__main__":
    main()