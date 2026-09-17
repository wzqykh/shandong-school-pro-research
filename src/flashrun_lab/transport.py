"""Transport abstraction for request delivery."""

from __future__ import annotations

import json
import shlex
import tempfile
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .apk_lab import AdbRunner


@dataclass(frozen=True)
class RequestContext:
    method: str
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | None = None


@dataclass(frozen=True)
class ResponseContext:
    status: int
    headers: dict[str, str]
    body: bytes


class TransportError(RuntimeError):
    """Raised when a transport cannot complete a request."""


class Transport(ABC):
    @abstractmethod
    def send(self, request: RequestContext) -> ResponseContext:
        raise NotImplementedError

    @abstractmethod
    def probe(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def describe(self) -> str:
        raise NotImplementedError


class DirectTransport(Transport):
    """Ordinary HTTPS transport for local validation or a trusted test proxy."""

    def __init__(self, timeout: float = 15.0) -> None:
        self.timeout = timeout

    def send(self, request: RequestContext) -> ResponseContext:
        req = urllib.request.Request(
            request.url,
            data=request.body,
            headers=request.headers,
            method=request.method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read()
                return ResponseContext(
                    status=response.status,
                    headers=dict(response.headers.items()),
                    body=body,
                )
        except urllib.error.HTTPError as exc:
            return ResponseContext(
                status=exc.code,
                headers=dict(exc.headers.items()),
                body=exc.read(),
            )
        except urllib.error.URLError as exc:
            raise TransportError(str(exc)) from exc

    def probe(self) -> bool:
        return True

    def describe(self) -> str:
        return "direct"


class MockTransport(Transport):
    """Deterministic transport used by tests and offline replay."""

    def __init__(self, responses: dict[tuple[str, str], ResponseContext] | None = None) -> None:
        self.responses = responses or {}
        self.requests: list[RequestContext] = []

    def send(self, request: RequestContext) -> ResponseContext:
        self.requests.append(request)
        key = (request.method, request.url)
        response = self.responses.get(key)
        if response is None:
            raise TransportError(f"no mock response for {request.method} {request.url}")
        return response

    def probe(self) -> bool:
        return True

    def describe(self) -> str:
        return "mock"


class AdbTransport(Transport):
    """Send HTTP requests from the device side via adb shell curl."""

    def __init__(
        self,
        adb: AdbRunner,
        device_workdir: str = "/data/local/tmp/flashrun",
        timeout: int = 30,
    ) -> None:
        self.adb = adb
        self.device_workdir = device_workdir
        self.timeout = timeout

    def probe(self) -> bool:
        try:
            self.adb.run("shell", "command", "-v", "curl")
            return True
        except Exception:
            return False

    def describe(self) -> str:
        return "adb-device-curl"

    def send(self, request: RequestContext) -> ResponseContext:
        if not self.probe():
            raise TransportError("adb device does not provide curl")

        self.adb.run("shell", "mkdir", "-p", self.device_workdir)

        body_path: str | None = None
        if request.body:
            with tempfile.NamedTemporaryFile(delete=False) as handle:
                handle.write(request.body)
                local_path = Path(handle.name)
            remote_path = f"{self.device_workdir}/body.bin"
            self.adb.run("push", str(local_path), remote_path)
            local_path.unlink(missing_ok=True)
            body_path = remote_path

        header_path = f"{self.device_workdir}/headers.txt"
        response_path = f"{self.device_workdir}/response.bin"
        self.adb.run("shell", "rm", "-f", header_path, response_path)

        command = [
            "curl",
            "-sS",
            "--max-time",
            str(self.timeout),
            "-D",
            header_path,
            "-o",
            response_path,
            "-X",
            request.method,
        ]
        for key, value in request.headers.items():
            command.extend(["-H", f"{key}: {value}"])
        if body_path:
            command.extend(["--data-binary", f"@{body_path}"])
        command.append(request.url)

        shell_command = " ".join(shlex.quote(part) for part in command)
        self.adb.run("shell", shell_command)

        raw_headers = self.adb.run("shell", "cat", header_path)
        raw_body = self.adb.run("shell", "cat", response_path)
        status, headers = _parse_curl_headers(raw_headers)
        return ResponseContext(
            status=status,
            headers=headers,
            body=raw_body.encode("utf-8", errors="surrogateescape"),
        )


def _parse_curl_headers(raw: str) -> tuple[int, dict[str, str]]:
    status = 0
    headers: dict[str, str] = {}
    lines = raw.splitlines()
    if not lines:
        return status, headers
    first = lines[0]
    parts = first.split()
    if len(parts) >= 2 and parts[1].isdigit():
        status = int(parts[1])
    for line in lines[1:]:
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
    return status, headers
