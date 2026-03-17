import asyncio
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "tax_authority.json"

_LOCK = asyncio.Lock()


def now_ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def _default_data() -> dict:
    return {
        "taxpayers": [],
        "penalties": [],
        "counters": {
            "taxpayers": 0,
            "penalties": 0,
        },
    }


def _compute_counters(data: dict):
    counters = data.get("counters") or {}
    for key in ["taxpayers", "penalties"]:
        items = data.get(key, [])
        max_id = 0
        for item in items:
            max_id = max(max_id, int(item.get("id", 0)))
        counters[key] = max_id
    data["counters"] = counters


def _ensure_keys(data: dict):
    defaults = _default_data()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
    if not isinstance(data.get("taxpayers"), list):
        data["taxpayers"] = []
    if not isinstance(data.get("penalties"), list):
        data["penalties"] = []
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


def _next_id(data: dict, key: str) -> int:
    counters = data.setdefault("counters", {})
    counters[key] = int(counters.get(key, 0)) + 1
    return counters[key]


def _normalize_phone(phone: str | None) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


def _match_taxpayer(data: dict, tg_id: int | None, fullname: str | None, phone: str | None):
    if tg_id is not None:
        for user in data.get("taxpayers", []):
            if user.get("tg_id") == tg_id:
                return user
    norm_phone = _normalize_phone(phone)
    if norm_phone:
        for user in data.get("taxpayers", []):
            if _normalize_phone(user.get("phone")) == norm_phone:
                return user
    name_key = (fullname or "").strip().casefold()
    if name_key:
        for user in data.get("taxpayers", []):
            if (user.get("fullname") or "").strip().casefold() == name_key:
                return user
    return None


async def init_db():
    async with _LOCK:
        data = _read_data_sync()
        _ensure_keys(data)
        _write_data_sync(data)


async def upsert_taxpayer(
    tg_id: int | None,
    fullname: str,
    phone: str | None,
    source: str | None = None,
    linar_user_id: int | None = None,
):
    async with _LOCK:
        data = _read_data_sync()
        taxpayer = _match_taxpayer(data, tg_id, fullname, phone)
        if taxpayer:
            if fullname:
                taxpayer["fullname"] = fullname
            if phone is not None:
                taxpayer["phone"] = phone
            if source:
                taxpayer["source"] = source
            if linar_user_id is not None:
                taxpayer["linar_user_id"] = linar_user_id
            taxpayer["updated_at"] = now_ts()
        else:
            taxpayer = {
                "id": _next_id(data, "taxpayers"),
                "tg_id": tg_id,
                "fullname": fullname,
                "phone": phone,
                "status": "active",
                "source": source,
                "linar_user_id": linar_user_id,
                "created_at": now_ts(),
                "updated_at": now_ts(),
            }
            data["taxpayers"].append(taxpayer)
        _write_data_sync(data)
        return taxpayer


async def has_taxpayer(name: str) -> bool:
    key = (name or "").strip().casefold()
    if not key:
        return False
    async with _LOCK:
        data = _read_data_sync()
        for taxpayer in data.get("taxpayers", []):
            if (taxpayer.get("fullname") or "").strip().casefold() == key:
                return True
    return False


async def get_taxpayer_by_name(name: str):
    key = (name or "").strip().casefold()
    if not key:
        return None
    async with _LOCK:
        data = _read_data_sync()
        for taxpayer in data.get("taxpayers", []):
            if (taxpayer.get("fullname") or "").strip().casefold() == key:
                return taxpayer
    return None


async def list_taxpayers():
    async with _LOCK:
        data = _read_data_sync()
        taxpayers = list(data.get("taxpayers", []))
    taxpayers.sort(key=lambda x: int(x.get("id", 0)))
    return taxpayers


async def create_penalty(name: str, amount: float, reason: str, created_by: int | None = None):
    async with _LOCK:
        data = _read_data_sync()
        taxpayer = _match_taxpayer(data, None, name, None)
        penalty = {
            "id": _next_id(data, "penalties"),
            "name": name,
            "amount": float(amount),
            "reason": reason,
            "taxpayer_id": taxpayer.get("id") if taxpayer else None,
            "tg_id": taxpayer.get("tg_id") if taxpayer else None,
            "created_by": created_by,
            "created_at": now_ts(),
        }
        data.setdefault("penalties", []).append(penalty)
        _write_data_sync(data)
        return penalty


async def list_penalties():
    async with _LOCK:
        data = _read_data_sync()
        penalties = list(data.get("penalties", []))
    penalties.sort(key=lambda x: int(x.get("id", 0)))
    return penalties


async def list_penalties_by_name(name: str):
    key = (name or "").strip().casefold()
    if not key:
        return []
    async with _LOCK:
        data = _read_data_sync()
        penalties = [
            p for p in data.get("penalties", [])
            if (p.get("name") or "").strip().casefold() == key
        ]
    penalties.sort(key=lambda x: int(x.get("id", 0)))
    return penalties


async def delete_taxpayer(query: str):
    term = (query or "").strip()
    if not term:
        return None
    norm = _normalize_phone(term)
    async with _LOCK:
        data = _read_data_sync()
        idx = None
        if norm:
            for i, taxpayer in enumerate(data.get("taxpayers", [])):
                if _normalize_phone(taxpayer.get("phone")) == norm:
                    idx = i
                    break
        if idx is None:
            name_key = term.casefold()
            for i, taxpayer in enumerate(data.get("taxpayers", [])):
                if (taxpayer.get("fullname") or "").strip().casefold() == name_key:
                    idx = i
                    break
        if idx is None:
            return None
        removed = data["taxpayers"].pop(idx)
        _write_data_sync(data)
        return removed
