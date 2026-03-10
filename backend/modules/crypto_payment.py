# modules/crypto_payment.py
# Module 2: Crypto subscription payments via NowPayments
# Provides: plans, subscription status, invoice creation, webhook, plan manager
# Requires: modules.auth (require_auth)
# Optional: modules.balance_check (is_holder) — falls back gracefully if missing

import hashlib
import hmac
import json
import os
from pprint import pprint
import time
import requests
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from modules.auth import require_auth
import asyncio
from datetime import datetime
import traceback

router = APIRouter()

NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "").strip()
NOWPAYMENTS_IPN_SECRET = os.getenv("NOWPAYMENTS_IPN_SECRET")
# NOWPAYMENTS_EMAIL = os.getenv("NOWPAYMENTS_EMAIL")
# NOWPAYMENTS_PASSWORD = os.getenv("NOWPAYMENTS_PASSWORD")
DOMAIN_URL = os.getenv("DOMAIN_URL")
FE_DOMAIN_URL = os.getenv("FE_DOMAIN_URL")

pro_per_days = 30

PLANS = {
    "base_tier": {
        "is_base": True,
        "title": "Lite Reader",
        "price": 0,
        "duration_days": 0,
        "features": [
            {"icon": "book", "title": "Digital Library", "text": "3 books per month"},
            {"icon": "headphones", "title": "Audiobooks", "text": "1 preview daily"},
        ],
        "per_period_label": "free forever",
    },
    "pro": {
        "is_base": False,
        "title": "Pro",
        "price": 9.99,
        "duration_days": pro_per_days,
        "features": [
            {"icon": "book", "title": "Digital Library", "text": "Unlimited books"},
            {
                "icon": "headphones",
                "title": "Audiobooks",
                "text": "Full catalog access",
            },
        ],
        "is_popular": True,
        "per_period_label": f"per {pro_per_days} days",
    },
    "holder": {
        "is_base": False,
        "title": "Collector Edition",
        "price": 0,
        "duration_days": None,
        "features": [
            {"icon": "book", "title": "Digital Library", "text": "Unlimited books"},
            {
                "icon": "headphones",
                "title": "Audiobooks",
                "text": "Full catalog access",
            },
        ],
        "is_popular": False,
        "per_period_label": "for token holders",
        "action_text": "Buy Token",
        "action_url": DOMAIN_URL,
    },
}


def get_plans_config():
    """Fetch plans from DB or use defaults"""
    from services.mock_db import get

    try:
        db_plans = get("config", "plans")
        if db_plans:
            return db_plans
    except:
        pass
    return PLANS


PLAN_LIMITS = {
    "base_tier": {
        "books_borrowed": 3,
        "audio_previews": 1,
        "forum_posts": 10,
        "bookmarks": 5,
    },
    "pro": {
        "books_borrowed": 9999,
        "audio_previews": 9999,
        "forum_posts": 9999,
        "bookmarks": 9999,
    },
    "holder": {
        "books_borrowed": 9999,
        "audio_previews": 9999,
        "forum_posts": 9999,
        "bookmarks": 9999,
    },
}


class InvoiceRequest(BaseModel):
    plan_id: str


# def get_jwt_token():
#     """
#     Authenticate with NOWPayments and get JWT token.
#     Required for subscription deletion operations.
#     """
#     if not NOWPAYMENTS_EMAIL or not NOWPAYMENTS_PASSWORD:
#         print("Missing NOWPAYMENTS_EMAIL or NOWPAYMENTS_PASSWORD for JWT auth.")
#         return None

#     try:
#         response = requests.post(
#             f"{NOWPAYMENTS_API_URL}/auth",
#             json={"email": NOWPAYMENTS_EMAIL, "password": NOWPAYMENTS_PASSWORD},
#             timeout=10,
#         )
#         response.raise_for_status()
#         return response.json().get("token")
#     except Exception as e:
#         print(f"Failed to get JWT token: {e}")
#         return None


# STEP 1: Extract small focused functions from get_active_subscription


# def get_all_nowpayments(limit=500):
#     """Fetch payments from NOWPayments API"""
#     token = get_jwt_token()
#     headers = {"x-api-key": NOWPAYMENTS_API_KEY, "Authorization": f"Bearer {token}"}

#     res = requests.get(
#         f"{NOWPAYMENTS_API_URL}/payment",
#         headers=headers,
#         params={"limit": limit, "sortBy": "updated_at", "orderBy": "desc"},
#         timeout=10,
#     )
#     res.raise_for_status()
#     return res.json().get("data", [])


