"""
app.py

The FleetWatch website. Flask turns the functions in analysis.py into web pages:
  /          upload a device export CSV
  /dashboard totals and flagged counts by building and cart
  /devices   searchable, filterable table of every laptop

Run it with:  python app.py   then open http://127.0.0.1:5000
"""

from pathlib import Path

import pandas as pd
from flask import Flask, flash, redirect, render_template, request, url_for

from analysis import add_flags, find_missing, load_devices, summarize

app = Flask(__name__)
# flash() messages are stored in a signed cookie, which needs a secret key.
# Fine for a local project; a real deployment would read it from an environment variable.
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
    # pandas reads blank cells as NaN ("no value"); show them as empty text on the page.
    flagged["assigned_teacher"] = flagged["assigned_teacher"].fillna("")
    return flagged