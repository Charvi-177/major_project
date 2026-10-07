import pandas as pd
from pathlib import Path

FEATURE_FILE = "dataset/features/component_features.csv"
LABEL_FILE = "dataset/labels/component_labels.csv"
OUTPUT_FILE = "dataset/features/training_dataset.csv"

# Load data
features = pd.read_csv(FEATURE_FILE)
labels = pd.read_csv(LABEL_FILE)

# Columns used to identify rows
ID_COLS = ["dashboard_id", "candidate_id"]

# Merge features and labels
df = features.merge(
    labels[ID_COLS + ["label"]],
    on=ID_COLS,
    how="inner"
)

# Features used by the model
FEATURE_COLS = [
    "width",
    "height",
    "area",
    "aspect_ratio",
    "child_count",
    "text_count",
    "numeric_text_count",
    "text_density",
    "numeric_density",
    "vector_count",
    "line_count",
    "ellipse_count",
    "rectangle_count",
    "graphical_count",
    "has_percentage",
    "has_date_text",
    "has_chart_word",
    "has_table_word",
    "has_kpi_word",
    "has_filter_word",
]

# Check for missing values
missing = df[FEATURE_COLS].isna().sum()

print("Dataset shape:", df.shape)
print("Missing feature values:", missing.sum())

# Check labels
print("\nLabel distribution:")
print(df["label"].value_counts())

# Create final training dataset
training_df = df[ID_COLS + FEATURE_COLS + ["label"]]

Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

training_df.to_csv(OUTPUT_FILE, index=False)

print("\nSaved:", OUTPUT_FILE)
print("Training rows:", len(training_df))
print("Model features:", len(FEATURE_COLS))