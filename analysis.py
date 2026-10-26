"""
analysis.py

The "brain" of FleetWatch: functions that read the device export,
flag problem laptops, and summarize them by building and cart.

"""


import pandas as pd

# The rules for what counts as a problem. Kept at the top so they're easy to change.
STALE_AFTER_DAYS = 30
CURRENT_OS = "Windows 11 23H2"
LOW_BATTERY_THRESHOLD = 60

def load_devices(path):
    """Read the device export CSV into a DataFrame."""
    df = pd.read_csv(path)
    # Turn the last_sync text into real dates
    df["last_sync"] = pd.to_datetime(df["last_sync"])
    return df

def flag_stale(df, today=None):
    """An export is a snapshot, so by default "today" is the newest sync date in the
    export itself, otherwise an old export would make
    every laptop look stale.
    """
    if today is None:
        today = df["last_sync"].max()
    days_since_sync = (pd.Timestamp(today) - df["last_sync"]).dt.days
    return days_since_sync > STALE_AFTER_DAYS


def flag_outdated_os(df):
    """True for laptops not running the current OS version."""
    return df["os_version"] != CURRENT_OS


def flag_low_battery(df):
    """True for laptops whose battery health is below the threshold."""
    return df["battery_health"] < LOW_BATTERY_THRESHOLD

def find_missing(df, expected):
    """Return the laptops in the expected inventory that are NOT in the export."""
    in_export = expected["serial_number"].isin(df["serial_number"])
    return expected[~in_export]

def add_flags(df, today=None):
    """Return a copy of df with one True/False column per flag, plus a total."""
    df = df.copy()
    df["stale"] = flag_stale(df, today)
    df["outdated_os"] = flag_outdated_os(df)
    df["low_battery"] = flag_low_battery(df)
    # True counts as 1 and False as 0, so adding the columns counts the problems.
    df["flag_count"] = df["stale"].astype(int) + df["outdated_os"].astype(int) + df["low_battery"].astype(int)
    return df

def summarize(df, by):
    """Count total and flagged laptops for each value of a column """
    return df.groupby(by).agg(
        total=("serial_number", "count"),
        stale=("stale", "sum"),
        outdated_os=("outdated_os", "sum"),
        low_battery=("low_battery", "sum"),
        any_flag=("flag_count", lambda counts: (counts > 0).sum()),
    )

def main():
    devices = load_devices("data/laptops.csv")
    expected = pd.read_csv("data/expected_inventory.csv")

    flagged = add_flags(devices)
    missing = find_missing(devices, expected)

    print(f"Laptops in export: {len(flagged)}")
    print(f"Stale (>{STALE_AFTER_DAYS} days): {flagged['stale'].sum()}")
    print(f"Outdated OS:       {flagged['outdated_os'].sum()}")
    print(f"Low battery (<{LOW_BATTERY_THRESHOLD}%): {flagged['low_battery'].sum()}")
    print(f"Missing from export: {len(missing)}")

    print("\nBy building:")
    print(summarize(flagged, "building"))

    print("\nBy cart:")
    print(summarize(flagged, "cart"))

    print("\nMissing laptops:")
    print(missing.to_string(index=False))

    print("\nWorst laptops (2+ problems):")
    worst = flagged[flagged["flag_count"] >= 2]
    print(worst[["serial_number", "cart", "assigned_teacher",
                "stale", "outdated_os", "low_battery"]].to_string(index=False))


if __name__ == "__main__":
    main()