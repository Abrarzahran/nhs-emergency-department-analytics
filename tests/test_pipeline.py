"""The build pipeline, and the dashboard's behaviour when the database file does not exist."""
import sqlite3

import pytest
from streamlit.testing.v1 import AppTest

from conftest import ROOT
from nhs_ed import config
from nhs_ed.pipeline import build


def _count(path, table):
    with sqlite3.connect(path) as con:
        return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_build_writes_the_database_without_touching_committed_reports(tmp_path):
    reports = [config.RAW_DIR.parent / "MANIFEST.csv", config.PROCESSED_DIR / "validation_report.csv"]
    before = [p.read_bytes() for p in reports]
    target = tmp_path / "nested" / "ae.sqlite"

    result = build(target, write_reports=False)

    assert result.db_path == target and target.exists()
    assert not result.errors
    assert _count(target, "fact_org_month") == 2386
    assert list(target.parent.glob("*.tmp")) == []  # the temporary file was moved into place
    assert [p.read_bytes() for p in reports] == before


def test_build_replaces_an_existing_database(tmp_path):
    target = tmp_path / "ae.sqlite"
    target.write_bytes(b"not a database")
    build(target, write_reports=False)
    assert _count(target, "dim_month") == 12


@pytest.fixture
def app_with_missing_database(tmp_path, monkeypatch):
    import streamlit as st
    target = tmp_path / "ae_2025_26.sqlite"
    monkeypatch.setattr(config, "DB_PATH", target)
    st.cache_resource.clear()
    yield target
    st.cache_resource.clear()


def test_dashboard_builds_a_missing_database_and_starts(app_with_missing_database):
    target = app_with_missing_database
    assert not target.exists()

    at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=120).run()

    assert not at.exception
    assert not at.error
    assert target.exists()
    assert dict((m.label, m.value) for m in at.metric)["Type 1 attendances"] == "17,121,495"


def test_dashboard_builds_only_once_across_interactions(app_with_missing_database):
    target = app_with_missing_database
    at = AppTest.from_file(str(ROOT / "app" / "streamlit_app.py"), default_timeout=120).run()
    built_at = target.stat().st_mtime_ns

    at.sidebar.checkbox[0].uncheck().run()

    assert not at.exception
    assert target.stat().st_mtime_ns == built_at
