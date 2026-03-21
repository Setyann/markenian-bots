import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "data.json"
LEGACY_PATH = BASE_DIR / "data" / "central_bank_rates.json"
NAMESPACE = "central_bank"

_LOCK = asyncio.Lock()


def _default_data() -> dict:
    return {
        "mrk_usd_rate": None,
        "mrk_usd_date": None,
        "updated_at": None,
        "updated_by": None,
    }


def _read_root_sync() -> dict:
    if not DATA_PATH.exists():
        return {}
    try:
        raw = DATA_PATH.read_text(encoding="utf-8")
        root = json.loads(raw) if raw.strip() else {}
    except Exception:
        root = {}
    return root if isinstance(root, dict) else {}


def _read_legacy_sync() -> dict:
    if not LEGACY_PATH.exists():
        return {}
    try:
        raw = LEGACY_PATH.read_text(encoding="utf-8")
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


def _read_data_sync() -> dict:
    root = _read_root_sync()
    data = root.get(NAMESPACE)
    if not isinstance(data, dict):
        data = _read_legacy_sync()
    defaults = _default_data()
    for key, value in defaults.items():
        if key not in data:
            data[key] = value
    return data


def _write_root_sync(root: dict):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(root, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_PATH)


def _write_data_sync(data: dict):
    root = _read_root_sync()
    root[NAMESPACE] = data
    _write_root_sync(root)


def _today_str() -> str:
    return datetime.now().date().isoformat()


async def init_db():
    async with _LOCK:
        data = _read_data_sync()
        _write_data_sync(data)


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
        data["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        data["updated_by"] = int(updated_by) if updated_by is not None else None
        _write_data_sync(data)
