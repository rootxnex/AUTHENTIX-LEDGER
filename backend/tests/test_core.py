"""Backend unit tests — hashing, encryption, RBAC, AI scoring."""
import json
import os
import pytest

# ── Test Hashing ──────────────────────────────────────────────────────────────

def test_sha256_bytes_consistency():
    from app.services.hashing import sha256_bytes
    data = b"hello world"
    assert sha256_bytes(data) == sha256_bytes(data)
    assert len(sha256_bytes(data)) == 64  # hex SHA-256

def test_sha256_string():
    from app.services.hashing import sha256_string
    h = sha256_string("authentix")
    assert isinstance(h, str) and len(h) == 64

def test_canonical_profile_id_stable():
    from app.services.hashing import canonical_profile_id
    h1 = canonical_profile_id("twitter", "https://twitter.com/testuser")
    h2 = canonical_profile_id("twitter", "https://twitter.com/testuser")
    assert h1 == h2

def test_canonical_profile_id_different_platforms():
    from app.services.hashing import canonical_profile_id
    h1 = canonical_profile_id("twitter", "https://twitter.com/testuser")
    h2 = canonical_profile_id("instagram", "https://twitter.com/testuser")
    assert h1 != h2

def test_evidence_bundle_hash_deterministic():
    from app.services.hashing import hash_evidence_bundle
    bundle = {"case_id": "abc", "file_hash": "def", "evidence_type": "SCREENSHOT", "created_at": "2024-01-01T00:00:00Z"}
    assert hash_evidence_bundle(bundle) == hash_evidence_bundle(bundle)


# ── Test Encryption ───────────────────────────────────────────────────────────

def test_encrypt_decrypt_roundtrip():
    from app.services.encryption import encrypt_bytes, decrypt_bytes
    key = os.urandom(32)
    plaintext = b"AUTHENTIX LEDGER secret evidence data"
    ciphertext = encrypt_bytes(plaintext, key)
    assert ciphertext != plaintext
    recovered = decrypt_bytes(ciphertext, key)
    assert recovered == plaintext

def test_encrypt_different_nonces():
    from app.services.encryption import encrypt_bytes
    key = os.urandom(32)
    c1 = encrypt_bytes(b"same data", key)
    c2 = encrypt_bytes(b"same data", key)
    # Different nonces → different ciphertext
    assert c1 != c2

def test_decrypt_wrong_key_fails():
    from app.services.encryption import encrypt_bytes, decrypt_bytes
    from cryptography.exceptions import InvalidTag
    key1 = os.urandom(32)
    key2 = os.urandom(32)
    ciphertext = encrypt_bytes(b"secret", key1)
    with pytest.raises(Exception):  # InvalidTag or similar
        decrypt_bytes(ciphertext, key2)


# ── Test AI Scoring ───────────────────────────────────────────────────────────

def test_heuristic_score_bot_pattern():
    from app.services.ai_client import score_profile
    result = score_profile({
        "follower_count": 5,
        "following_count": 2000,
        "post_count": 500,
        "account_age_days": 10,
        "bio_text": "",
        "username": "user12345678",
    })
    assert result["risk_score"] > 50, "Should flag bot-pattern profile"
    assert result["risk_level"] in ("HIGH", "CRITICAL")

def test_heuristic_score_normal_profile():
    from app.services.ai_client import score_profile
    result = score_profile({
        "follower_count": 1200,
        "following_count": 400,
        "post_count": 200,
        "account_age_days": 1200,
        "bio_text": "Digital journalist covering cybersecurity",
        "username": "journalist_india",
    })
    assert result["risk_score"] < 50, "Should score normal profile low"

def test_score_returns_required_keys():
    from app.services.ai_client import score_profile
    result = score_profile({"follower_count": 100, "following_count": 100})
    assert "risk_score" in result
    assert "risk_level" in result
    assert "risk_factors" in result
    assert 0 <= result["risk_score"] <= 100


# ── Test RBAC ─────────────────────────────────────────────────────────────────

def test_jwt_create_and_decode():
    from app.auth.jwt import create_access_token, decode_token
    token = create_access_token({"sub": "user-123", "role": "INVESTIGATOR"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "INVESTIGATOR"

def test_jwt_invalid_token_raises():
    from app.auth.jwt import decode_token
    from jose import JWTError
    with pytest.raises(JWTError):
        decode_token("obviously.invalid.token")

def test_password_hash_verify():
    from app.auth.jwt import hash_password, verify_password
    hashed = hash_password("MySecret@123")
    assert verify_password("MySecret@123", hashed)
    assert not verify_password("wrongpassword", hashed)
