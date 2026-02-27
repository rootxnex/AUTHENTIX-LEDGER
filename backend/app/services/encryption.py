"""AES-256-GCM encryption / decryption for evidence files."""
import os
import struct
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings

_NONCE_SIZE = 12  # 96-bit nonce for GCM


def encrypt_bytes(plaintext: bytes, key: bytes | None = None) -> bytes:
    """
    Encrypt plaintext using AES-256-GCM.
    Returns: nonce (12 bytes) + ciphertext+tag
    """
    key = key or settings.aes_key_bytes
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    # Prepend nonce length (4 bytes, big-endian) + nonce
    return struct.pack(">I", _NONCE_SIZE) + nonce + ciphertext


def decrypt_bytes(data: bytes, key: bytes | None = None) -> bytes:
    """
    Decrypt AES-256-GCM ciphertext produced by encrypt_bytes.
    """
    key = key or settings.aes_key_bytes
    aesgcm = AESGCM(key)
    nonce_len = struct.unpack(">I", data[:4])[0]
    nonce = data[4 : 4 + nonce_len]
    ciphertext = data[4 + nonce_len :]
    return aesgcm.decrypt(nonce, ciphertext, None)


def encrypt_file(plaintext: bytes) -> bytes:
    """Wrapper for encrypting evidence file content."""
    return encrypt_bytes(plaintext)


def decrypt_file(ciphertext: bytes) -> bytes:
    """Wrapper for decrypting evidence file content."""
    return decrypt_bytes(ciphertext)
