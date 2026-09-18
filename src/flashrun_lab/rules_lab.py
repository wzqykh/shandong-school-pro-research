"""School run rules, geofence and checkpoint models.

These models are intentionally read-only research artifacts.  They store data
observed from the app UI or from later dynamic instrumentation, and provide
small offline validators that can be used against recorded route samples.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import math
import re
from pathlib import Path
from typing import Any, Iterable, Sequence
import xml.etree.ElementTree as ET


class RulesError(ValueError):
    """Raised when a rules/fence artifact is invalid."""


def _parse_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise RulesError(f"{field_name} must be numeric") from exc


@dataclass(frozen=True)
class PaceRange:
    min_sec_per_km: float
    max_sec_per_km: float

    def to_dict(self) -> dict[str, float]:
        return {
            "min_sec_per_km": self.min_sec_per_km,
            "max_sec_per_km": self.max_sec_per_km,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PaceRange":
        if not isinstance(data, dict):
            raise RulesError("pace must be an object")
        try:
            minimum = float(data["min_sec_per_km"])
            maximum = float(data["max_sec_per_km"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RulesError("pace requires min_sec_per_km and max_sec_per_km") from exc
        if minimum <= 0 or maximum <= minimum:
            raise RulesError("pace values must satisfy 0 < min < max")
        return cls(min_sec_per_km=minimum, max_sec_per_km=maximum)


@dataclass(frozen=True)
class RunPolicy:
    version: str
    source: str
    effective_from: str
    effective_to: str
    target_runs: int
    daily_start: str
    daily_end: str
    min_distance_km: float
    max_distance_km: float
    pace: PaceRange
    daily_max_runs: int = 2
    weekly_max_runs: int = 14
    pause_seconds: int = 120
    run_mode: str = "sequential_checkpoint"
    checkpoint_count: int = 3
    valid_area: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "effective_from": self.effective_from,
            "effective_to": self.effective_to,
            "target_runs": self.target_runs,
            "daily_start": self.daily_start,
            "daily_end": self.daily_end,
            "min_distance_km": self.min_distance_km,
            "max_distance_km": self.max_distance_km,
            "pace": self.pace.to_dict(),
            "daily_max_runs": self.daily_max_runs,
            "weekly_max_runs": self.weekly_max_runs,
            "pause_seconds": self.pause_seconds,
            "run_mode": self.run_mode,
            "checkpoint_count": self.checkpoint_count,
            "valid_area": self.valid_area,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunPolicy":
        required = (
            "version",
            "source",
            "effective_from",
            "effective_to",
            "target_runs",
            "daily_start",
            "daily_end",
            "min_distance_km",
            "max_distance_km",
            "pace",
        )
        missing = [key for key in required if key not in data]
        if missing:
            raise RulesError(f"run policy missing fields: {missing}")

        target_runs = int(data["target_runs"])
        daily_max = int(data.get("daily_max_runs", 2))
        weekly_max = int(data.get("weekly_max_runs", 14))
        pause_seconds = int(data.get("pause_seconds", 120))
        checkpoint_count = int(data.get("checkpoint_count", 3))
        minimum_distance = _parse_float(data["min_distance_km"], "min_distance_km")
        maximum_distance = _parse_float(data["max_distance_km"], "max_distance_km")

        if target_runs <= 0 or daily_max <= 0 or weekly_max <= 0:
            raise RulesError("run counts must be positive")
        if minimum_distance <= 0 or maximum_distance < minimum_distance:
            raise RulesError("distance bounds must satisfy 0 < min <= max")
        if checkpoint_count < 0:
            raise RulesError("checkpoint_count cannot be negative")
        if pause_seconds < 0:
            raise RulesError("pause_seconds cannot be negative")

        return cls(
            version=str(data["version"]),
            source=str(data["source"]),
            effective_from=str(data["effective_from"]),
            effective_to=str(data["effective_to"]),
            target_runs=target_runs,
            daily_start=str(data["daily_start"]),
            daily_end=str(data["daily_end"]),
            min_distance_km=minimum_distance,
            max_distance_km=maximum_distance,
            pace=PaceRange.from_dict(data["pace"]),
            daily_max_runs=daily_max,
            weekly_max_runs=weekly_max,
            pause_seconds=pause_seconds,
            run_mode=str(data.get("run_mode", "sequential_checkpoint")),
            checkpoint_count=checkpoint_count,
            valid_area=str(data.get("valid_area", "")),
        )


@dataclass(frozen=True)
class FenceCatalogEntry:
    id: str
    name: str
    distance_km: float
    status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "distance_km": self.distance_km,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FenceCatalogEntry":
        for key in ("id", "name", "distance_km"):
            if key not in data:
                raise RulesError(f"fence entry missing field: {key}")
        distance = _parse_float(data["distance_km"], "distance_km")
        if distance < 0:
            raise RulesError("fence distance cannot be negative")
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            distance_km=distance,
            status=str(data.get("status", "unknown")),
        )


@dataclass(frozen=True)
class FenceCatalog:
    version: str
    source: str
    fences: tuple[FenceCatalogEntry, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "source": self.source,
            "fences": [fence.to_dict() for fence in self.fences],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FenceCatalog":
        for key in ("version", "source", "fences"):
            if key not in data:
                raise RulesError(f"fence catalog missing field: {key}")
        fences = tuple(FenceCatalogEntry.from_dict(item) for item in data["fences"])
        return cls(
            version=str(data["version"]),
            source=str(data["source"]),
            fences=fences,
        )

    def find(self, fence_id: str) -> FenceCatalogEntry:
        for fence in self.fences:
            if fence.id == fence_id:
                return fence
        raise RulesError(f"unknown fence id: {fence_id}")


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float

    def to_dict(self) -> dict[str, float]:
        return {"lat": self.lat, "lng": self.lng}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoPoint":
        if not isinstance(data, dict) or "lat" not in data or "lng" not in data:
            raise RulesError("geo point must contain lat and lng")
        lat = _parse_float(data["lat"], "lat")
        lng = _parse_float(data["lng"], "lng")
        if not -90.0 <= lat <= 90.0 or not -180.0 <= lng <= 180.0:
            raise RulesError("geo point is out of range")
        return cls(lat=lat, lng=lng)

    def as_tuple(self) -> tuple[float, float]:
        return (self.lat, self.lng)


@dataclass(frozen=True)
class GeoFence:
    id: str
    name: str
    polygon: tuple[GeoPoint, ...] = field(default_factory=tuple)
    status: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "polygon": [point.to_dict() for point in self.polygon],
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GeoFence":
        for key in ("id", "name", "polygon"):
            if key not in data:
                raise RulesError(f"geo fence missing field: {key}")
        polygon = tuple(GeoPoint.from_dict(point) for point in data["polygon"])
        if polygon and len(polygon) < 3:
            raise RulesError("geo fence polygon requires at least 3 points")
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            polygon=polygon,
            status=str(data.get("status", "unknown")),
        )


@dataclass(frozen=True)
class CheckpointPlan:
    fence_id: str
    points: tuple[GeoPoint, ...] = field(default_factory=tuple)
    required_order: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "fence_id": self.fence_id,
            "points": [point.to_dict() for point in self.points],
            "required_order": self.required_order,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointPlan":
        if "fence_id" not in data:
            raise RulesError("checkpoint plan missing fence_id")
        points = tuple(GeoPoint.from_dict(point) for point in data.get("points", []))
        return cls(
            fence_id=str(data["fence_id"]),
            points=points,
            required_order=bool(data.get("required_order", True)),
        )


def load_json_object(path: str | Path) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RulesError(f"{path} root must be a JSON object")
    return raw


def save_json_object(path: str | Path, data: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_run_policy(path: str | Path) -> RunPolicy:
    return RunPolicy.from_dict(load_json_object(path))


def save_run_policy(path: str | Path, policy: RunPolicy) -> None:
    save_json_object(path, policy.to_dict())


def load_fence_catalog(path: str | Path) -> FenceCatalog:
    return FenceCatalog.from_dict(load_json_object(path))


def save_fence_catalog(path: str | Path, catalog: FenceCatalog) -> None:
    save_json_object(path, catalog.to_dict())


def load_geofence(path: str | Path) -> GeoFence:
    return GeoFence.from_dict(load_json_object(path))


def save_geofence(path: str | Path, fence: GeoFence) -> None:
    save_json_object(path, fence.to_dict())


def load_checkpoint_plan(path: str | Path) -> CheckpointPlan:
    return CheckpointPlan.from_dict(load_json_object(path))


def save_checkpoint_plan(path: str | Path, plan: CheckpointPlan) -> None:
    save_json_object(path, plan.to_dict())


def extract_ui_texts(path: str | Path) -> list[str]:
    """Return non-empty ``text`` and ``content-desc`` values from a uiautomator dump."""
    root = ET.parse(path).getroot()
    output: list[str] = []
    for node in root.iter("node"):
        for attr in ("text", "content-desc"):
            value = (node.attrib.get(attr) or "").strip()
            if value:
                output.append(value)
    return output


def parse_fence_catalog_from_ui(
    path: str | Path,
    *,
    version: str,
    source: str | None = None,
) -> FenceCatalog:
    """Parse the simple "更多" fence list UI dump.

    The app UI lists rows as ``name``, ``distance``, ``status``.  This parser is
    intentionally narrow and therefore does not try to infer polygons.
    """
    texts = extract_ui_texts(path)
    entries: list[FenceCatalogEntry] = []
    distance_re = re.compile(r"^\d+(?:\.\d+)?公里$")

    for index, text in enumerate(texts):
        if not distance_re.match(text):
            continue
        if index == 0:
            raise RulesError("fence distance found without a preceding name")
        name = texts[index - 1]
        status = texts[index + 1] if index + 1 < len(texts) else "unknown"
        if not status.startswith(("开放", "关闭", "维护", "未开放")):
            status = "unknown"
        distance_km = float(text.removesuffix("公里"))
        entry_id = _slug_fence_id(name, distance_km)
        entries.append(
            FenceCatalogEntry(
                id=entry_id,
                name=name,
                distance_km=distance_km,
                status=status,
            )
        )

    if not entries:
        raise RulesError("no fence rows found in UI dump")
    return FenceCatalog(
        version=version,
        source=source or str(path),
        fences=tuple(entries),
    )


def _slug_fence_id(name: str, distance_km: float) -> str:
    slug = re.sub(r"\s+", "-", name)
    distance = f"{distance_km:g}".replace(".", "-")
    return f"{slug}-{distance}km"


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    earth_radius_m = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * earth_radius_m * math.asin(math.sqrt(a))


def route_distance_km(points: Sequence[GeoPoint | tuple[float, float]]) -> float:
    if len(points) < 2:
        return 0.0
    total = 0.0
    for start, end in zip(points, points[1:]):
        start_lat, start_lng = _coords(start)
        end_lat, end_lng = _coords(end)
        total += haversine_m(start_lat, start_lng, end_lat, end_lng)
    return total / 1000.0


def point_in_polygon(
    point: GeoPoint | tuple[float, float],
    polygon: Sequence[GeoPoint | tuple[float, float]],
) -> bool:
    """Ray-casting point-in-polygon test on latitude/longitude coordinates."""
    if len(polygon) < 3:
        return False
    lat, lng = _coords(point)
    inside = False
    previous = polygon[-1]
    for current in polygon:
        prev_lat, prev_lng = _coords(previous)
        curr_lat, curr_lng = _coords(current)
        intersects = (curr_lng > lng) != (prev_lng > lng)
        if intersects:
            boundary_lat = (prev_lat - curr_lat) * (lng - curr_lng) / (
                prev_lng - curr_lng
            ) + curr_lat
            if lat < boundary_lat:
                inside = not inside
        previous = current
    return inside


def checkpoint_order_satisfied(
    route: Sequence[GeoPoint | tuple[float, float]],
    checkpoints: Sequence[GeoPoint | tuple[float, float]],
    *,
    tolerance_m: float = 25.0,
    required_order: bool = True,
) -> bool:
    """Return whether the route passes every checkpoint within tolerance."""
    if not checkpoints:
        return True

    route_coords = [_coords(point) for point in route]
    last_index = -1
    for checkpoint in checkpoints:
        target_lat, target_lng = _coords(checkpoint)
        found = -1
        for index, (lat, lng) in enumerate(route_coords):
            if haversine_m(lat, lng, target_lat, target_lng) <= tolerance_m:
                found = index
                break
        if found < 0 or (required_order and found <= last_index):
            return False
        if required_order:
            last_index = found
    return True


@dataclass(frozen=True)
class RouteAssessment:
    distance_km: float
    average_pace_sec_per_km: float | None
    inside_ratio: float
    checkpoints_satisfied: bool
    violations: tuple[str, ...]


def assess_recorded_route(
    route: Sequence[GeoPoint | tuple[float, float]],
    *,
    policy: RunPolicy | None = None,
    fence: GeoFence | None = None,
    checkpoints: Sequence[GeoPoint | tuple[float, float]] | None = None,
    duration_s: float | None = None,
    required_order: bool = True,
    checkpoint_tolerance_m: float = 25.0,
) -> RouteAssessment:
    """Assess an already recorded route without modifying app behavior."""
    if len(route) < 2:
        raise RulesError("route assessment requires at least two points")
    if duration_s is not None and duration_s <= 0:
        raise RulesError("duration_s must be positive when provided")

    distance = route_distance_km(route)
    violations: list[str] = []

    inside_ratio = 1.0
    if fence is not None:
        inside_count = sum(1 for point in route if point_in_polygon(point, fence.polygon))
        inside_ratio = inside_count / len(route)
        if inside_ratio < 1.0:
            violations.append("route contains points outside the geofence")

    if policy is not None:
        if distance < policy.min_distance_km:
            violations.append("route distance is below the minimum")
        if distance > policy.max_distance_km:
            violations.append("route distance is above the maximum")

    average_pace = None
    if duration_s is not None:
        average_pace = duration_s / distance if distance > 0 else math.inf
        if policy is not None and math.isfinite(average_pace):
            if average_pace < policy.pace.min_sec_per_km:
                violations.append("average pace is faster than allowed")
            elif average_pace > policy.pace.max_sec_per_km:
                violations.append("average pace is slower than allowed")

    checkpoints_satisfied = True
    if checkpoints:
        checkpoints_satisfied = checkpoint_order_satisfied(
            route,
            checkpoints,
            tolerance_m=checkpoint_tolerance_m,
            required_order=required_order,
        )
        if not checkpoints_satisfied:
            violations.append("checkpoint order was not satisfied")

    return RouteAssessment(
        distance_km=distance,
        average_pace_sec_per_km=average_pace,
        inside_ratio=inside_ratio,
        checkpoints_satisfied=checkpoints_satisfied,
        violations=tuple(violations),
    )


def _coords(point: GeoPoint | tuple[float, float]) -> tuple[float, float]:
    if isinstance(point, GeoPoint):
        return (point.lat, point.lng)
    if isinstance(point, (tuple, list)) and len(point) == 2:
        return (float(point[0]), float(point[1]))
    raise RulesError("point must be GeoPoint or a (lat, lng) tuple")
