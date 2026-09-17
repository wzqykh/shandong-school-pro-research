from flashrun_lab.detection_lab import (
    DEFAULT_PATTERNS,
    DetectionLayer,
    DetectionMatrix,
    DetectionPoint,
    DetectionSeverity,
    scan_text_for_patterns,
)


def test_scan_text_for_patterns() -> None:
    findings = scan_text_for_patterns("frida-agent detected /proc/self/maps")
    assert ("hook", "frida") in findings


def test_detection_matrix_round_trip(tmp_path) -> None:
    matrix = DetectionMatrix()
    matrix.add(
        DetectionPoint(
            point_id="native-hook-check",
            layer=DetectionLayer.NATIVE,
            category="anti-hook",
            severity=DetectionSeverity.HARD,
            evidence="/proc/self/maps scan for frida-agent",
            weight=2.0,
        )
    )
    path = tmp_path / "detection.json"
    matrix.save_json(path)
    loaded = DetectionMatrix.load_json(path)
    assert loaded.points == matrix.points


def test_detection_matrix_filters_and_markdown() -> None:
    point = DetectionPoint(
        point_id="root-check",
        layer=DetectionLayer.JAVA,
        category="root",
        severity=DetectionSeverity.SOFT,
        evidence="check magisk",
    )
    matrix = DetectionMatrix([point])
    assert matrix.filter(layer=DetectionLayer.JAVA) == [point]
    assert matrix.filter(severity=DetectionSeverity.HARD) == []
    assert "root-check" in matrix.to_markdown()


def test_default_patterns_are_nonempty() -> None:
    assert DEFAULT_PATTERNS
