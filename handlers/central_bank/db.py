import asyncio
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "central_bank_rates.json"

_LOCK = asyncio.Lock()


def _default_data() -> dict:
    return {
        "mrk_usd_rate": None,
        "mrk_usd_date": None,
        "updated_at": None,
        "updated_by": None,
        "users": [],
        "counters": {
            "users": 0,
        },
    }

def _compute_counters(data: dict):
    counters = data.get("counters") or {}
    users = data.get("users") or []
    max_id = 0
    for user in users:
        max_id = max(max_id, int(user.get("id", 0)))
    counters["users"] = max_id
    data["counters"] = counters


def _ensure_keys(data: dict):
    defaults = _default_data()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
    if not isinstance(data.get("users"), list):
        data["users"] = []
    if "counters" not in data or not isinstance(data["counters"], dict):
        data["counters"] = {}
    _compute_counters(data)


def _read_data_sync() -> dict:
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        data = _default_data()
        _write_data_sync(data)
        return data
    try:
        raw = DATA_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else _default_data()
    except Exception:
        data = _default_data()
    _ensure_keys(data)
    return data


def _write_data_sync(data: dict):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_PATH)


def _today_str() -> str:
    return datetime.now().date().isoformat()


def _next_id(data: dict, key: str) -> int:
    counters = data.setdefault("counters", {})
    counters[key] = int(counters.get(key, 0)) + 1
    return counters[key]


def _normalize_phone(phone: str | None) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def _match_user(data: dict, tg_id: int | None, fullname: str | None, phone: str | None):
    if tg_id is not None:
        for user in data.get("users", []):
            if user.get("tg_id") == tg_id:
                return user
    norm_phone = _normalize_phone(phone)
    if norm_phone:
        for user in data.get("users", []):
            if _normalize_phone(user.get("phone")) == norm_phone:
                return user
    name_key = (fullname or "").strip().casefold()
    if name_key:
        for user in data.get("users", []):
            if (user.get("fullname") or "").strip().casefold() == name_key:
                return user
    return None


def _now_ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


async def init_db():
    async with _LOCK:
        data = _read_data_sync()
        _ensure_keys(data)
        _write_data_sync(data)


async def upsert_user(
    tg_id: int | None,
    fullname: str,
    phone: str | None,
    source: str | None = None,
    linar_user_id: int | None = None,
):
    async with _LOCK:
        data = _read_data_sync()
        user = _match_user(data, tg_id, fullname, phone)
        if user:
            if fullname:
                user["fullname"] = fullname
            if phone is not None:
                user["phone"] = phone
            if source:
                user["source"] = source
            if linar_user_id is not None:
                user["linar_user_id"] = linar_user_id
            user["updated_at"] = _now_ts()
        else:
            user = {
                "id": _next_id(data, "users"),
                "tg_id": tg_id,
                "fullname": fullname,
                "phone": phone,
                "status": "active",
                "source": source,
                "linar_user_id": linar_user_id,
                "created_at": _now_ts(),
                "updated_at": _now_ts(),
            }
            data.setdefault("users", []).append(user)
        _write_data_sync(data)
        return user


async def get_user_by_tg(tg_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for user in data.get("users", []):
            if user.get("tg_id") == tg_id:
                return user
    return None


async def get_user_by_phone(phone: str):
    norm = _normalize_phone(phone)
    async with _LOCK:
        data = _read_data_sync()
        for user in data.get("users", []):
            if phone and user.get("phone") == phone:
                return user
            if norm and _normalize_phone(user.get("phone")) == norm:
                return user
    return None


async def list_users():
    async with _LOCK:
        data = _read_data_sync()
        users = list(data.get("users", []))
    users.sort(key=lambda x: int(x.get("id", 0)))
    return users


async def get_mrk_usd_rate_for_today(today: str | None = None) -> float | None:
    async with _LOCK:
        data = _read_data_sync()
    rate = data.get("mrk_usd_rate")
    rate_date = data.get("mrk_usd_date")
    if rate is None or rate_date is None:
        return None
    if (today or _today_str()) != rate_date:
        return None
    try:
        return float(rate)
    except (TypeError, ValueError):
        return None


async def get_latest_mrk_usd_rate() -> tuple[float | None, str | None]:
    async with _LOCK:
        data = _read_data_sync()
    rate = data.get("mrk_usd_rate")
    rate_date = data.get("mrk_usd_date")
    if rate is None or rate_date is None:
        return None, None
    try:
        return float(rate), str(rate_date)
    except (TypeError, ValueError):
        return None, None


async def set_mrk_usd_rate(rate: float, date_str: str | None, updated_by: int | None):
    if date_str is None:
        date_str = _today_str()
    async with _LOCK:
        data = _read_data_sync()
        data["mrk_usd_rate"] = float(rate)
        data["mrk_usd_date"] = date_str
        data["updated_at"] = datetime.utcnow().isoformat(timespec="seconds")
        data["updated_by"] = int(updated_by) if updated_by is not None else None
        _write_data_sync(data)
