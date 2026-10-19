"""
generate_data.py
...
"""

import csv
import random
import string
from datetime import date, timedelta
from pathlib import Path

random.seed(21)  #fixed seed so the data is the same every run 

#constants, lists, and dictionaries at top
DATA_DIR = Path("data")

MODELS = ["Dell Latitude 3420", "Dell Latitude 3440", "Lenovo ThinkPad 11e", "HP ProBook 440"]
CURRENT_OS = "Windows 11 23H2"
OLD_OS_VERSIONS = ["Windows 11 22H2", "Windows 10 22H2"]

TEACHERS = ["Ms. Rivera", "Mr. Chen", "Ms. Patel", "Mr. Johnson", "Ms. Okafor",
            "Mr. Garcia", "Ms. Kim", "Mr. Brooks", "Ms. Haddad", "Mr.Nguyen",
            "Ms. Russo", "Mr. Alvarez", "Ms. Thompson", "Mr. Diaz", "Ms. Cohen",
            ]

# 6 carts of 30 laptops = 180 laptops. Each cart on one floor.
CARTS = [
    {"cart": "A-Cart-1", "building": "Building A", "floor": 1},
    {"cart": "A-Cart-2", "building": "Building A", "floor": 2},
    {"cart": "A-Cart-3", "building": "Building A", "floor": 3},
    {"cart": "B-Cart-1", "building": "Building B", "floor": 1},
    {"cart": "B-Cart-2", "building": "Building B", "floor": 2},
    {"cart": "B-Cart-4", "building": "Building B", "floor": 4},
]

LAPTOPS_PER_CART = 30
MISSING_COUNT = 6


def make_serial():
    """Return a fake serial number like 'CA-5X8K2P'."""
    chars = string.ascii_uppercase + string.digits
    return "CA-" + "".join(random.choices(chars, k=6))

def make_laptop(cart_info):
    """Build one laptop as a dictionaru (one row of the CSV)."""
    today = date.today()


    #Most laptops synced in the last 2 weeks; about 10% are stale
    if random.random() < 0.10:
        days_ago = random.randint(31,120)
    else:
        days_ago = random.randint(0,14)

    #About 15% run an outdated OS
    if random.random() < 0.15:
        os_version = random.choice(OLD_OS_VERSIONS)
    else:
        os_version = CURRENT_OS

    #Most batteries are healthy; about 12% are below 60%
    if random.random() <0.12:
        battery = random.randint(25,59)
    else:
        battery = random.randint(60,100)

    #About 10% have no teacher assigned
    teacher = "" if random.random() < 0.10 else random.choice(TEACHERS)
    status = random.choices(["Active", "In Repair", "Retired"], weights=[90, 7, 3])[0]

    return {
        "serial_number": make_serial(),
        "model": random.choice(MODELS),
        "building": cart_info["building"],
        "floor": cart_info["floor"],
        "cart": cart_info["cart"],
        "assigned_teacher": teacher,
        "os_version": os_version,
        "last_sync": (today - timedelta(days=days_ago)).isoformat(),
        "battery_health": battery,
        "status": status,
    }

def write_csv(path, rows, columns):
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

def main():
    DATA_DIR.mkdir(exist_ok=True)

    laptops = []
    for cart_info in CARTS:
        for _ in range(LAPTOPS_PER_CART):
            laptops.append(make_laptop(cart_info))

    expected = [
        {"serial_number": l["serial_number"], "cart": l["cart"], "model": l["model"]}
        for l in laptops
    ]

    missing = random.sample(laptops, MISSING_COUNT)
    export = [l for l in laptops if l not in missing]

    write_csv(DATA_DIR / "laptops.csv", export, list(laptops[0].keys()))
    write_csv(DATA_DIR / "expected_inventory.csv", expected, ["serial_number", "cart", "model"])


    print(f"Write {len(export)} laptops to data/laptops.csv")
    print(f"Wrote {len(expected)} laptops to data/expected_inventory.csv")
    print(f"{MISSING_COUNT} laptops are missing from the export on purpose")

if __name__ == "__main__":
    main()