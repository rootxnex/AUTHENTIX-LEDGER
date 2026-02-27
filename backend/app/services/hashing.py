"""SHA-256 hashing utilities for evidence integrity."""
import hashlib
import json
import re
from urllib.parse import urlparse


def sha256_bytes(data: bytes) -> str:
    """Return hex SHA-256 of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(file_path: str) -> str:
    """Compute SHA-256 of a file by path (streaming — safe for large files)."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_string(s: str) -> str:
    """Return hex SHA-256 of a UTF-8 string."""
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def canonical_profile_id(platform: str, profile_url: str) -> str:
    """
    Produce a stable, canonical identifier for a profile.
    Normalises URL and platform so the same profile always gets the same hash.
    """
    parsed = urlparse(profile_url.strip().lower())
    canonical = f"{platform.lower()}::{parsed.netloc}{parsed.path}".rstrip("/")
    return sha256_string(canonical)


def canonical_evidence_bundle(case_id: str, file_hash: str, evidence_type: str, created_at: str) -> dict:
    """
    Returns a deterministic dict used as the evidence bundle for chain anchoring.
    """
    bundle = {
        "case_id": str(case_id),
        "file_hash": file_hash,
        "evidence_type": evidence_type,
        "created_at": created_at,
    }
    # Sort keys for deterministic JSON
    return bundle


def hash_evidence_bundle(bundle: dict) -> str:
    """SHA-256 of deterministically serialized evidence bundle."""
    serialized = json.dumps(bundle, sort_keys=True, separators=(",", ":"))
    return sha256_string(serialized)
