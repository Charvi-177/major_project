import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


SCRIPTS = [
    ROOT / "preprocessing" / "validate_json.py",
    ROOT / "preprocessing" / "build_hierarchy.py",
    ROOT / "preprocessing" / "generate_candidates.py",
    ROOT / "features" / "extract_features.py",
    ROOT / "labeling" / "create_labels.py",
]


def run_script(script):

    print()
    print("=" * 70)
    print(
        f"RUNNING: {script.name}"
    )
    print("=" * 70)

    result = subprocess.run(
        [
            sys.executable,
            str(script)
        ]
    )

    if result.returncode != 0:

        print()
        print(
            f"ERROR: {script.name} failed."
        )

        sys.exit(
            result.returncode
        )


def main():

    print("=" * 70)
    print("FIGMA DASHBOARD PREPROCESSING")
    print("=" * 70)

    for script in SCRIPTS:

        if not script.exists():

            print(
                f"Missing script: {script}"
            )

            sys.exit(1)

        run_script(script)

    print()
    print("=" * 70)
    print("PREPROCESSING COMPLETE")
    print("=" * 70)

    print()
    print(
        "Next step:"
    )

    print(
        "Inspect dataset/candidates/"
    )

    print(
        "Then manually verify component_labels.csv"
    )


if __name__ == "__main__":
    main()