import json
import os
import re


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

DASHBOARDS_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "dashboards"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "candidates"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_name(name):
    """
    Normalize Figma node names for easier matching.
    """
    if not name:
        return ""

    name = str(name).lower().strip()
    name = re.sub(r"[_\-]+", " ", name)
    name = re.sub(r"\s+", " ", name)

    return name


def is_container(node):
    """
    Nodes that can contain dashboard components.
    """
    return node.get("type") in {
        "FRAME",
        "COMPONENT",
        "COMPONENT_SET",
        "INSTANCE",
        "GROUP",
        "SECTION"
    }


def is_root_or_layout(node):
    """
    Remove dashboard/page/layout wrappers.
    """
    name = normalize_name(node.get("name"))

    layout_patterns = [
        "healthcare dashboard",
        "health dashboard",
        "medical dashboard",
        "dashboard",
        "main content",
        "content area",
        "dashboard content",
        "page",
        "sidebar",
        "side bar",
        "header",
        "footer",
        "navigation",
        "navbar",
        "nav bar",
        "menu",
        "topbar",
        "top bar",
    ]

    for pattern in layout_patterns:
        if name == pattern:
            return True

    return False


# ============================================================
# INTERNAL COMPONENT DETECTION
# ============================================================

def is_internal_component(node):
    """
    Detect nodes that are normally internal pieces of a
    larger dashboard component.

    Examples:
        grid-lines
        plot-area
        axis
        legend
        table-header
        table-header-title
        row-xxx
        demographics-body
        dept-list
        nav-list
    """

    name = normalize_name(node.get("name"))

    internal_patterns = [

        # -----------------------------
        # Chart internals
        # -----------------------------
        "grid lines",
        "grid line",
        "plot area",
        "plot-area",
        "chart and y axis",
        "chart with axes",
        "y axis",
        "x axis",
        "axis",
        "axes",
        "chart line",
        "chart lines",
        "chart body",
        "chart content",

        # -----------------------------
        # Chart legends
        # -----------------------------
        "legend",
        "legend item",
        "legend items",

        # -----------------------------
        # Table internals
        # -----------------------------
        "table header",
        "table header title",
        "header title",
        "table body",
        "table footer",
        "table pagination",
        "pagination",
        "table row",
        "table column",
        "column header",

        # -----------------------------
        # Card internals
        # -----------------------------
        "card body",
        "card header",
        "card footer",
        "card content",

        # -----------------------------
        # Department internals
        # -----------------------------
        "dept list",
        "department list",
        "department body",
        "department content",

        # -----------------------------
        # Demographics internals
        # -----------------------------
        "demographics body",
        "demographics content",
        "demographics legend",

        # -----------------------------
        # Navigation
        # -----------------------------
        "nav list",
        "navigation list",
        "sidebar footer",
        "sidebar header",

        # -----------------------------
        # Generic layout internals
        # -----------------------------
        "content",
        "body",
        "inner",
        "inner content",
        "inner container",
    ]

    for pattern in internal_patterns:
        if pattern in name:
            return True

    # Repeated activity/table rows such as:
    # row-eleanor-vance
    # row-marcus-sterling
    # row-thomas-miller
    if name.startswith("row "):
        return True

    # Common wrapper rows
    wrapper_names = {
        "kpis row",
        "split row",
        "main row",
        "content row",
        "dashboard row",
        "top row",
        "bottom row",
    }

    if name in wrapper_names:
        return True

    return False


# ============================================================
# SIDEBAR / UI ELEMENT DETECTION
# ============================================================

def is_navigation_or_sidebar(node):
    """
    Remove navigation/sidebar UI elements.

    These are not report/dashboard data components.
    """

    name = normalize_name(node.get("name"))

    navigation_patterns = [
        "nav",
        "navigation",
        "sidebar",
        "side bar",
        "menu",
        "profile",
        "user profile",
        "settings",
        "logout",
        "log out",
        "support",
        "help",
        "logo",
        "brand",
    ]

    # Exact / partial semantic names
    for pattern in navigation_patterns:

        if name == pattern:
            return True

        if name.startswith(pattern + " "):
            return True

        if name.endswith(" " + pattern):
            return True

    # Specific sidebar UI
    if "sidebar" in name:
        return True

    return False


# ============================================================
# WEAK SEMANTIC CHECKS
# ============================================================

def has_keyword(name, keywords):
    """
    Check whether a normalized name contains one of the
    provided semantic keywords.
    """

    name = normalize_name(name)

    for keyword in keywords:
        if keyword in name:
            return True

    return False


