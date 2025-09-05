from __future__ import annotations
import base64
import os
from typing import Tuple
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- KDF (пароль → ключ) ---
def _kdf_from_password(password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))

def derive_key(password: str) -> Tuple[bytes, bytes]:
    """Возвращает (ключ, соль)."""
    salt = os.urandom(16)
    key = _kdf_from_password(password, salt)
    return key, salt

def restore_key(password: str, salt: bytes) -> bytes:
    return _kdf_from_password(password, salt)

# --- Шифрование / Расшифровка ---
def encrypt_json_bytes(plaintext: bytes, password: str) -> bytes:
    key, salt = derive_key(password)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext, None)
    blob = b"|".join([
        base64.b64encode(salt),
        base64.b64encode(nonce),
        base64.b64encode(ct),
    ])
    return blob

def decrypt_json_bytes(blob: bytes, password: str) -> bytes:
    parts = blob.split(b"|")
    if len(parts) != 3:
        raise ValueError("Malformed encrypted blob")
    salt = base64.b64decode(parts[0])
    nonce = base64.b64decode(parts[1])
    ct = base64.b64decode(parts[2])
    key = restore_key(password, salt)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct, None)
