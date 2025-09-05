from __future__ import annotations
import json
from getpass import getpass
from pathlib import Path
from typing import Dict, Optional

from src.utils.crypto import decrypt_json_bytes

CONFIGS_DIR = Path("/content/configs")
SECRETS_PATH = CONFIGS_DIR / "secrets.enc"

def load_secrets(passphrase: Optional[str] = None) -> Dict[str, str]:
    if not SECRETS_PATH.exists():
        raise FileNotFoundError(f"Encrypted secrets not found at: {SECRETS_PATH}")

    if passphrase is None:
        passphrase = getpass("Введите пароль для расшифровки секретов: ")

    blob = SECRETS_PATH.read_bytes()
    raw = decrypt_json_bytes(blob, passphrase)
    data = json.loads(raw.decode("utf-8"))

    for key in ("OPENAI_API_KEY", "EXCHANGERATE_API_KEY"):
        if key not in data or not data[key]:
            raise ValueError(f"Secret '{key}' is missing or empty.")

    return data
