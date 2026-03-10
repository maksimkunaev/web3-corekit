# test_smoke.py
# Smoke tests for all 3 backend modules using FastAPI TestClient
# Run: cd backend && python -m pytest test_smoke.py -v

import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

# Set env vars before importing
os.environ["IS_DEVELOPMENT"] = "True"
os.environ["ALCHEMY_KEY"] = "test"
os.environ["TOKEN_CONTRACT"] = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
os.environ["TOKEN_DECIMALS"] = "6"
os.environ["MIN_HOLDER_BALANCE"] = "0"
os.environ["TOKEN_SYMBOL"] = "TEST"
os.environ["NOWPAYMENTS_API_KEY"] = "test"
os.environ["NOWPAYMENTS_IPN_SECRET"] = "test"

from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


# ==========================================
# Module 1: Auth
# ==========================================


class TestAuthModule:
    def test_health(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_get_nonce(self):
        res = client.get("/api/nonce")
        assert res.status_code == 200
        data = res.json()
        assert "nonce" in data
        assert len(data["nonce"]) == 32  # hex(16) = 32 chars

    def test_status(self):
        res = client.get("/api/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "active_sessions" in data
        assert "active_nonces" in data

    def test_verify_missing_data(self):
        res = client.post("/api/verify", json={})
        assert res.status_code == 400

    def test_verify_missing_signature(self):
        res = client.post("/api/verify", json={"message": "test"})
        assert res.status_code == 400

    def test_session_without_auth(self):
        res = client.get("/api/session")
        assert res.status_code == 401

    def test_signout_without_auth(self):
        res = client.post("/api/signout")
        assert res.status_code == 401


# ==========================================
# Module 2: Crypto Payment
# ==========================================


class TestCryptoPaymentModule:
    def test_get_plans(self):
        res = client.get("/api/crypto/plans")
        assert res.status_code == 200
        data = res.json()
        assert "result" in data
        plans = data["result"]
        assert len(plans) == 3
        plan_ids = [p["id"] for p in plans]
        assert "base_tier" in plan_ids
        assert "pro" in plan_ids
        assert "holder" in plan_ids

    def test_plans_order(self):
        res = client.get("/api/crypto/plans")
        plans = res.json()["result"]
        assert plans[0]["id"] == "base_tier"
        assert plans[1]["id"] == "pro"
        assert plans[2]["id"] == "holder"

    def test_plans_have_features(self):
        res = client.get("/api/crypto/plans")
        plans = res.json()["result"]
        for plan in plans:
            assert "features" in plan
            assert len(plan["features"]) > 0

    def test_subscription_without_auth(self):
        res = client.get("/api/crypto/my-subscription")
        assert res.status_code == 401

    def test_create_invoice_without_auth(self):
        res = client.post("/api/crypto/create-invoice", json={"plan_id": "pro"})
        assert res.status_code == 401

    def test_user_plan_without_auth(self):
        res = client.get("/api/crypto/user-plan")
        assert res.status_code == 401


# ==========================================
# Module 3: Balance Check
# ==========================================


class TestBalanceCheckModule:
    def test_balance_without_auth(self):
        res = client.get("/api/balance")
        assert res.status_code == 401

    def test_is_holder_without_auth(self):
        res = client.get("/api/is-holder")
        assert res.status_code == 401


# ==========================================
# Integration: mock_db
# ==========================================


class TestMockDB:
    def test_save_and_get(self):
        from services.mock_db import save, get, clear

        clear()
        save("test", "key1", {"hello": "world"})
        result = get("test", "key1")
        assert result == {"hello": "world"}

    def test_get_missing(self):
        from services.mock_db import get, clear

        clear()
        result = get("nonexistent", "key")
        assert result is None

    def test_list_keys(self):
        from services.mock_db import save, list_keys, clear

        clear()
        save("coll", "a", 1)
        save("coll", "b", 2)
        keys = list_keys("coll")
        assert sorted(keys) == ["a", "b"]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
