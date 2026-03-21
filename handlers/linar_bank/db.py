import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data" / "data.json"
LEGACY_PATH = BASE_DIR / "data" / "linar_bank.json"
NAMESPACE = "linar_bank"

DEFAULT_DAILY_LIMIT = 1_000_000.0
DEFAULT_TX_LIMIT = 250_000.0

_LOCK = asyncio.Lock()


def now_ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _default_data() -> dict:
    return {
        "users": [],
        "accounts": [],
        "limits": [],
        "cards": [],
        "transactions": [],
        "credit_applications": [],
        "support_tickets": [],
        "otp_codes": [],
        "audit_logs": [],
        "counters": {
            "users": 0,
            "accounts": 0,
            "cards": 0,
            "transactions": 0,
            "credit_applications": 0,
            "support_tickets": 0,
            "otp_codes": 0,
            "audit_logs": 0,
        },
    }


def _compute_counters(data: dict):
    counters = data.get("counters") or {}
    for key in [
        "users",
        "accounts",
        "cards",
        "transactions",
        "credit_applications",
        "support_tickets",
        "otp_codes",
        "audit_logs",
    ]:
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
    if "counters" not in data or not isinstance(data["counters"], dict):
        _compute_counters(data)
    else:
        _compute_counters(data)


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
    if not data:
        data = _default_data()
    _ensure_keys(data)
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


def _next_id(data: dict, key: str) -> int:
    counters = data.setdefault("counters", {})
    counters[key] = int(counters.get(key, 0)) + 1
    return counters[key]


def _normalize_phone(phone: str) -> str:
    return "".join(ch for ch in (phone or "") if ch.isdigit())


async def init_db():
    async with _LOCK:
        data = _read_data_sync()
        _ensure_keys(data)
        _write_data_sync(data)


