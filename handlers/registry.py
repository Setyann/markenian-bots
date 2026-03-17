from handlers.tax_authority import db as tax_db
from handlers.central_bank import db as central_db


async def sync_user_from_linar(user: dict | None):
    if not user:
        return
    tg_id = user.get("tg_id")
    fullname = user.get("fullname") or ""
    phone = user.get("phone")
    linar_user_id = user.get("id")
    try:
        await tax_db.upsert_taxpayer(
            tg_id=tg_id,
            fullname=fullname,
            phone=phone,
            source="linar_bank",
            linar_user_id=linar_user_id,
        )
    except Exception:
        pass
    try:
        await central_db.upsert_user(
            tg_id=tg_id,
            fullname=fullname,
            phone=phone,
            source="linar_bank",
            linar_user_id=linar_user_id,
        )
    except Exception:
        pass
