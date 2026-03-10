# web3-corekit — Developer Guide

Technical documentation for the modular Web3 toolkit.

---

## 🏗 System Overview

Three independent modules:
1. **Auth** (`modules/auth.py`): SIWE wallet authentication.
2. **Crypto Payment** (`modules/crypto_payment.py`): Subscription + plan management.
3. **Balance Check** (`modules/balance_check.py`): ERC-20 token balance verification.

---

## 💳 Crypto Payment Module

### Subscription Plans (Example: Book Store)

| Plan | Price | Duration | Key Feature |
|------|-------|----------|-------------|
| `base_tier` | Free | Forever | 3 books / month |
| `pro` | $9.99 | 30 days | Unlimited + Audio |
| `holder` | Free | Unlimited | Collector perks |

### Webhook Security
Verifies NowPayments IPN signatures using HMAC-SHA512 on raw request bytes.

### Order ID Format
`{wallet_address}|{plan_id}|{timestamp}`

---

## 🔐 Auth Module (SIWE)
Uses Sign-In with Ethereum. 
1. `GET /api/nonce`
2. `POST /api/verify` (with signature)
3. Session stored in httponly cookie.

---

## 💰 Balance Check Module
Queries `balanceOf()` via Alchemy RPC. Results cached for 5 minutes.

---

## 🗄 Database (Mock DB)
In-memory key-value store (`services/mock_db.py`).
- `save(collection, key, value)`
- `get(collection, key)`
- `list_keys(collection)`