def filter_wallet_payments(all_payments, wallet):
    """Extract payments for specific wallet"""
    wallet_payments = []
    for pay in all_payments:
        order_str = pay.get("order_id", "")
        if not order_str or "|" not in order_str:
            continue

        parts = order_str.split("|")
        wallet_address = parts[0]
        plan_id = parts[1] if len(parts) > 1 else "pro"

        if wallet != wallet_address:
            continue

        wallet_payments.append(
            {
                "payment_id": pay.get("payment_id"),
                "plan_id": plan_id,
                "payment_status": pay.get("payment_status"),
                "updated_at": pay.get("updated_at"),
            }
        )

    return wallet_payments


def calculate_subscription_status(payment_data):
    """Convert payment to subscription with expire_at and status"""
    now = time.time()
    plans = get_plans_config()

    updated_ts = time.mktime(
        time.strptime(payment_data["updated_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
    )
    plan_config = plans.get(payment_data["plan_id"], plans["pro"])
    duration = plan_config["duration_days"] * 86400
    expire_at = updated_ts + duration

    # Determine status
    if payment_data["payment_status"] == "finished":
        sub_status = "ACTIVE" if expire_at > now else "EXPIRED"
    elif payment_data["payment_status"] in [
        "waiting",
        "confirming",
        "confirmed",
        "sending",
    ]:
        sub_status = "PENDING"
    else:
        sub_status = "FAILED"

    return {
        "payment_id": payment_data["payment_id"],
        "plan_id": payment_data["plan_id"],
        "expire_at": int(expire_at),
        "expire_in_days": max(0, int((expire_at - now) / 86400)),
        "status": sub_status,
        "payment_status": payment_data["payment_status"],
        "created_at": int(updated_ts),  # we use last update as paid date
    }


def get_latest_subscription(subscriptions):
    """Pick best subscription (ACTIVE > PENDING > others)"""
    if not subscriptions:
        return None

    active = [s for s in subscriptions if s["status"] == "ACTIVE"]
    if active:
        latest = max(active, key=lambda s: s["expire_at"])
        return latest

    pending = [s for s in subscriptions if s["status"] == "PENDING"]
    if pending:
        latest = max(pending, key=lambda s: s["expire_at"])
        return latest

    return max(subscriptions, key=lambda s: s["expire_at"])


def get_active_subscription(wallet: str):
    # Try local DB first
    wallet_payments = get_wallet_payments_from_db(wallet)

    print("Wallet payments found in local DB:", len(wallet_payments))

    # # Fallback to API if DB empty
    # if not wallet_payments:
    #     try:
    #         all_payments = get_all_nowpayments()
    #         wallet_payments = filter_wallet_payments(all_payments, wallet)

    #         # Save to DB for next time
    #         for payment in wallet_payments:
    #             save_payment_to_db(wallet, payment)
    #     except Exception as e:
    #         print(f"API fetch failed: {e}")
    #         return None

    if not wallet_payments:
        return None

    # Convert to subscriptions
    subscriptions = [calculate_subscription_status(p) for p in wallet_payments]

    # print("Subscriptions constructed:")
    # pprint(subscriptions)
    # print()

    return get_latest_subscription(subscriptions)


# STEP 2: Database layer


def save_payment_to_db(wallet, payment_data):
    """Save/update payment in local DB"""
    from services.mock_db import get, save

    user_data = get("wallet_payments", wallet) or {"payments": {}}
    payment_id = str(payment_data["payment_id"])

    user_data["payments"][payment_id] = {
        "plan_id": payment_data["plan_id"],
        "payment_status": payment_data["payment_status"],
        "updated_at": payment_data["updated_at"],
    }

    save("wallet_payments", wallet, user_data)


def get_wallet_payments_from_db(wallet):
    """Fetch payments from local DB"""
    from services.mock_db import get

    user_data = get("wallet_payments", wallet)
    if not user_data or "payments" not in user_data:
        return []

    return [
        {"payment_id": pid, **pdata} for pid, pdata in user_data["payments"].items()
    ]


# STEP 3: Sync function (keeps NOWPayments as source of truth)


# def sync_all_payments_to_db():
#     print(""" ---- Pull all payments from NOWPayments and update local DB ---""")
#     try:
#         all_payments = get_all_nowpayments(limit=500)

#         # Group by wallet
#         wallet_groups = {}
#         for pay in all_payments:
#             order_str = pay.get("order_id", "")
#             if not order_str or "|" not in order_str:
#                 continue

#             wallet = order_str.split("|")[0]
#             if wallet not in wallet_groups:
#                 wallet_groups[wallet] = []
#             wallet_groups[wallet].append(pay)

#         # Save each wallet's payments
#         for wallet, payments in wallet_groups.items():
#             wallet_filtered = filter_wallet_payments(payments, wallet)
#             for payment in wallet_filtered:
#                 save_payment_to_db(wallet, payment)

#         print(f"Synced {len(wallet_groups)} wallets")
#     except Exception as e:
#         print(f"Sync error: {e}")


@router.get("/crypto/plans")
async def get_plans():
    plans = get_plans_config()
    order = ["base_tier", "pro", "holder"]

    def get_order(k):
        try:
            return order.index(k)
        except ValueError:
            return 999

    sorted_plans = sorted(
        [{"id": k, **v} for k, v in plans.items()], key=lambda x: get_order(x["id"])
    )
    return {"result": sorted_plans}


@router.get("/crypto/my-subscription")
async def get_my_status(session=Depends(require_auth)):
    wallet = session["address"]
    sub = get_active_subscription(wallet)
    print("sub:", sub)

    if not sub or sub.get("status") != "ACTIVE":
        is_active_holder = _check_is_holder(wallet)
        print("is_active_holder:", is_active_holder)

        if is_active_holder:
            return {
                "plan_id": "holder",
                "status": "NO_SUBSCRIPTION",
                "payment_status": "none",
                "expire_at": None,
                "expire_in_days": None,
                "created": None,
                "is_active": True,
                "is_expired": False,
                "features": get_plans_config()["holder"]["features"],
                "per_period_label": PLANS["holder"]["per_period_label"],
            }

    if not sub:
        return {
            "plan_id": "base_tier",
            "per_period_label": "",
            "status": "NO_SUBSCRIPTION",
            "expire_at": 0,
            "is_active": False,
            "is_expired": False,
            "features": [],
        }

    # Determine if subscription is expired but keep showing it
    is_expired = sub["status"] == "EXPIRED"

    return {
        "plan_id": sub["plan_id"],
        "status": sub["status"],  # ACTIVE, PENDING, EXPIRED, FAILED
        "payment_status": sub["payment_status"],
        "expire_at": sub["expire_at"],
        "expire_in_days": sub["expire_in_days"],
        "created": sub["created_at"],
        "is_active": sub["status"] == "ACTIVE",
        "is_expired": is_expired,
        "features": get_plans_config()[sub["plan_id"]]["features"],
    }


@router.post("/crypto/create-invoice")
async def create_invoice(payload: InvoiceRequest, session=Depends(require_auth)):
    wallet = session["address"]
    plans = get_plans_config()
    plan = plans.get(payload.plan_id)

    if not plan or payload.plan_id == "base_tier":
        raise HTTPException(status_code=400, detail="Invalid plan")

    data = {
        "price_amount": plan["price"],
        "price_currency": "usd",
        "order_id": f"{wallet}|{payload.plan_id}|{int(time.time())}",
        "order_description": f"Plan: {plan['title']}",
        "ipn_callback_url": f"{DOMAIN_URL}/api/crypto/webhook",
        "success_url": f"{FE_DOMAIN_URL}/?view=plans&payment_success=true",
        "cancel_url": f"{FE_DOMAIN_URL}/?view=plans&payment_status=cancelled",
    }

    print()
    pprint(data)
    print()
    try:
        res = requests.post(
            f"{NOWPAYMENTS_API_URL}/invoice",
            headers={
                "x-api-key": NOWPAYMENTS_API_KEY,
                "Content-Type": "application/json",
            },
            json=data,
        )
        res.raise_for_status()
        invoice = res.json()
        return {"invoice_url": invoice["invoice_url"], "invoice_id": invoice["id"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def log_webhook(
    body, sorted_json=None, received_sig=None, calculated_sig=None, verified=False
):
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    payment_id = body.get("payment_id", body.get("id", "unknown"))
    filename = f"logs/webhook_{timestamp}_{payment_id}.json"

    log_data = {
        "body": body,
        "sorted_json": sorted_json,
        "received_signature": received_sig,
        "calculated_signature": calculated_sig,
        "signature_verified": verified,
        "timestamp": timestamp,
    }

    with open(filename, "w") as f:
        json.dump(log_data, f, indent=2)


# STEP 5: Updated webhook
@router.post("/crypto/webhook")
async def payment_webhook(request: Request):
    print("---- Payment webhook Received----")

    if not NOWPAYMENTS_IPN_SECRET:
        raise HTTPException(status_code=500, detail="IPN Secret missing")

    # Get raw bytes EXACTLY as NOWPayments sent
    body_bytes = await request.body()

    # Calculate signature on RAW BYTES
    signature = request.headers.get("x-nowpayments-sig")
    calculated_hmac = hmac.new(
        NOWPAYMENTS_IPN_SECRET.encode(),
        body_bytes,
        hashlib.sha512,
    ).hexdigest()

    # Parse AFTER signature calculation
    body = json.loads(body_bytes)

    print("---- payment_webhook body----")
    pprint(body)

    verified = signature == calculated_hmac

    print(f"Received sig: {signature}")
    print(f"Calculated:   {calculated_hmac}")

    log_webhook(body, body_bytes.decode(), signature, calculated_hmac, verified)

    if not verified:
        raise HTTPException(status_code=401, detail="Invalid signature")

    print("✅ Signature verified")

    # Save to DB
    order_id = body.get("order_id", "")
    if not order_id or "|" not in order_id:
        return {"status": "ok"}

    wallet = order_id.split("|")[0]
    plan_id = order_id.split("|")[1] if len(order_id.split("|")) > 1 else "pro"

    updated_at_ms = body.get("updated_at")
    if updated_at_ms:
        updated_at_iso = time.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(updated_at_ms / 1000)
        )
    else:
        updated_at_iso = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())

    payment_data = {
        "payment_id": body.get("payment_id"),
        "plan_id": plan_id,
        "payment_status": body.get("payment_status"),
        "updated_at": updated_at_iso,
    }
    save_payment_to_db(wallet, payment_data)
    print(f"Webhook: Updated payment {payment_data['payment_id']} for {wallet}")
    return {"status": "ok"}


### Plan Manager helper  ###
from typing import Dict, Any


# --- Optional holder check ---


def _check_is_holder(wallet: str) -> bool:
    """Try to use balance_check module if available, otherwise return False"""
    try:
        from modules.balance_check import is_holder

        return is_holder(wallet)
    except ImportError:
        return False


async def get_user_plan(wallet_address: str) -> Dict[str, Any]:
    try:
        sub = get_active_subscription(wallet_address)

        plan_id = "base_tier"
        expire_at = 0

        if sub and sub.get("status") == "ACTIVE":
            plan_id = sub["plan_id"]
            expire_at = sub["expire_at"]
        else:
            if _check_is_holder(wallet_address):
                plan_id = "holder"

        plan_info = PLANS.get(plan_id, PLANS["base_tier"])

        res = {
            "wallet": wallet_address,
            "plan_id": plan_id,
            "is_basic": plan_id == "base_tier",
            "expire_at": expire_at,
            "plan_name": plan_info.get("title", ""),
            "limits": PLAN_LIMITS.get(plan_id, PLAN_LIMITS["base_tier"]),
        }

        return res
    except Exception as e:
        print(f"❌ Plan Manager Error: {e}")
        # Default to base tier on error
        return {
            "wallet": wallet_address,
            "plan_id": "base_tier",
            "is_basic": True,
            "expire_at": 0,
            "plan_name": PLANS["base_tier"]["title"],
            "limits": PLAN_LIMITS["base_tier"],
        }


@router.get("/crypto/user-plan")
async def get_plan_route(session=Depends(require_auth)):
    """Get current user plan with limits"""
    return await get_user_plan(session["address"])


async def current_plan(session: dict = Depends(require_auth)) -> Dict[str, Any]:
    return await get_user_plan(session["address"])


def get_usage(wallet: str, feature: str) -> int:
    """Get current daily usage for a feature."""
    from services.mock_db import get

    today = datetime.now().strftime("%Y-%m-%d")
    user_usage = get("usage_stats", wallet) or {}
    daily_stats = user_usage.get(today, {})
    return daily_stats.get(feature, 0)


def increment_usage(wallet: str, feature: str):
    """Increment daily usage for a feature."""
    from services.mock_db import get, save

    today = datetime.now().strftime("%Y-%m-%d")
    user_usage = get("usage_stats", wallet) or {}

    if today not in user_usage:
        user_usage[today] = {}

    daily_stats = user_usage[today]
    daily_stats[feature] = daily_stats.get(feature, 0) + 1

    save("usage_stats", wallet, user_usage)


def check_limit(wallet: str, feature: str, plan_info: Dict[str, Any]):
    """
    Check if a feature's usage limit has been reached.
    Returns: (is_limited, current_usage, limit)
    """
    limit = plan_info.get("limits", {}).get(feature, 0)
    current_usage = get_usage(wallet, feature)
    return current_usage >= limit, current_usage, limit


from services.mock_db import list_keys, save


def reset_all_wallets():
    wallets = list_keys("wallet_payments")
    print("Found wallets:", wallets)

    for wallet in wallets:
        save("wallet_payments", wallet, {"payments": {}})

    print(f"✅ Reset {len(wallets)} wallets")


# crypto_payment.py
if __name__ == "__main__":
    import asyncio
    from services.mock_db import get, save

    reset_all_wallets()
    # sync_all_payments_to_db()
