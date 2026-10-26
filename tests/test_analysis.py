"""
Tests for analysis.py: does each flag rule catch the right laptops?

Each test builds a tiny table where we already know the right answer,
runs one function on it, and checks the result with assert.

"""

import pandas as pd

from analysis import (
    add_flags,
    find_missing,
    flag_low_battery,
    flag_outdated_os,
    flag_stale,
    summarize,
)


def make_devices():
    """Four laptops, each built to test something specific."""
    return pd.DataFrame({
        "serial_number": ["CA-1", "CA-2", "CA-3", "CA-4"],
        "building": ["Building A", "Building A", "Building B", "Building B"],
        "cart": ["A-Cart-1", "A-Cart-1", "B-Cart-1", "B-Cart-1"],
        "os_version": ["Windows 11 23H2", "Windows 10 22H2", "Windows 11 23H2", "Windows 11 23H2"],
        "last_sync": pd.to_datetime(["2026-10-20", "2026-10-01", "2026-09-01", "2026-10-20"]),
        "battery_health": [90, 85, 40, 60],
    })

def test_stale_uses_the_newest_sync_as_today():
    devices = make_devices()
    # The newest sync is Oct 20. CA-3 synced Sep 1, which is 49 days earlier.
    assert flag_stale(devices).tolist() == [False, False, True, False]


def test_stale_with_a_given_date():
    devices = make_devices()
    # Measured from Nov 15, CA-2 (Oct 1, 45 days) is now stale too.
    result = flag_stale(devices, today="2026-11-15")
    assert result.tolist() == [False, True, True, False]


def test_exactly_30_days_is_not_stale():
    devices = make_devices()
    # CA-2 synced Oct 1. From Oct 31 that's exactly 30 days, and the rule is "more than 30".
    result = flag_stale(devices, today="2026-10-31")
    assert result.tolist() == [False, False, True, False]

def test_outdated_os():
    devices = make_devices()
    assert flag_outdated_os(devices).tolist() == [False, True, False, False]


def test_low_battery_is_below_60_not_equal():
    devices = make_devices()
    # CA-3 is at 40% (low). CA-4 is at exactly 60%, which is not below 60.
    assert flag_low_battery(devices).tolist() == [False, False, True, False]


def test_find_missing():
    devices = make_devices()
    expected = pd.DataFrame({"serial_number": ["CA-1", "CA-2", "CA-3", "CA-4", "CA-5"]})
    missing = find_missing(devices, expected)
    assert missing["serial_number"].tolist() == ["CA-5"]


def test_add_flags_counts_problems():
    flagged = add_flags(make_devices())
    # CA-2 has an old OS. CA-3 is stale and has a low battery.
    assert flagged["flag_count"].tolist() == [0, 1, 2, 0]


def test_add_flags_does_not_change_the_original():
    devices = make_devices()
    add_flags(devices)
    assert "stale" not in devices.columns


def test_summarize_by_building():
    summary = summarize(add_flags(make_devices()), "building")
    assert summary.loc["Building A", "total"] == 2
    assert summary.loc["Building A", "outdated_os"] == 1
    assert summary.loc["Building B", "any_flag"] == 1