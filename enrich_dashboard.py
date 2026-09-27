import json

# Load dashboard config
with open("dashboard_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


# -----------------------------------------
# Get components from dashboard config
# -----------------------------------------

if isinstance(config, dict):
    if "components" in config:
        components = config["components"]
    else:
        # Your config may use component IDs as dictionary keys
        components = list(config.values())
else:
    components = config


# -----------------------------------------
# Semantic information
# -----------------------------------------

semantic_info = {

    "12:138": {
        "chart_type": "line",
        "description":
            "12-Month trend of emergency vs inpatient admissions",
        "x_axis": [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ],
        "y_axis": [0, 150, 300, 450, 600]
    },

    "12:290": {
        "table_type": "patient_activity",
        "columns": [
            "Patient Name",
            "Department",
            "Attending Doctor",
            "Status",
            "Admit Date"
        ]
    },

    "12:200": {
        "section_type": "department_performance"
    },

    "12:249": {
        "section_type": "patient_demographics"
    },

    "12:53": {
        "section_type": "kpi_section"
    }
}


# -----------------------------------------
# Add semantic information
# -----------------------------------------

updated = 0

for component in components:

    if not isinstance(component, dict):
        continue

    component_id = component.get("id")

    if component_id in semantic_info:
        component.update(semantic_info[component_id])
        updated += 1


# -----------------------------------------
# Create output
# -----------------------------------------

output = {
    "dashboard_name": "MedPulse",
    "dashboard_title": "Clinical Operations",
    "description":
        "Real-time hospital capacity and performance monitor.",
    "components": components
}


# -----------------------------------------
# Save
# -----------------------------------------

with open(
    "dashboard_config_enriched.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(output, f, indent=2, ensure_ascii=False)


print("================================")
print("Dashboard enrichment complete")
print("================================")
print(f"Components found: {len(components)}")
print(f"Components enriched: {updated}")
print("Output: dashboard_config_enriched.json")
print("================================")