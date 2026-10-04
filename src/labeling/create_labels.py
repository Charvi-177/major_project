import json
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_DIR = ROOT / "dataset" / "candidates"
LABEL_DIR = ROOT / "dataset" / "labels"

LABEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)


VALID_LABELS = {
    "KPI_CARD",
    "CHART",
    "TABLE",
    "FILTER",
    "OTHER"
}


def main():

    files = sorted(
        CANDIDATE_DIR.glob(
            "*_candidates.json"
        )
    )

    if not files:
        print(
            "No candidate files found."
        )
        print(
            "Run generate_candidates.py first."
        )
        return

    rows = []

    for file_path in files:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:
            data = json.load(f)

        dashboard = data.get(
            "dashboard"
        )

        for candidate in data.get(
            "candidates",
            []
        ):

            rows.append({
                "dashboard_id": dashboard,
                "candidate_id": candidate.get(
                    "candidate_id"
                ),
                "name": candidate.get(
                    "name",
                    ""
                ),
                "label": ""
            })

    output_file = (
        LABEL_DIR /
        "component_labels.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dashboard_id",
                "candidate_id",
                "name",
                "label"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    print("=" * 60)
    print("LABEL TEMPLATE CREATED")
    print("=" * 60)
    print(
        f"Candidates: {len(rows)}"
    )
    print(
        f"Output: {output_file}"
    )
    print()
    print(
        "Allowed labels:"
    )

    for label in sorted(
        VALID_LABELS
    ):
        print(
            f"  {label}"
        )


if __name__ == "__main__":
    main()