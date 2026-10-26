"""
Tests for app.py: do the pages load, and do saving and downloading work?

"""

import io

import pytest

import app as fleetwatch
import database


@pytest.fixture
def client(tmp_path, monkeypatch):
    """A fake browser for the app, using a throwaway database so tests never touch your real one."""
    # tmp_path is a brand-new empty folder pytest makes for each test.
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(fleetwatch, "UPLOADED_EXPORT", tmp_path / "uploaded_export.csv")
    database.init_db()
    return fleetwatch.app.test_client()


@pytest.mark.parametrize("page", ["/", "/dashboard", "/devices", "/devices?flag=stale"])
def test_pages_load(client, page):
    assert client.get(page).status_code == 200


def test_saving_a_teacher_stores_it(client):
    client.post("/devices/CA-TEST01/assign", data={"teacher": "Mr. Pytest"})
    assert database.get_assignments() == {"CA-TEST01": "Mr. Pytest"}


def test_saved_teacher_replaces_the_export(client):
    serial = fleetwatch.get_flagged_devices()["serial_number"].iloc[0]
    client.post(f"/devices/{serial}/assign", data={"teacher": "Ms. Override"})
    page = client.get("/devices?search=override").get_data(as_text=True)
    assert serial in page


def test_saving_twice_keeps_one_row(client):
    client.post("/devices/CA-TEST01/assign", data={"teacher": "First"})
    client.post("/devices/CA-TEST01/assign", data={"teacher": "Second"})
    assert database.get_assignments() == {"CA-TEST01": "Second"}

def test_search_ignores_spaces_and_dots(client):
    # The data spells it "Ms. Rivera", but people type it all sorts of ways.
    for typed in ["Ms. Rivera", "ms.rivera", "msrivera", "RIVERA"]:
        page = client.get(f"/devices?search={typed}").get_data(as_text=True)
        assert "Ms. Rivera" in page
        assert "Showing 0 of" not in page

def test_building_filter(client):
    page = client.get("/devices?building=Building+B").get_data(as_text=True)
    assert "B-Cart-1" in page
    assert "A-Cart-1</td>" not in page


def test_export_downloads_only_flagged_laptops(client):
    response = client.get("/export.csv?flag=any")
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]
    lines = response.get_data(as_text=True).splitlines()
    assert lines[0].endswith(",problems")
    # Every row after the header names at least one problem, so none end with an empty problems column.
    assert all(not line.endswith(",") for line in lines[1:])


def test_upload_rejects_a_csv_missing_columns(client):
    bad_csv = (io.BytesIO(b"serial_number,cart\nCA-1,A-Cart-1\n"), "bad.csv")
    response = client.post("/", data={"export": bad_csv}, follow_redirects=True)
    assert "missing columns" in response.get_data(as_text=True)