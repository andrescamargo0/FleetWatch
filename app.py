"""
app.py

The FleetWatch website. Flask turns the functions in analysis.py into web pages:
  /          upload a device export CSV
  /dashboard totals and flagged counts by building and cart
  /devices   searchable, filterable table of every laptop

"""
import os
import re
from pathlib import Path

import pandas as pd
from flask import Flask, Response, flash, redirect, render_template, request, url_for

from analysis import add_flags, find_missing, load_devices, summarize
from database import get_assignments, init_db, set_assignment

app = Flask(__name__)
# flash() messages are stored in a signed cookie, which needs a secret key
app.secret_key = os.environ.get("SECRET_KEY", "dev")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_EXPORT = DATA_DIR / "laptops.csv"
UPLOADED_EXPORT = DATA_DIR / "uploaded_export.csv"
EXPECTED_INVENTORY = DATA_DIR / "expected_inventory.csv"

REQUIRED_COLUMNS = {"serial_number", "building", "cart", "assigned_teacher",
                    "os_version", "last_sync", "battery_health", "status"}

FLAG_NAMES = {"stale": "Stale", "outdated_os": "Outdate OS", "low_battery": "Low battery"}

init_db()

def current_export_path():
    """Use the most recent upload if there is one, otherwise the sample data."""
    if UPLOADED_EXPORT.exists():
        return UPLOADED_EXPORT
    return SAMPLE_EXPORT


def current_export_path():
    """Use the most recent upload if there is one, otherwise the sample data."""
    if UPLOADED_EXPORT.exists():
        return UPLOADED_EXPORT
    return SAMPLE_EXPORT


def get_flagged_devices():
    """Load the current export, apply saved teacher assignments, and add the flag columns."""
    devices = load_devices(current_export_path())
    devices["assigned_teacher"] = devices["assigned_teacher"].fillna("")
    # A saved assignment wins over whatever the export says.
    # map() looks up each serial in the dictionary; serials with nothing saved become NaN,
    # and fillna() puts the export's teacher back in for those.
    saved = get_assignments()
    devices["assigned_teacher"] = devices["serial_number"].map(saved).fillna(devices["assigned_teacher"])

    return add_flags(devices)

def simplify(text):
    """Lowercase and keep only letters and digits, so "Ms. Rivera", "ms rivera", and "ms.rivera" all match."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def filter_devices(flagged, search, building, cart, flag):
    """Keep only the laptops that match the filters. Used by the table and the CSV download."""
    shown = flagged
    search = simplify(search)
    if search:
        # Simplify every serial and teacher the same way, then look for the search inside them.
        serials = shown["serial_number"].map(simplify)
        teachers = shown["assigned_teacher"].map(simplify)
        shown = shown[serials.str.contains(search, regex=False) | teachers.str.contains(search, regex=False)]
    if building:
        shown = shown[shown["building"] == building]
    if cart:
        shown = shown[shown["cart"] == cart]
    if flag == "any":
        shown = shown[shown["flag_count"] > 0]
    elif flag in FLAG_NAMES:
        shown = shown[shown[flag]]
    return shown.sort_values(["flag_count", "cart"], ascending=[False, True])

def read_filters():
    """Read the filters from the URL, e.g. /devices?search=rivera&cart=A-Cart-1&flag=stale"""
    return {
        "search": request.args.get("search", "").strip(),
        "building": request.args.get("building", ""),
        "cart": request.args.get("cart", ""),
        "flag": request.args.get("flag", ""),
    }

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
    # reset_index() turns the group names back into a normal column;
    # to_dict("records") makes a list of dictionaries, one per row, which Jinja can loop over.
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
    filters = read_filters()
    shown = filter_devices(flagged, **filters)

    return render_template(
        "devices.html",
        devices = shown.to_dict("records"),
        buildings=sorted(flagged["building"].unique()),
        carts = sorted(flagged["cart"].unique()),
        teachers = sorted(t for t in flagged["assigned_teacher"].unique() if t),
        total = len(flagged),
        **filters,
    )

@app.route("/devices/<serial>/assign", methods=["POST"])
def assign(serial):
    teacher = request.form.get("teacher", "").strip()
    set_assignment(serial, teacher)
    if teacher:
        flash(f"{serial} is now assigned to {teacher},")
    else:
        flash(f"{serial} is now unassigned.")
    return redirect(request.referrer or url_for("devices"))

@app.route("/export.csv")
def export_csv():
    shown = filter_devices(get_flagged_devices(), **read_filters())

    # One readable "problems" column instead of three True/False columns.
    shown = shown.copy()
    shown["problems"] = shown.apply(
        lambda row: ", ".join(name for col, name in FLAG_NAMES.items() if row[col]),
        axis=1,
    )
    columns = ["serial_number", "building", "cart", "assigned_teacher",
               "os_version", "last_sync", "battery_health", "status", "problems"]
    csv_text = shown[columns].to_csv(index=False, date_format="%Y-%m-%d")

    #attachment tells the browser to download the file instead of showing it.
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=fleetwatch_devices.csv"},
    )


if __name__ == "__main__":
    app.run(debug=True)