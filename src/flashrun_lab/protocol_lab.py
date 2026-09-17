"""Protocol schema and signature oracle."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7


class ProtocolError(ValueError):
    """Raised when a protocol artifact is invalid."""


@dataclass(frozen=True)
class EndpointSchema:
    name: str
    method: str
    path: str
    auth_headers: tuple[str, ...]
    query_fields: tuple[str, ...]
    body_fields: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EndpointSchema":
        missing = [key for key in ("name", "method", "path") if key not in data]
        if missing:
            raise ProtocolError(f"endpoint schema missing fields: {missing}")
        return cls(
            name=str(data["name"]),
            method=str(data["method"]).upper(),
            path=str(data["path"]),
            auth_headers=tuple(data.get("auth_headers", [])),
            query_fields=tuple(data.get("query_fields", [])),
            body_fields=tuple(data.get("body_fields", [])),
        )


def load_endpoint_map(path: str | Path) -> dict[str, EndpointSchema]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {name: EndpointSchema.from_dict(item) for name, item in raw.items()}


def sha256_reorder(hex_digest: str) -> str:
    """Swap the first 8 and last 8 hex characters of a SHA-256 digest."""
    if len(hex_digest) != 64:
        raise ProtocolError("SHA-256 hex digest must be 64 characters")
    return hex_digest[-8:] + hex_digest[8:-8] + hex_digest[:8]


def pad_key(key: str, length: int = 32) -> bytes:
    """Encode a key as bytes and right-pad with zero bytes."""
    raw = key.encode("utf-8")
    if len(raw) > length:
        raise ProtocolError("key is longer than requested block size")
    return raw.ljust(length, b"\x00")


def aes_cbc_pkcs7_encrypt(plaintext: bytes, key: str, iv: str) -> bytes:
    padded_key = pad_key(key)
    padded_iv = iv.encode("utf-8")
    if len(padded_iv) != 16:
        raise ProtocolError("IV must be 16 bytes after utf-8 encoding")
    padder = PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    encryptor = Cipher(algorithms.AES(padded_key), modes.CBC(padded_iv)).encryptor()
    return encryptor.update(padded_data) + encryptor.finalize()


def compute_sign(payload: str | bytes, key: str, iv: str) -> str:
    """Compute the observed app signature: sha256 -> hex reorder -> AES-CBC -> base64."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    reordered = sha256_reorder(digest)
    encrypted = aes_cbc_pkcs7_encrypt(reordered.encode("ascii"), key, iv)
    return base64.b64encode(encrypted).decode("ascii")


class SignOracle:
    """Validates a captured request by recomputing its signature."""

    def __init__(self, key: str, iv: str) -> None:
        self.key = key
        self.iv = iv

    def recompute(self, payload: str | bytes) -> str:
        return compute_sign(payload, self.key, self.iv)

    def verify_replay(self, payload: str | bytes, expected_sign: str) -> bool:
        actual = self.recompute(payload)
        return actual == expected_sign
