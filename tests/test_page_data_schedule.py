"""Tests for the once-per-month page-data limit (scripts/page_data_schedule.py)."""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import page_data_schedule as sched  # noqa: E402


def _use_tmp_stamp(tmp_path, monkeypatch):
    monkeypatch.setattr(sched, "STAMP", str(tmp_path / "page_data_generated.json"))


def test_never_generated_runs(tmp_path, monkeypatch):
    _use_tmp_stamp(tmp_path, monkeypatch)
    assert not sched.skip_if_generated_this_month("streets")


def test_same_month_skips_unless_forced(tmp_path, monkeypatch):
    _use_tmp_stamp(tmp_path, monkeypatch)
    sched.record_generated("streets")
    assert sched.skip_if_generated_this_month("streets")
    assert not sched.skip_if_generated_this_month("streets", force=True)


def test_new_calendar_month_runs(tmp_path, monkeypatch):
    _use_tmp_stamp(tmp_path, monkeypatch)
    sched.record_generated("pages", today=date(2026, 10, 31))
    assert sched.generated_this_month("pages", today=date(2026, 10, 1))
    assert not sched.generated_this_month("pages", today=date(2026, 11, 1))


def test_generators_tracked_separately(tmp_path, monkeypatch):
    _use_tmp_stamp(tmp_path, monkeypatch)
    sched.record_generated("pages")
    assert not sched.skip_if_generated_this_month("developments")
