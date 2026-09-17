"""Sensor and GPS baseline recording, replay and fault injection utilities."""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence


class MotionError(ValueError):
    """Raised when motion data is invalid."""


@dataclass(frozen=True)
class SensorSample:
    timestamp_ns: int
    sensor_type: int
    values: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ns": self.timestamp_ns,
            "sensor_type": self.sensor_type,
            "values": list(self.values),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SensorSample":
        return cls(
            timestamp_ns=int(data["timestamp_ns"]),
            sensor_type=int(data["sensor_type"]),
            values=tuple(float(value) for value in data["values"]),
        )


@dataclass(frozen=True)
class GpsSample:
    timestamp_ns: int
    lat: float
    lng: float
    accuracy_m: float
    speed_mps: float
    bearing_deg: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GpsSample":
        return cls(
            timestamp_ns=int(data["timestamp_ns"]),
            lat=float(data["lat"]),
            lng=float(data["lng"]),
            accuracy_m=float(data["accuracy_m"]),
            speed_mps=float(data["speed_mps"]),
            bearing_deg=float(data["bearing_deg"]),
        )


@dataclass
class MotionRecording:
    sensors: list[SensorSample] = field(default_factory=list)
    gps: list[GpsSample] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sensors": [sample.to_dict() for sample in self.sensors],
            "gps": [sample.to_dict() for sample in self.gps],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MotionRecording":
        return cls(
            sensors=[SensorSample.from_dict(item) for item in data.get("sensors", [])],
            gps=[GpsSample.from_dict(item) for item in data.get("gps", [])],
            metadata=dict(data.get("metadata", {})),
        )

    def save_json(self, path: str | Path) -> None:
        Path(path).write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load_json(cls, path: str | Path) -> "MotionRecording":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise MotionError("motion recording root must be an object")
        return cls.from_dict(raw)


def generate_cadence_series(
    duration_s: float,
    base_cadence: float,
    step_s: float = 0.1,
    variation: float = 4.0,
    seed: int | None = None,
) -> list[float]:
    """Generate a non-constant, time-varying cadence series."""
    if duration_s <= 0:
        raise MotionError("duration_s must be positive")
    if step_s <= 0:
        raise MotionError("step_s must be positive")
    rng = random.Random(seed)
    count = max(2, int(duration_s / step_s) + 1)
    phase_a = rng.uniform(0.0, math.tau)
    phase_b = rng.uniform(0.0, math.tau)
    output: list[float] = []
    for index in range(count):
        t = index * step_s
        low_freq = variation * math.sin((2 * math.pi * t / max(duration_s, 1.0)) + phase_a)
        high_freq = variation * 0.35 * math.sin((0.7 * t) + phase_b)
        noise = rng.gauss(0.0, variation * 0.12)
        cadence = base_cadence + low_freq + high_freq + noise
        cadence = max(20.0, min(240.0, cadence))
        output.append(round(cadence, 3))
    return output


def cadence_to_step_counts(
    cadence_series: Sequence[float],
    step_s: float,
    initial_steps: float = 0.0,
) -> list[float]:
    """Integrate cadence (steps/min) into a monotonic step count series."""
    if step_s <= 0:
        raise MotionError("step_s must be positive")
    counts: list[float] = []
    current = initial_steps
    for cadence in cadence_series:
        current += cadence * step_s / 60.0
        counts.append(round(current, 4))
    return counts


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * earth_radius_m * math.asin(math.sqrt(a))


def interpolate_route(
    waypoints: Sequence[tuple[float, float]],
    points_per_segment: int = 20,
) -> list[tuple[float, float]]:
    """Interpolate waypoints with simple spherical linear interpolation."""
    if len(waypoints) < 2:
        raise MotionError("at least two waypoints are required")
    if points_per_segment < 1:
        raise MotionError("points_per_segment must be positive")

    result: list[tuple[float, float]] = []
    for start, end in zip(waypoints, waypoints[1:]):
        for index in range(points_per_segment):
            ratio = index / points_per_segment
            lat = start[0] + (end[0] - start[0]) * ratio
            lng = start[1] + (end[1] - start[1]) * ratio
            result.append((round(lat, 8), round(lng, 8)))
    result.append(tuple(waypoints[-1]))
    return result


class FaultInjector:
    """Apply reproducible sensor/GPS faults for boundary condition tests."""

    def __init__(self, seed: int | None = None) -> None:
        self.rng = random.Random(seed)

    def drop_tail(self, samples: list[SensorSample], ratio: float) -> list[SensorSample]:
        if not 0.0 <= ratio <= 1.0:
            raise MotionError("ratio must be between 0 and 1")
        keep = int(len(samples) * (1.0 - ratio))
        return samples[:keep]

    def zero_sensor_values(self, samples: list[SensorSample]) -> list[SensorSample]:
        return [
            SensorSample(sample.timestamp_ns, sample.sensor_type, tuple(0.0 for _ in sample.values))
            for sample in samples
        ]

    def spike_gps(
        self,
        samples: list[GpsSample],
        index: int,
        lat_delta: float,
        lng_delta: float,
    ) -> list[GpsSample]:
        if not samples:
            return samples
        target = max(0, min(len(samples) - 1, index))
        sample = samples[target]
        changed = GpsSample(
            timestamp_ns=sample.timestamp_ns,
            lat=sample.lat + lat_delta,
            lng=sample.lng + lng_delta,
            accuracy_m=sample.accuracy_m,
            speed_mps=sample.speed_mps,
            bearing_deg=sample.bearing_deg,
        )
        return [*samples[:target], changed, *samples[target + 1 :]]
