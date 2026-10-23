"""
app.py

The FleetWatch website. Flask turns the functions in analysis.py into web pages:
  /          upload a device export CSV
  /dashboard totals and flagged counts by building and cart
  /devices   searchable, filterable table of every laptop

"""

from pathlib import Path

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for

from analysis import add_flags, find_missing, load_devices, summarize

app = Flask(__name__)
# flash() messages are stored in a signed cookie, which needs a secret key
app.secret_key = "dev"

DATA_DIR = Path("data")
SAMPLE_EXPORT = DATA_DIR / "laptops.csv"
UPLOADED_EXPORT = DATA_DIR / "uploaded_export.csv"
EXPECTED_INVENTORY = DATA_DIR / "expected_inventory.csv"

REQUIRED_COLUMNS = {"serial_number", "building", "cart", "assigned_teacher",
                    "os_version", "last_sync", "battery_health", "status"}

def current_export_path():
    """Use the most recent upload if there is one, otherwise the sample data."""
    if UPLOADED_EXPORT.exists():
        return UPLOADED_EXPORT
    return SAMPLE_EXPORT


def get_flagged_devices():
    """Load the current export and add the flag columns."""
    devices = load_devices(current_export_path())
    flagged = add_flags(devices)
    # pandas reads blank cells as NaN ("no value"), show them as empty text on the page
    flagged["assigned_teacher"] = flagged["assigned_teacher"].fillna("")
    return flagged

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("export")

        if file is None or file.filename == "":
            flash("Choose a CSV file first.")
            return redirect(url_for("index"))
        if not file.filename.lower().endswith(".csv"):
            flash("That file isn't a CSV.")
            return redirect(url_for("index"))

        uploaded = pd.read_csv(file)
        missing_columns = REQUIRED_COLUMNS - set(uploaded.columns)
        if missing_columns:
            flash(f"That CSV is missing columns: {', '.join(sorted(missing_columns))}")
            return redirect(url_for("index"))

        uploaded.to_csv(UPLOADED_EXPORT, index=False)
        flash(f"Uploaded {file.filename} with {len(uploaded)} laptops.")
        return redirect(url_for("dashboard"))

    return render_template("index.html", source=current_export_path().name)

@app.route("/dashboard")
def dashboard():
    flagged = get_flagged_devices()
    expected = pd.read_csv(EXPECTED_INVENTORY)
    missing = find_missing(flagged, expected)

    totals = {
        "laptops": len(flagged),
        "stale": int(flagged["stale"].sum()),
        "outdated_os": int(flagged["outdated_os"].sum()),
        "low_battery": int(flagged["low_battery"].sum()),
        "missing": len(missing),
        "expected": len(expected),
        "needs_attention": int((flagged["flag_count"] > 0).sum()),
    }
    # reset_index() turns the group names back into a normal column
    # to_dict("records") makes a list of dictionaries, one per row, which Jinja can loop over
    by_building = summarize(flagged, "building").reset_index().to_dict("records")
    by_cart = summarize(flagged, "cart").reset_index().to_dict("records")

    return render_template(
        "dashboard.html",
        totals=totals,
        by_building=by_building,
        by_cart=by_cart,
        missing=missing.to_dict("records"),
    )

@app.route("/devices")
def devices():
    flagged = get_flagged_devices()

    # Read the filters from the URL
    search = request.args.get("search", "").strip()
    cart = request.args.get("cart", "")
    flag = request.args.get("flag", "")

    shown = flagged
    if search:
        matches_serial = shown["serial_number"].str.contains(search, case=False, regex=False)
        matches_teacher = shown["assigned_teacher"].str.contains(search, case=False, regex=False)
        shown = shown[matches_serial | matches_teacher]
    if cart:
        shown = shown[shown["cart"] == cart]
    if flag == "any":
        shown = shown[shown["flag_count"] > 0]
    elif flag in ("stale", "outdated_os", "low_battery"):
        shown = shown[shown[flag]]

    shown = shown.sort_values(["flag_count", "cart"], ascending=[False, True])

    return render_template(
        "devices.html",
        devices=shown.to_dict("records"),
        carts=sorted(flagged["cart"].unique()),
        search=search,
        cart=cart,
        flag=flag,
        total=len(flagged),
    )

if __name__ == "__main__":
    app.run(debug=True)