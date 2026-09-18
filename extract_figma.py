import os
import json
import requests
from dotenv import load_dotenv

# Load .env
load_dotenv()

FIGMA_TOKEN = os.getenv("FIGMA_TOKEN")
FILE_KEY = os.getenv("FIGMA_FILE_KEY")

# Check credentials
if not FIGMA_TOKEN:
    raise ValueError("FIGMA_TOKEN is missing from .env")

if not FILE_KEY:
    raise ValueError("FIGMA_FILE_KEY is missing from .env")


# Figma API endpoint
url = f"https://api.figma.com/v1/files/{FILE_KEY}"

headers = {
    "X-Figma-Token": FIGMA_TOKEN
}

print("Connecting to Figma...")

response = requests.get(url, headers=headers)


# Check response
if response.status_code != 200:
    print("Figma API Error")
    print("Status:", response.status_code)
    print(response.text)
    exit()


data = response.json()

print("Successfully connected to Figma!")
print("File name:", data.get("name"))


# ---------------------------------------------------
# Extract useful information from Figma nodes
# ---------------------------------------------------

def extract_nodes(node, results):

    if not isinstance(node, dict):
        return

    node_type = node.get("type")

    # Basic information
    node_data = {
        "id": node.get("id"),
        "name": node.get("name"),
        "type": node_type
    }

    # Position and size
    bounding_box = node.get("absoluteBoundingBox")

    if bounding_box:

        node_data["x"] = bounding_box.get("x")
        node_data["y"] = bounding_box.get("y")
        node_data["width"] = bounding_box.get("width")
        node_data["height"] = bounding_box.get("height")

    # Text information
    if node_type == "TEXT":

        node_data["text"] = node.get("characters")

        style = node.get("style", {})

        node_data["font_family"] = style.get("fontFamily")
        node_data["font_size"] = style.get("fontSize")
        node_data["font_weight"] = style.get("fontWeight")


    # Store extracted node
    results.append(node_data)


    # Process child nodes recursively
    children = node.get("children", [])

    for child in children:

        extract_nodes(child, results)


# ---------------------------------------------------
# Start extraction
# ---------------------------------------------------

all_nodes = []

document = data.get("document", {})

pages = document.get("children", [])


for page in pages:

    extract_nodes(page, all_nodes)


# ---------------------------------------------------
# Save extracted data
# ---------------------------------------------------

output = {

    "file_name": data.get("name"),

    "total_nodes": len(all_nodes),

    "nodes": all_nodes
}


with open(
    "figma_data.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        indent=4,
        ensure_ascii=False
    )


print()
print("--------------------------------")
print("EXTRACTION COMPLETE")
print("--------------------------------")
print("File:", data.get("name"))
print("Nodes extracted:", len(all_nodes))
print("Output: figma_data.json")
print("--------------------------------")