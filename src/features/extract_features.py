import json
import math
import re
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CANDIDATE_DIR = ROOT / "dataset" / "candidates"
FEATURE_DIR = ROOT / "dataset" / "features"

FEATURE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def safe_number(value):

    try:
        return float(value)
    except:
        return 0.0


def calculate_features(candidate):

    width = safe_number(
        candidate.get("width")
    )

    height = safe_number(
        candidate.get("height")
    )

    aspect_ratio = (
        width / height
        if height > 0
        else 0
    )

    area = width * height

    text_count = int(
        candidate.get(
            "text_count",
            0
        )
    )

    numeric_text_count = int(
        candidate.get(
            "numeric_text_count",
            0
        )
    )

    child_count = int(
        candidate.get(
            "child_count",
            0
        )
    )

    vector_count = int(
        candidate.get(
            "vector_count",
            0
        )
    )

    line_count = int(
        candidate.get(
            "line_count",
            0
        )
    )

    ellipse_count = int(
        candidate.get(
            "ellipse_count",
            0
        )
    )

    rectangle_count = int(
        candidate.get(
            "rectangle_count",
            0
        )
    )

    text_density = (
        text_count / child_count
        if child_count > 0
        else 0
    )

    numeric_density = (
        numeric_text_count / text_count
        if text_count > 0
        else 0
    )

    graphical_count = (
        vector_count
        + line_count
        + ellipse_count
    )

    name = str(
        candidate.get(
            "name",
            ""
        )
    ).lower()

    text_preview = candidate.get(
        "text_preview",
        []
    )

    all_text = " ".join(
        str(x).lower()
        for x in text_preview
    )

    # These are weak semantic features.
    # They should NOT dominate the model.
    has_chart_word = int(
        any(
            word in name
            for word in [
                "chart",
                "graph",
                "analytics",
                "trend",
                "statistics"
            ]
        )
    )

    has_table_word = int(
        any(
            word in name
            for word in [
                "table",
                "list",
                "records"
            ]
        )
    )

    has_kpi_word = int(
        any(
            word in name
            for word in [
                "kpi",
                "metric",
                "stat"
            ]
        )
    )

    has_filter_word = int(
        any(
            word in name
            for word in [
                "filter",
                "dropdown",
                "select"
            ]
        )
    )

    has_percentage = int(
        candidate.get(
            "has_percentage",
            False
        )
    )

    has_date_text = int(
        bool(
            re.search(
                r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b"
                r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
                all_text
            )
        )
    )

    return {
        "dashboard_id": candidate.get(
            "dashboard"
        ),
        "candidate_id": candidate.get(
            "candidate_id"
        ),
        "name": candidate.get(
            "name",
            ""
        ),

        "width": width,
        "height": height,
        "area": area,
        "aspect_ratio": aspect_ratio,

        "child_count": child_count,
        "text_count": text_count,
        "numeric_text_count": numeric_text_count,

        "text_density": text_density,
        "numeric_density": numeric_density,

        "vector_count": vector_count,
        "line_count": line_count,
        "ellipse_count": ellipse_count,
        "rectangle_count": rectangle_count,
        "graphical_count": graphical_count,

        "has_percentage": has_percentage,
        "has_date_text": has_date_text,

        "has_chart_word": has_chart_word,
        "has_table_word": has_table_word,
        "has_kpi_word": has_kpi_word,
        "has_filter_word": has_filter_word
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

            candidate["dashboard"] = (
                dashboard
            )

            rows.append(
                calculate_features(
                    candidate
                )
            )

    if not rows:
        print(
            "No candidates found."
        )
        return

    output_file = (
        FEATURE_DIR /
        "component_features.csv"
    )

    fieldnames = list(
        rows[0].keys()
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        writer.writerows(rows)

    print("=" * 60)
    print("FEATURE EXTRACTION COMPLETE")
    print("=" * 60)
    print(
        f"Candidates: {len(rows)}"
    )
    print(
        f"Output: {output_file}"
    )


if __name__ == "__main__":
    main()