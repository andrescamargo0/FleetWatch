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

MODELS = ["Dell Latitude 3420", "Dell Latitude 3440", ...]
CURRENT_OS = "Windows 11 23H2"
OLD_OS_VERSIONS = ["Windows 11 22H2", "Windows 10 22H2"]

TEACHERS = ["Ms. Rivera", "Mr. Chen", "Ms. Patel", "Mr. Johnson", "Ms. Okafor",
            "Mr. Garcia", "Ms. Kim", "Mr. Brooks", "Ms. Haddad", "Mr.Nguyen",
            "Ms. Russo", "Mr. Alvarez", "Ms. Thompson", "Mr. Diaz", "Ms. Cohen",
            ]

# 6 carts of 30 laptops = 180 laptops. Each cart on one floor.
CARTS = [
    {"carts": "A-Cart-1", "building": "Building A", "floor": 1},
    {"carts": "A-Cart-2", "building": "Building A", "floor": 2},
    {"carts": "A-Cart-3", "building": "Building A", "floor": 3},
    {"carts": "B-Cart-1", "building": "Building B", "floor": 1},
    {"carts": "B-Cart-2", "building": "Building B", "floor": 2},
    {"carts": "B-Cart-4", "building": "Building B", "floor": 4},
]
LAPTOPS_PER_CART = 30
MISSING_COUNT = 6


def make_serial():
    """Return a fake serial number like 'CA-5X8K2P'."""
    chars = string.ascii_uppercase + string.digits
    return "CA-" + "".join(random.choices(chars, k=6))


#random sync dates
if random.random() < 0.10:
    days_ago = random.randint(31,120)
else:
    days_ago = random.randint(0,14)


teacher = "" if random.random() < 0.10 else random.choice(TEACHERS)
status = random.choices(["Active", "In Repair", "Retired"], weights=[90, 7, 3])[0]
"last_sync": (today - timedelta(days=days_ago)).isoformat(),