async def get_user_by_tg(tg_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("tg_id") == tg_id:
                return user
    return None


async def get_user_by_id(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                return user
    return None


async def get_user_by_phone(phone: str):
    query = _normalize_phone(phone)
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            stored = _normalize_phone(user.get("phone") or "")
            if phone and user.get("phone") == phone:
                return user
            if query and stored and query == stored:
                return user
    return None


async def search_users_by_fullname(query: str, limit: int = 5):
    term = (query or "").strip().casefold()
    async with _LOCK:
        data = _read_data_sync()
        matches = []
        for user in data["users"]:
            if term and term in (user.get("fullname") or "").casefold():
                matches.append(user)
        matches.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
        return matches[:limit]


async def list_users_by_role(role: str):
    async with _LOCK:
        data = _read_data_sync()
        return [u for u in data["users"] if u.get("role") == role]


async def list_users(status: str | None = None):
    async with _LOCK:
        data = _read_data_sync()
        if status is None:
            return list(data["users"])
        return [u for u in data["users"] if u.get("status") == status]


async def create_user(tg_id: int, fullname: str, phone: str | None, role: str):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("tg_id") == tg_id:
                return user
        user = {
            "id": _next_id(data, "users"),
            "tg_id": tg_id,
            "fullname": fullname,
            "phone": phone,
            "role": role,
            "status": "active",
            "pin_hash": None,
            "pin_attempts": 0,
            "created_at": now_ts(),
        }
        data["users"].append(user)
        _write_data_sync(data)
        return user


async def set_user_role(user_id: int, role: str):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                user["role"] = role
                break
        _write_data_sync(data)


async def set_user_status(user_id: int, status: str):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                user["status"] = status
                break
        _write_data_sync(data)


async def set_user_pin(user_id: int, pin_hash: str):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                user["pin_hash"] = pin_hash
                user["pin_attempts"] = 0
                break
        _write_data_sync(data)


async def update_user_profile(user_id: int, fullname: str | None = None, phone: str | None = None):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                if fullname:
                    user["fullname"] = fullname
                if phone is not None:
                    user["phone"] = phone
                break
        _write_data_sync(data)


async def increment_pin_attempts(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                user["pin_attempts"] = int(user.get("pin_attempts") or 0) + 1
                break
        _write_data_sync(data)


async def reset_pin_attempts(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for user in data["users"]:
            if user.get("id") == user_id:
                user["pin_attempts"] = 0
                break
        _write_data_sync(data)


async def create_account(user_id: int, name: str, currency: str, balance: float = 0.0):
    async with _LOCK:
        data = _read_data_sync()
        account = {
            "id": _next_id(data, "accounts"),
            "user_id": user_id,
            "name": name,
            "currency": currency,
            "balance": float(balance),
            "status": "active",
            "created_at": now_ts(),
        }
        data["accounts"].append(account)
        _write_data_sync(data)
        return account


async def get_accounts(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        return [a for a in data["accounts"] if a.get("user_id") == user_id]


async def get_account(account_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for account in data["accounts"]:
            if account.get("id") == account_id:
                return account
    return None


async def update_balance(account_id: int, delta: float):
    async with _LOCK:
        data = _read_data_sync()
        for account in data["accounts"]:
            if account.get("id") == account_id:
                account["balance"] = float(account.get("balance", 0.0)) + float(delta)
                break
        _write_data_sync(data)


async def set_account_status(user_id: int, status: str):
    async with _LOCK:
        data = _read_data_sync()
        for account in data["accounts"]:
            if account.get("user_id") == user_id:
                account["status"] = status
        _write_data_sync(data)


async def ensure_limits(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for limit in data["limits"]:
            if limit.get("user_id") == user_id:
                return limit
        limit = {
            "user_id": user_id,
            "daily_limit": DEFAULT_DAILY_LIMIT,
            "tx_limit": DEFAULT_TX_LIMIT,
        }
        data["limits"].append(limit)
        _write_data_sync(data)
        return limit


async def set_limits(user_id: int, daily_limit: float, tx_limit: float):
    async with _LOCK:
        data = _read_data_sync()
        for limit in data["limits"]:
            if limit.get("user_id") == user_id:
                limit["daily_limit"] = float(daily_limit)
                limit["tx_limit"] = float(tx_limit)
                _write_data_sync(data)
                return
        data["limits"].append({
            "user_id": user_id,
            "daily_limit": float(daily_limit),
            "tx_limit": float(tx_limit),
        })
        _write_data_sync(data)


async def get_limits(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for limit in data["limits"]:
            if limit.get("user_id") == user_id:
                return limit
    return None


async def create_transaction(user_id: int, from_account_id: int | None, to_account_id: int | None,
                             amount: float, fee: float, tx_type: str, status: str, description: str):
    async with _LOCK:
        data = _read_data_sync()
        tx = {
            "id": _next_id(data, "transactions"),
            "user_id": user_id,
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": float(amount),
            "fee": float(fee),
            "type": tx_type,
            "status": status,
            "description": description,
            "created_at": now_ts(),
        }
        data["transactions"].append(tx)
        _write_data_sync(data)
        return tx["id"]


async def update_transaction_status(tx_id: int, status: str):
    async with _LOCK:
        data = _read_data_sync()
        for tx in data["transactions"]:
            if tx.get("id") == tx_id:
                tx["status"] = status
                break
        _write_data_sync(data)


async def list_transactions(user_id: int, limit: int | None = 10):
    async with _LOCK:
        data = _read_data_sync()
        txs = [t for t in data["transactions"] if t.get("user_id") == user_id]
        txs.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
        return txs if limit is None else txs[:limit]


async def list_all_transactions():
    async with _LOCK:
        data = _read_data_sync()
        return list(data["transactions"])


async def create_card(user_id: int, card_number: str, card_type: str = "virtual"):
    async with _LOCK:
        data = _read_data_sync()
        card = {
            "id": _next_id(data, "cards"),
            "user_id": user_id,
            "card_number": card_number,
            "status": "active",
            "type": card_type,
            "created_at": now_ts(),
            "blocked_reason": None,
        }
        data["cards"].append(card)
        _write_data_sync(data)
        return card["id"]


async def get_card_by_user(user_id: int):
    async with _LOCK:
        data = _read_data_sync()
        cards = [c for c in data["cards"] if c.get("user_id") == user_id]
        if not cards:
            return None
        cards.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
        return cards[0]


async def get_card_by_number(card_number: str):
    async with _LOCK:
        data = _read_data_sync()
        for card in data["cards"]:
            if card.get("card_number") == card_number:
                return card
    return None


async def update_card_status(card_id: int, status: str, reason: str | None = None):
    async with _LOCK:
        data = _read_data_sync()
        for card in data["cards"]:
            if card.get("id") == card_id:
                card["status"] = status
                card["blocked_reason"] = reason
                break
        _write_data_sync(data)


async def create_credit_application(user_id: int, amount: float, term_months: int):
    async with _LOCK:
        data = _read_data_sync()
        app = {
            "id": _next_id(data, "credit_applications"),
            "user_id": user_id,
            "amount": float(amount),
            "term_months": int(term_months),
            "status": "review",
            "decision_by": None,
            "decision_reason": None,
            "created_at": now_ts(),
            "decided_at": None,
        }
        data["credit_applications"].append(app)
        _write_data_sync(data)
        return app["id"]


async def list_pending_credit_applications():
    async with _LOCK:
        data = _read_data_sync()
        return [a for a in data["credit_applications"] if a.get("status") == "review"]


async def list_credit_applications(status: str | None = None):
    async with _LOCK:
        data = _read_data_sync()
        if status is None:
            return list(data["credit_applications"])
        return [a for a in data["credit_applications"] if a.get("status") == status]


async def decide_credit_application(app_id: int, status: str, decision_by: int, reason: str | None):
    async with _LOCK:
        data = _read_data_sync()
        for app in data["credit_applications"]:
            if app.get("id") == app_id:
                app["status"] = status
                app["decision_by"] = decision_by
                app["decision_reason"] = reason
                app["decided_at"] = now_ts()
                break
        _write_data_sync(data)


async def create_support_ticket(user_id: int, message: str):
    async with _LOCK:
        data = _read_data_sync()
        ticket = {
            "id": _next_id(data, "support_tickets"),
            "user_id": user_id,
            "message": message,
            "status": "open",
            "operator_id": None,
            "response": None,
            "created_at": now_ts(),
            "responded_at": None,
        }
        data["support_tickets"].append(ticket)
        _write_data_sync(data)
        return ticket["id"]


async def list_open_tickets():
    async with _LOCK:
        data = _read_data_sync()
        return [t for t in data["support_tickets"] if t.get("status") == "open"]


async def respond_ticket(ticket_id: int, operator_id: int, response: str):
    async with _LOCK:
        data = _read_data_sync()
        for ticket in data["support_tickets"]:
            if ticket.get("id") == ticket_id:
                ticket["status"] = "closed"
                ticket["operator_id"] = operator_id
                ticket["response"] = response
                ticket["responded_at"] = now_ts()
                break
        _write_data_sync(data)


async def create_otp(user_id: int, transaction_id: int, code: str, expires_at: str):
    async with _LOCK:
        data = _read_data_sync()
        otp = {
            "id": _next_id(data, "otp_codes"),
            "user_id": user_id,
            "transaction_id": transaction_id,
            "code": code,
            "attempts": 0,
            "expires_at": expires_at,
            "status": "active",
        }
        data["otp_codes"].append(otp)
        _write_data_sync(data)
        return otp["id"]


async def get_otp(otp_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for otp in data["otp_codes"]:
            if otp.get("id") == otp_id:
                return otp
    return None


async def increment_otp_attempts(otp_id: int):
    async with _LOCK:
        data = _read_data_sync()
        for otp in data["otp_codes"]:
            if otp.get("id") == otp_id:
                otp["attempts"] = int(otp.get("attempts") or 0) + 1
                break
        _write_data_sync(data)


async def set_otp_status(otp_id: int, status: str):
    async with _LOCK:
        data = _read_data_sync()
        for otp in data["otp_codes"]:
            if otp.get("id") == otp_id:
                otp["status"] = status
                break
        _write_data_sync(data)


async def log_action(actor_user_id: int, action: str, details: str):
    async with _LOCK:
        data = _read_data_sync()
        log = {
            "id": _next_id(data, "audit_logs"),
            "actor_user_id": actor_user_id,
            "action": action,
            "details": details,
            "created_at": now_ts(),
        }
        data["audit_logs"].append(log)
        _write_data_sync(data)


async def list_logs(limit: int = 20):
    async with _LOCK:
        data = _read_data_sync()
        logs = list(data["audit_logs"])
        logs.sort(key=lambda x: int(x.get("id", 0)), reverse=True)
        return logs[:limit]
