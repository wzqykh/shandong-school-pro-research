from pathlib import Path

import pytest

from flashrun_lab.rules_lab import (
    CheckpointPlan,
    GeoFence,
    GeoPoint,
    PaceRange,
    RulesError,
    RunPolicy,
    assess_recorded_route,
    checkpoint_order_satisfied,
    extract_ui_texts,
    load_fence_catalog,
    load_geofence,
    load_run_policy,
    parse_fence_catalog_from_ui,
    point_in_polygon,
    route_distance_km,
)


def _profile_path(name: str) -> Path:
    return Path(__file__).resolve().parents[1] / "profiles" / name


def test_load_versioned_school_rules() -> None:
    policy = load_run_policy(_profile_path("2.0.6.run_rules.json"))
    assert policy.version == "2.0.6"
    assert policy.target_runs == 50
    assert policy.min_distance_km == 2.4
    assert policy.pace == PaceRange(min_sec_per_km=240, max_sec_per_km=480)
    assert policy.run_mode == "sequential_checkpoint"
    assert policy.checkpoint_count == 3


def test_load_versioned_fence_catalog() -> None:
    catalog = load_fence_catalog(_profile_path("2.0.6.fence_catalog.json"))
    assert len(catalog.fences) == 4
    assert catalog.find("track-west-3-36km").name == "西田径场"


def test_empty_geofence_example_loads_as_placeholder() -> None:
    fence = load_geofence(_profile_path("2.0.6.geofence.example.json"))
    assert fence.id == "track-main-6-84km"
    assert fence.polygon == ()
    assert not point_in_polygon((1.0, 1.0), fence.polygon)


def test_parse_fence_catalog_from_ui(tmp_path) -> None:
    path = tmp_path / "fence_more.xml"
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy>
  <node text="跑步区域" />
  <node text="田径场" />
  <node text="0.07公里" />
  <node text="开放中" />
  <node text="西田径场" />
  <node text="3.36公里" />
  <node text="开放中" />
</hierarchy>
""",
        encoding="utf-8",
    )

    catalog = parse_fence_catalog_from_ui(path, version="2.0.6")
    assert [fence.name for fence in catalog.fences] == ["田径场", "西田径场"]
    assert [fence.distance_km for fence in catalog.fences] == [0.07, 3.36]
    assert all(fence.status == "开放中" for fence in catalog.fences)


def test_extract_ui_texts_includes_content_desc(tmp_path) -> None:
    path = tmp_path / "ui.xml"
    path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<hierarchy>
  <node text="开始跑步" content-desc="" />
  <node text="" content-desc="跑步区域" />
</hierarchy>
""",
        encoding="utf-8",
    )
    assert extract_ui_texts(path) == ["开始跑步", "跑步区域"]


def test_route_distance_km_known_scale() -> None:
    route = [(0.0, 0.0), (0.0, 0.001), (0.001, 0.001)]
    distance = route_distance_km(route)
    assert 0.2 < distance < 0.25


def test_point_in_polygon_ray_cast() -> None:
    polygon = [GeoPoint(0, 0), GeoPoint(0, 2), GeoPoint(2, 2), GeoPoint(2, 0)]
    assert point_in_polygon(GeoPoint(1, 1), polygon)
    assert not point_in_polygon(GeoPoint(3, 3), polygon)


def test_checkpoint_order_requires_forward_sequence() -> None:
    route = [(0.0, 0.0), (0.0001, 0.0), (0.0002, 0.0)]
    checkpoints = [(0.0, 0.0), (0.0002, 0.0)]
    assert checkpoint_order_satisfied(route, checkpoints, tolerance_m=5.0)
    assert not checkpoint_order_satisfied(
        list(reversed(route)), checkpoints, tolerance_m=5.0
    )


def test_assess_recorded_route_reports_violations() -> None:
    policy = RunPolicy(
        version="2.0.6",
        source="test",
        effective_from="2026-09-14",
        effective_to="2026-12-20",
        target_runs=50,
        daily_start="06:00",
        daily_end="22:00",
        min_distance_km=2.4,
        max_distance_km=10.0,
        pace=PaceRange(240, 480),
    )
    fence = GeoFence(
        id="track",
        name="track",
        polygon=(GeoPoint(0, 0), GeoPoint(0, 2), GeoPoint(2, 2), GeoPoint(2, 0)),
    )
    route = [(0.0001, 0.0001), (0.0002, 0.0002)]
    assessment = assess_recorded_route(route, policy=policy, fence=fence, duration_s=600)
    assert assessment.distance_km < 1.0
    assert "route distance is below the minimum" in assessment.violations
    assert "average pace is slower than allowed" in assessment.violations


def test_geo_fence_rejects_open_polygon() -> None:
    with pytest.raises(RulesError):
        GeoFence.from_dict(
            {
                "id": "bad",
                "name": "bad",
                "polygon": [{"lat": 0, "lng": 0}, {"lat": 1, "lng": 1}],
            }
        )


def test_checkpoint_plan_round_trip(tmp_path) -> None:
    plan = CheckpointPlan(
        fence_id="track-main-6-84km",
        points=(GeoPoint(1, 2), GeoPoint(3, 4)),
        required_order=True,
    )
    from flashrun_lab.rules_lab import load_checkpoint_plan, save_checkpoint_plan

    path = tmp_path / "plan.json"
    save_checkpoint_plan(path, plan)
    assert load_checkpoint_plan(path) == plan