def is_meaningful_named_component(node):
    """
    Strong semantic names that usually represent an actual
    dashboard/report component.
    """

    name = normalize_name(node.get("name"))

    if not name:
        return False

    meaningful_keywords = [

        # KPI
        "kpi",
        "metric",
        "stat",
        "statistics",

        # Charts
        "chart",
        "graph",
        "trend",
        "overview",
        "analytics",
        "analysis",
        "survey",
        "performance",
        "demographics",
        "admissions",
        "appointments",
        "revenue",
        "payments",

        # Tables / lists
        "table",
        "activity",
        "activities",
        "patient data",
        "patient list",
        "doctor list",
        "admit patient",

        # Healthcare sections
        "department",
        "patient statistics",
        "hospital overview",

        # Calendar / schedule
        "schedule",
        "calendar",
        "appointment",

        # Filters
        "filter",
        "date picker",
        "dropdown",
        "select",
        "search",
    ]

    return has_keyword(name, meaningful_keywords)


# ============================================================
# DIMENSION FILTER
# ============================================================

def is_dashboard_sized(node):
    """
    Prevent the entire dashboard/root frame from becoming
    a candidate.
    """

    width = node.get("width", 0) or 0
    height = node.get("height", 0) or 0

    # Very large frames are normally page/dashboard wrappers.
    if width >= 1200 and height >= 700:
        return True

    return False


# ============================================================
# STRUCTURAL SCORE
# ============================================================

def calculate_candidate_score(node, all_nodes):
    """
    Calculate a structural/semantic score.

    This is NOT the final ML classification.

    It is only used to find reasonable component boundaries.
    """

    score = 0

    name = normalize_name(node.get("name", ""))

    width = node.get("width", 0) or 0
    height = node.get("height", 0) or 0

    children = [
        n for n in all_nodes
        if n.get("parent_id") == node.get("id")
    ]

    child_count = len(children)

    text_nodes = [
        n for n in children
        if n.get("type") == "TEXT"
    ]

    text_count = len(text_nodes)

    numeric_text_count = 0

    has_percentage = False
    has_date_text = False

    for child in text_nodes:

        text = str(child.get("text", ""))

        if re.search(r"\d", text):
            numeric_text_count += 1

        if "%" in text:
            has_percentage = True

        if re.search(
            r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
            text.lower()
        ):
            has_date_text = True

    vectors = [
        n for n in children
        if n.get("type") == "VECTOR"
    ]

    lines = [
        n for n in children
        if n.get("type") == "LINE"
    ]

    ellipses = [
        n for n in children
        if n.get("type") == "ELLIPSE"
    ]

    rectangles = [
        n for n in children
        if n.get("type") == "RECTANGLE"
    ]

    # --------------------------------------------------------
    # Semantic name score
    # --------------------------------------------------------

    if "kpi" in name:
        score += 6

    if any(
        word in name
        for word in [
            "chart",
            "graph",
            "trend",
            "overview",
            "analytics",
            "survey",
            "demographics",
            "admissions",
            "performance"
        ]
    ):
        score += 4

    if any(
        word in name
        for word in [
            "table",
            "activity",
            "activities",
            "patient data",
            "patient list",
            "payments"
        ]
    ):
        score += 4

    if any(
        word in name
        for word in [
            "filter",
            "date picker",
            "dropdown",
            "select"
        ]
    ):
        score += 4

    # --------------------------------------------------------
    # Numeric/text signals
    # --------------------------------------------------------

    if numeric_text_count >= 1:
        score += 1

    if numeric_text_count >= 3:
        score += 1

    if has_percentage:
        score += 1

    # --------------------------------------------------------
    # Structural signals
    # --------------------------------------------------------

    if child_count >= 5:
        score += 1

    if child_count >= 15:
        score += 1

    if child_count >= 30:
        score += 1

    # --------------------------------------------------------
    # Graphic signals
    # --------------------------------------------------------

    if len(lines) >= 5:
        score += 2

    if len(ellipses) >= 2:
        score += 2

    if len(rectangles) >= 5:
        score += 1

    if len(vectors) >= 3:
        score += 1

    # --------------------------------------------------------
    # Reasonable component dimensions
    # --------------------------------------------------------

    area = width * height

    if area >= 20_000:
        score += 1

    if area >= 50_000:
        score += 1

    return score


# ============================================================
# CANDIDATE INFORMATION
# ============================================================

