from __future__ import annotations
import requests
from typing import Tuple

def usd_to_rub_rate(api_key: str) -> Tuple[float, str]:
    """
    Получает курс USD→RUB с exchangerate-api.com (v6).
    Возвращает (курс, время_последнего_обновления_UTC).
    """
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("result") != "success":
        raise RuntimeError(f"Exchange API error: {data}")
    rate = float(data["conversion_rates"]["RUB"])
    update_time = data.get("time_last_update_utc", "")
    return rate, update_time
