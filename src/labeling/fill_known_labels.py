import pandas as pd

LABEL_FILE = "dataset/labels/component_labels.csv"

# Known labels
LABELS = {
    # Dashboard 01
    ("dashboard_01", "12:54"): "KPI_CARD",
    ("dashboard_01", "12:199"): "CHART",
    ("dashboard_01", "12:75"): "KPI_CARD",
    ("dashboard_01", "12:96"): "KPI_CARD",
    ("dashboard_01", "12:249"): "CHART",
    ("dashboard_01", "12:117"): "KPI_CARD",
    ("dashboard_01", "12:293"): "TABLE",
    ("dashboard_01", "12:138"): "CHART",

    # Dashboard 02
    ("dashboard_02", "42:106"): "KPI_CARD",
    ("dashboard_02", "42:119"): "KPI_CARD",
    ("dashboard_02", "42:135"): "KPI_CARD",
    ("dashboard_02", "42:147"): "KPI_CARD",
    ("dashboard_02", "42:160"): "CHART",
    ("dashboard_02", "42:259"): "OTHER",
    ("dashboard_02", "42:289"): "TABLE",

    # Dashboard 03
    ("dashboard_03", "29:9"): "KPI_CARD",
    ("dashboard_03", "32:10"): "KPI_CARD",
    ("dashboard_03", "40:62"): "KPI_CARD",
    ("dashboard_03", "40:69"): "KPI_CARD",
    ("dashboard_03", "32:40"): "KPI_CARD",
    ("dashboard_03", "35:80"): "KPI_CARD",
    ("dashboard_03", "45:114"): "CHART",
    ("dashboard_03", "45:113"): "OTHER",

    # Dashboard 04
    ("dashboard_04", "1:17"): "KPI_CARD",
    ("dashboard_04", "1:24"): "KPI_CARD",
    ("dashboard_04", "1:45"): "CHART",
    ("dashboard_04", "1:124"): "CHART",
    ("dashboard_04", "1:209"): "CHART",
    ("dashboard_04", "1:382"): "CHART",
    ("dashboard_04", "1:31"): "KPI_CARD",
    ("dashboard_04", "1:38"): "KPI_CARD",
    ("dashboard_04", "1:469"): "TABLE",

    # Dashboard 05
    ("dashboard_05", "52:2618"): "TABLE",
    ("dashboard_05", "72:1474"): "CHART",
    ("dashboard_05", "42:1661"): "CHART",

    # Dashboard 06
    ("dashboard_06", "1:754"): "CHART",
    ("dashboard_06", "1:818"): "KPI_CARD",
    ("dashboard_06", "1:794"): "KPI_CARD",
    ("dashboard_06", "1:899"): "CHART",
    ("dashboard_06", "1:857"): "CHART",
    ("dashboard_06", "1:20"): "CHART",
    ("dashboard_06", "1:1058"): "CHART",

    # Dashboard 07
    ("dashboard_07", "1:5"): "KPI_CARD",
    ("dashboard_07", "1:22"): "KPI_CARD",
    ("dashboard_07", "1:29"): "KPI_CARD",
    ("dashboard_07", "1:39"): "KPI_CARD",
    ("dashboard_07", "1:46"): "KPI_CARD",
    ("dashboard_07", "1:52"): "CHART",
    ("dashboard_07", "1:60"): "CHART",
    ("dashboard_07", "1:89"): "CHART",
    ("dashboard_07", "1:110"): "OTHER",
    ("dashboard_07", "1:409"): "CHART",

    # Dashboard 08
    ("dashboard_08", "1:106"): "KPI_CARD",
    ("dashboard_08", "1:171"): "KPI_CARD",
    ("dashboard_08", "1:190"): "KPI_CARD",
    ("dashboard_08", "1:207"): "KPI_CARD",
    ("dashboard_08", "1:119"): "KPI_CARD",
    ("dashboard_08", "1:145"): "KPI_CARD",
    ("dashboard_08", "1:132"): "KPI_CARD",
    ("dashboard_08", "1:157"): "KPI_CARD",
}


# Read label column explicitly as object/string-compatible
df = pd.read_csv(
    LABEL_FILE,
    dtype={"label": "object"}
)

# Make sure ID columns are strings
df["dashboard_id"] = df["dashboard_id"].astype(str)
df["candidate_id"] = df["candidate_id"].astype(str)

# Fill known labels
for (dashboard_id, candidate_id), label in LABELS.items():

    mask = (
        (df["dashboard_id"] == dashboard_id)
        & (df["candidate_id"] == candidate_id)
    )

    df.loc[mask, "label"] = label


# Save
df.to_csv(LABEL_FILE, index=False)

# Show results
remaining = df["label"].isna().sum()

print("Known labels filled.")
print(f"Remaining unlabeled: {remaining}")

print("\nLabel counts:")
print(df["label"].value_counts(dropna=False))