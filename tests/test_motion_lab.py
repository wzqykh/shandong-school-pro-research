import pytest

from flashrun_lab.motion_lab import (
    FaultInjector,
    GpsSample,
    MotionRecording,
    SensorSample,
    cadence_to_step_counts,
    generate_cadence_series,
    haversine_m,
    interpolate_route,
)


def test_cadence_series_varies_and_stays_in_range() -> None:
    series = generate_cadence_series(duration_s=60, base_cadence=170, step_s=1.0, seed=7)
    assert len(series) == 61
    assert len(set(series)) > 1
    assert all(20.0 <= value <= 240.0 for value in series)


def test_step_counts_are_monotonic() -> None:
    cadence = [160.0, 170.0, 180.0]
    counts = cadence_to_step_counts(cadence, step_s=60.0)
    assert counts == [160.0, 330.0, 510.0]
    assert counts == sorted(counts)


def test_interpolate_route_includes_waypoints() -> None:
    route = interpolate_route([(0.0, 0.0), (0.001, 0.001)], points_per_segment=3)
    assert route[0] == (0.0, 0.0)
    assert route[-1] == (0.001, 0.001)
    assert len(route) == 4


def test_recording_json_round_trip(tmp_path) -> None:
    recording = MotionRecording(
        sensors=[SensorSample(1, 1, (0.0, 9.8, 0.0))],
        gps=[GpsSample(1, 34.0, 120.0, 5.0, 2.0, 90.0)],
        metadata={"tag": "baseline"},
    )
    path = tmp_path / "recording.json"
    recording.save_json(path)
    loaded = MotionRecording.load_json(path)
    assert loaded == recording


def test_fault_injector_drop_tail_and_zero_values() -> None:
    injector = FaultInjector(seed=1)
    samples = [SensorSample(i, 1, (1.0, 2.0)) for i in range(10)]
    assert len(injector.drop_tail(samples, 0.5)) == 5
    zeroed = injector.zero_sensor_values(samples[:1])
    assert zeroed[0].values == (0.0, 0.0)


def test_haversine_known_distance() -> None:
    distance = haversine_m(0.0, 0.0, 0.0, 0.001)
    assert 100 < distance < 120