def build_candidate(node, all_nodes, dashboard_name):
    """
    Convert raw Figma node into candidate record.
    """

    children = [
        n for n in all_nodes
        if n.get("parent_id") == node.get("id")
    ]

    text_nodes = [
        n for n in children
        if n.get("type") == "TEXT"
    ]

    numeric_text_count = 0
    has_percentage = False
    has_date_text = False

    text_preview = []

    for text_node in text_nodes:

        text = str(
            text_node.get("text", "")
        ).strip()

        if not text:
            continue

        if len(text_preview) < 10:
            text_preview.append(text)

        if re.search(r"\d", text):
            numeric_text_count += 1

        if "%" in text:
            has_percentage = True

        if re.search(
            r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
            text.lower()
        ):
            has_date_text = True

    vector_count = sum(
        1 for n in children
        if n.get("type") == "VECTOR"
    )

    line_count = sum(
        1 for n in children
        if n.get("type") == "LINE"
    )

    ellipse_count = sum(
        1 for n in children
        if n.get("type") == "ELLIPSE"
    )

    rectangle_count = sum(
        1 for n in children
        if n.get("type") == "RECTANGLE"
    )

    graphical_count = (
        vector_count
        + line_count
        + ellipse_count
        + rectangle_count
    )

    width = node.get("width", 0) or 0
    height = node.get("height", 0) or 0

    area = width * height

    aspect_ratio = (
        width / height
        if height
        else 0
    )

    name = normalize_name(
        node.get("name", "")
    )

    candidate = {
        "candidate_id": node.get("id"),
        "name": node.get("name"),
        "type": node.get("type"),
        "parent_id": node.get("parent_id"),

        "x": node.get("x", 0),
        "y": node.get("y", 0),

        "width": width,
        "height": height,

        "area": area,
        "aspect_ratio": aspect_ratio,

        "child_count": len(children),
        "text_count": len(text_nodes),
        "numeric_text_count": numeric_text_count,

        "has_percentage": has_percentage,
        "has_date_text": has_date_text,

        "vector_count": vector_count,
        "line_count": line_count,
        "ellipse_count": ellipse_count,
        "rectangle_count": rectangle_count,
        "graphical_count": graphical_count,

        "text_preview": text_preview,

        "dashboard": dashboard_name,
    }

    candidate["candidate_score"] = calculate_candidate_score(
        node,
        all_nodes
    )

    # --------------------------------------------------------
    # Semantic flags
    # --------------------------------------------------------

    candidate["has_chart_word"] = any(
        word in name
        for word in [
            "chart",
            "graph",
            "trend",
            "overview",
            "analytics",
            "survey",
            "demographics",
            "admissions",
            "performance"
        ]
    )

    candidate["has_table_word"] = any(
        word in name
        for word in [
            "table",
            "activity",
            "activities",
            "patient data",
            "patient list",
            "payments"
        ]
    )

    candidate["has_kpi_word"] = any(
        word in name
        for word in [
            "kpi",
            "metric",
            "stat"
        ]
    )

    candidate["has_filter_word"] = any(
        word in name
        for word in [
            "filter",
            "date picker",
            "dropdown",
            "select"
        ]
    )

    return candidate


# ============================================================
# REMOVE DUPLICATE / NESTED CANDIDATES
# ============================================================

def remove_internal_nested_candidates(
    candidates,
    node_map
):
    """
    Remove candidates that are clearly children/internal
    pieces of another selected candidate.

    Important:
        We do NOT blindly remove every descendant.

    For example:

        kpis-row
            KPI card 1
            KPI card 2
            KPI card 3

    We want the KPI cards.

    But:

        demographics-card
            demographics-body
            demographics-legend
            donut-chart-container

    We want demographics-card only.
    """

    candidate_ids = {
        c["candidate_id"]
        for c in candidates
    }

    result = []

    # Explicit internal names should always be removed.
    for candidate in candidates:

        node_id = candidate["candidate_id"]

        node = node_map.get(node_id)

        if not node:
            continue

        if is_internal_component(node):
            continue

        result.append(candidate)

    # --------------------------------------------------------
    # Remove candidates inside another high-level component
    # when they are obvious structural children.
    # --------------------------------------------------------

    final_result = []

    for candidate in result:

        node_id = candidate["candidate_id"]
        node = node_map.get(node_id)

        if not node:
            continue

        name = normalize_name(
            node.get("name", "")
        )

        parent_id = node.get("parent_id")

        remove = False

        while parent_id:

            parent = node_map.get(parent_id)

            if not parent:
                break

            parent_name = normalize_name(
                parent.get("name", "")
            )

            # If parent itself is a meaningful high-level
            # component, decide whether this child is internal.
            if parent_id in candidate_ids:

                # Keep actual table inside activity-card only
                # when the parent is a generic wrapper.
                if (
                    "activity" in parent_name
                    and "table" in name
                ):
                    remove = False

                # Keep KPI cards inside kpis-row.
                elif (
                    parent_name == "kpis row"
                    and "kpi" in name
                ):
                    remove = False

                # Keep department/demographics cards inside
                # split-row.
                elif parent_name == "split row":
                    remove = False

                # Otherwise a child of a selected high-level
                # component is probably an internal element.
                else:
                    remove = True

                break

            parent_id = parent.get("parent_id")

        if not remove:
            final_result.append(candidate)

    return final_result


