import asyncio
import json
from pathlib import Path

from handlers.linar_bank import db as linar_db
from handlers.tax_authority import db as tax_db
from handlers.central_bank import db as cb_db


def run(coro):
    return asyncio.run(coro)


async def reset_locks(*modules):
    for mod in modules:
        mod._LOCK = asyncio.Lock()


def test_tax_authority_add_remove_taxpayer(local_tmp, monkeypatch):
    data_path = local_tmp / "data.json"
    legacy_path = local_tmp / "tax_authority.json"
    monkeypatch.setattr(tax_db, "DATA_PATH", data_path)
    monkeypatch.setattr(tax_db, "LEGACY_PATH", legacy_path)

    async def flow():
        await reset_locks(tax_db)
        await tax_db.init_db()
        await tax_db.upsert_taxpayer(
            tg_id=None,
            fullname="Ivan Petrov",
            phone="+374 99 123456",
            source="manual_admin",
            linar_user_id=None,
        )
        taxpayers = await tax_db.list_taxpayers()
        assert len(taxpayers) == 1
        assert taxpayers[0]["fullname"] == "Ivan Petrov"

        removed = await tax_db.delete_taxpayer("+37499123456")
        assert removed is not None

        taxpayers = await tax_db.list_taxpayers()
        assert taxpayers == []

        await tax_db.upsert_taxpayer(
            tg_id=None,
            fullname="Anna Sargsyan",
            phone="098765432",
            source="manual_admin",
            linar_user_id=None,
        )
        removed = await tax_db.delete_taxpayer("Anna Sargsyan")
        assert removed is not None

    run(flow())


def test_linar_and_central_share_root_file(local_tmp, monkeypatch):
    data_path = local_tmp / "data.json"
    legacy_linar = local_tmp / "linar_bank.json"
    legacy_cb = local_tmp / "central_bank_rates.json"
    monkeypatch.setattr(linar_db, "DATA_PATH", data_path)
    monkeypatch.setattr(linar_db, "LEGACY_PATH", legacy_linar)
    monkeypatch.setattr(cb_db, "DATA_PATH", data_path)
    monkeypatch.setattr(cb_db, "LEGACY_PATH", legacy_cb)

    async def flow():
        await reset_locks(linar_db, cb_db)
        await linar_db.init_db()
        await cb_db.init_db()

        user = await linar_db.create_user(123, "Test User", "+37499111222", "client")
        assert user["id"] == 1
        await cb_db.set_mrk_usd_rate(2.5, "2026-03-21", 123)

    run(flow())

    raw = data_path.read_text(encoding="utf-8")
    root = json.loads(raw)
    assert "linar_bank" in root
    assert "central_bank" in root
    assert root["central_bank"]["mrk_usd_rate"] == 2.5
    assert root["linar_bank"]["users"][0]["fullname"] == "Test User"


def test_central_bank_rate_helpers(local_tmp, monkeypatch):
    data_path = local_tmp / "data.json"
    legacy_cb = local_tmp / "central_bank_rates.json"
    monkeypatch.setattr(cb_db, "DATA_PATH", data_path)
    monkeypatch.setattr(cb_db, "LEGACY_PATH", legacy_cb)

    async def flow():
        await reset_locks(cb_db)
        await cb_db.init_db()
        await cb_db.set_mrk_usd_rate(3.14, "2026-03-21", 777)
        rate, date_str = await cb_db.get_latest_mrk_usd_rate()
        assert rate == 3.14
        assert date_str == "2026-03-21"
        today_rate = await cb_db.get_mrk_usd_rate_for_today("2026-03-21")
        assert today_rate == 3.14

    run(flow())
