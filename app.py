import os
import json
from flask import Flask, render_template, jsonify, request
import openpyxl

app = Flask(__name__)


def parse_allergen_matrix(filepath: str):
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb["Master List"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]
    # Indices 0=Section, 1=Items, 2–22=allergen cols, 23=Other/Notes
    allergen_cols = headers[2:23]   # 21 allergen columns
    notes_idx = 23

    items = []
    current_section = ""

    for row in rows[1:]:
        # Skip entirely blank rows
        if not any(v for v in row if v is not None):
            continue

        section_val = row[0]
        item_val = row[1]

        if section_val is not None and str(section_val).strip():
            current_section = str(section_val).strip()

        if item_val is None or not str(item_val).strip():
            continue

        allergens = {}
        for i, allergen in enumerate(allergen_cols):
            cell = row[i + 2]
            allergens[allergen] = str(cell).strip() if cell is not None else ""

        notes = ""
        if notes_idx < len(row) and row[notes_idx] is not None:
            notes = str(row[notes_idx]).strip()

        items.append(
            {
                "section": current_section,
                "name": str(item_val).strip(),
                "allergens": allergens,
                "notes": notes,
            }
        )

    return allergen_cols, items


# Parse once at startup
_data_path = os.path.join(
    os.path.dirname(__file__), "data", "Miru_Allergen_Matrix_9_2_26.xlsx"
)
ALLERGEN_COLS, MENU_ITEMS = parse_allergen_matrix(_data_path)

# Build ordered item map for O(1) lookups
ITEM_MAP = {item["name"]: item for item in MENU_ITEMS}

# Group names by section (preserving section order)
SECTIONS: dict[str, list[str]] = {}
for _item in MENU_ITEMS:
    sec = _item["section"]
    if sec not in SECTIONS:
        SECTIONS[sec] = []
    SECTIONS[sec].append(_item["name"])


@app.route("/")
def index():
    return render_template(
        "index.html",
        allergens_json=json.dumps(ALLERGEN_COLS),
        sections_json=json.dumps(SECTIONS),
    )


@app.route("/api/grid", methods=["POST"])
def get_grid():
    data = request.get_json(force=True)
    selected_items: list[str] = data.get("items", [])
    selected_allergens: list[str] = data.get("allergens", [])

    rows = []
    for name in selected_items:
        item = ITEM_MAP.get(name)
        if not item:
            continue
        rows.append(
            {
                "name": item["name"],
                "section": item["section"],
                "notes": item["notes"],
                "values": {
                    a: item["allergens"].get(a, "")
                    for a in selected_allergens
                },
            }
        )

    return jsonify({"rows": rows, "columns": selected_allergens})


@app.route("/menu")
def menu():
    return render_template(
        "menu.html",
        allergens_json=json.dumps(ALLERGEN_COLS),
    )


@app.route("/api/menu", methods=["POST"])
def get_menu():
    data = request.get_json(force=True)
    selected_allergens: list[str] = data.get("allergens", [])

    clear_items, mod_items, fail_items = [], [], []

    for item in MENU_ITEMS:
        vals = {a: item["allergens"].get(a, "") for a in selected_allergens}
        non_empty = {a: v for a, v in vals.items() if v}

        entry = {
            "section": item["section"],
            "name": item["name"],
            "notes": item["notes"],
            "flags": non_empty,
        }

        if any(v == "X" for v in non_empty.values()):
            fail_items.append(entry)
        elif non_empty:
            mod_items.append(entry)
        else:
            clear_items.append(entry)

    return jsonify({
        "clear": clear_items,
        "mod":   mod_items,
        "fail":  fail_items,
        "allergens": selected_allergens,
        "total": len(MENU_ITEMS),
    })


@app.route("/api/data")
def get_data():
    """Return full dataset as JSON (for debugging or future use)."""
    return jsonify({"items": MENU_ITEMS, "allergens": ALLERGEN_COLS})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