# ============================================================
# MAIN CANDIDATE GENERATION
# ============================================================

def generate_candidates_for_dashboard(
    dashboard_dir
):

    dashboard_name = os.path.basename(
        dashboard_dir
    )

    input_file = os.path.join(
        dashboard_dir,
        "figma_data.json"
    )

    if not os.path.exists(input_file):

        print(
            f"[SKIP] {dashboard_name}: "
            "figma_data.json not found"
        )

        return

    # --------------------------------------------------------
    # Load JSON
    # --------------------------------------------------------

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    nodes = data.get("nodes", [])

    if not nodes:

        print(
            f"[SKIP] {dashboard_name}: "
            "No nodes found"
        )

        return

    # --------------------------------------------------------
    # Build node map
    # --------------------------------------------------------

    node_map = {
        node.get("id"): node
        for node in nodes
        if node.get("id")
    }

    # --------------------------------------------------------
    # First-pass candidate selection
    # --------------------------------------------------------

    candidates = []

    for node in nodes:

        # Only containers can represent high-level
        # dashboard components.
        if not is_container(node):
            continue

        # Remove root/dashboard/layout frames.
        if is_root_or_layout(node):
            continue

        # Remove huge page-sized frames.
        if is_dashboard_sized(node):
            continue

        # Remove navigation/sidebar UI.
        if is_navigation_or_sidebar(node):
            continue

        # Remove known internal elements.
        if is_internal_component(node):
            continue

        width = node.get("width", 0) or 0
        height = node.get("height", 0) or 0

        # Ignore extremely tiny containers.
        if width < 40 or height < 30:
            continue

        # ----------------------------------------------------
        # Build candidate
        # ----------------------------------------------------

        candidate = build_candidate(
            node,
            nodes,
            dashboard_name
        )

        score = candidate["candidate_score"]

        meaningful_name = is_meaningful_named_component(
            node
        )

        # ----------------------------------------------------
        # Candidate acceptance
        # ----------------------------------------------------

        accept = False

        # Strong semantic component name.
        if meaningful_name and score >= 4:
            accept = True

        # Strong structural component.
        elif score >= 7:
            accept = True

        # KPI cards should be retained even if structural
        # score is slightly lower.
        elif "kpi" in normalize_name(
            node.get("name", "")
        ):
            accept = True

        if not accept:
            continue

        candidates.append(candidate)

    # --------------------------------------------------------
    # Remove nested/internal candidates
    # --------------------------------------------------------

    candidates = remove_internal_nested_candidates(
        candidates,
        node_map
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique = {}

    for candidate in candidates:

        candidate_id = candidate["candidate_id"]

        if candidate_id not in unique:

            unique[candidate_id] = candidate

        else:

            # Keep higher scoring version.
            if (
                candidate["candidate_score"]
                > unique[candidate_id]["candidate_score"]
            ):
                unique[candidate_id] = candidate

    candidates = list(
        unique.values()
    )

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: (
            x.get("y", 0),
            x.get("x", 0)
        )
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output_file = os.path.join(
        OUTPUT_DIR,
        f"{dashboard_name}_candidates.json"
    )

    output = {
        "dashboard": dashboard_name,
        "candidate_count": len(candidates),
        "candidates": candidates
    }

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

    # --------------------------------------------------------
    # Console output
    # --------------------------------------------------------

    print(
        f"[DONE] {dashboard_name}: "
        f"{len(candidates)} candidates"
    )

    for candidate in candidates:

        print(
            f"   - "
            f"{candidate['candidate_id']} | "
            f"{candidate['name']} | "
            f"score={candidate['candidate_score']}"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("GENERATING DASHBOARD COMPONENT CANDIDATES")
    print("=" * 60)

    if not os.path.exists(DASHBOARDS_DIR):

        print(
            f"[ERROR] Dashboard directory not found:\n"
            f"{DASHBOARDS_DIR}"
        )

        return

    dashboard_folders = sorted(
        [
            folder
            for folder in os.listdir(
                DASHBOARDS_DIR
            )
            if os.path.isdir(
                os.path.join(
                    DASHBOARDS_DIR,
                    folder
                )
            )
        ]
    )

    if not dashboard_folders:

        print(
            "[ERROR] No dashboard folders found."
        )

        return

    print(
        f"Found {len(dashboard_folders)} dashboards."
    )

    print()

    for dashboard in dashboard_folders:

        dashboard_dir = os.path.join(
            DASHBOARDS_DIR,
            dashboard
        )

        generate_candidates_for_dashboard(
            dashboard_dir
        )

    print()
    print("=" * 60)
    print("CANDIDATE GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()