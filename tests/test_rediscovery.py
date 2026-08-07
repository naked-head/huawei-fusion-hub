"""Tests for the rediscovery diff logic.

Standalone, in the same style as test_normalize.py: run with
`python tests/test_rediscovery.py`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components"))

from huawei_fusion_hub.coordinator import diff_candidates

HS = "huawei_solar"
FSP = "fusionsolarplus"


def test_no_change():
    before = {"battery_soc": {HS: "sensor.battery_soc"}}
    diff = diff_candidates(before, dict(before))
    assert not diff.changed
    assert not diff.has_losses
    assert diff.new_keys == [] and diff.gained == []


def test_rename_marks_changed_without_new_or_gained():
    """The regression this release fixes.

    A renamed source entity produces no new, gained or dropped key. Before
    the fix the rediscovery returned early on exactly this shape, leaving
    the state listener subscribed to the old entity_id.
    """
    before = {"battery_soc": {HS: "sensor.battery_soc"}}
    after = {"battery_soc": {HS: "sensor.casa_batteria_soc"}}
    diff = diff_candidates(before, after)
    assert diff.changed, "a rename must trigger a re-subscription"
    assert diff.new_keys == []
    assert diff.gained == []
    assert diff.dropped == []
    assert diff.lost_sources == {}


def test_new_key():
    before = {}
    after = {"battery_soc": {HS: "sensor.battery_soc"}}
    diff = diff_candidates(before, after)
    assert diff.changed
    assert diff.new_keys == ["battery_soc"]
    assert not diff.has_losses


def test_gained_source():
    before = {"battery_soc": {HS: "sensor.a"}}
    after = {"battery_soc": {HS: "sensor.a", FSP: "sensor.b"}}
    diff = diff_candidates(before, after)
    assert diff.gained == ["battery_soc"]
    assert not diff.has_losses


def test_lost_source_is_reported():
    """A fallback match broken by a rename shows up only as a lost source."""
    before = {"battery_soc": {HS: "sensor.a", FSP: "sensor.b"}}
    after = {"battery_soc": {HS: "sensor.a"}}
    diff = diff_candidates(before, after)
    assert diff.changed
    assert diff.lost_sources == {"battery_soc": [FSP]}
    assert diff.dropped == []
    assert diff.has_losses
    assert diff.new_keys == [] and diff.gained == []


def test_dropped_key_is_reported():
    before = {"battery_soc": {HS: "sensor.a"}}
    after = {}
    diff = diff_candidates(before, after)
    assert diff.changed
    assert diff.dropped == ["battery_soc"]
    assert diff.has_losses


def test_gain_and_loss_together():
    before = {"a": {HS: "sensor.a"}, "b": {FSP: "sensor.b"}}
    after = {"a": {HS: "sensor.a", FSP: "sensor.a2"}, "c": {HS: "sensor.c"}}
    diff = diff_candidates(before, after)
    assert diff.new_keys == ["c"]
    assert diff.gained == ["a"]
    assert diff.dropped == ["b"]
    assert diff.has_losses


def _run():
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
        except AssertionError as err:
            failures += 1
            print(f"FAIL {name}: {err}")
        else:
            print(f"PASS {name}")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run() else 0)
