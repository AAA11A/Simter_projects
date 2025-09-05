
from __future__ import annotations
import json
from getpass import getpass
from pathlib import Path

from src.utils.crypto import encrypt_json_bytes

def main():
    print("=== Инициализация зашифрованных секретов ===")
    openai_key = getpass("Вставьте ваш OPENAI_API_KEY (ввод скрыт): ")
    fx_key = getpass("Вставьте ваш EXCHANGERATE_API_KEY (ввод скрыт): ")
    passphrase = getpass("Придумайте пароль для шифрования: ")
    passphrase2 = getpass("Повторите пароль: ")
    if passphrase != passphrase2:
        print("Пароли не совпадают. Повторите запуск.")
        return

    payload = {
        "OPENAI_API_KEY": openai_key.strip(),
        "EXCHANGERATE_API_KEY": fx_key.strip(),
    }
    raw = json.dumps(payload).encode("utf-8")
    blob = encrypt_json_bytes(raw, passphrase)

    configs_dir = Path("/content/configs")
    configs_dir.mkdir(parents=True, exist_ok=True)
    out_path = configs_dir / "secrets.enc"
    out_path.write_bytes(blob)

    print(f"✅ Готово. Секреты сохранены в: {out_path}")
    print("Пароль нужно будет вводить при запуске программы.")

if __name__ == "__main__":
    main()
