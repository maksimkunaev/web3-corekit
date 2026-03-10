# web3-corekit — Deployment Guide

## 1. Prerequisites
- **Runtime**: Python 3.10+, Node.js 18+.
- **Database**: Uses in-memory mock DB by default.

## 2. Configuration (`.env`)

Create a `.env` file in `backend/` with the following:

```bash
# --- Server & Domain ---
HOST=0.0.0.0
PORT=9000
DEBUG=False
IS_DEVELOPMENT=False
DOMAIN_URL="https://yourdomain.com"
FE_DOMAIN_URL="https://yourdomain.com"

# --- Payments (NowPayments) ---
NOWPAYMENTS_API_KEY="your_api_key"
NOWPAYMENTS_IPN_SECRET="your_ipn_secret_key"
NOWPAYMENTS_API_PUBLIC_KEY="your_public_key"

# --- Token Balance Requirements ---
ALCHEMY_KEY="your_alchemy_key"
TOKEN_CONTRACT="0x..."
TOKEN_DECIMALS=18
MIN_HOLDER_BALANCE=10
TOKEN_SYMBOL="TOKEN"

# --- Reown / WalletConnect (Frontend) ---
NEXT_PUBLIC_REOWN_PROJECT_ID="your_reown_project_id"
NEXT_PUBLIC_REOWN_APP_NAME="Web3 Corekit"
NEXT_PUBLIC_REOWN_APP_DESCRIPTION="Modular Web3 Toolkit"
NEXT_PUBLIC_REOWN_APP_URL="https://yourdomain.com"
NEXT_PUBLIC_REOWN_DOMAIN="yourdomain.com"
```

## 3. Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd frontend
ln -sf ../backend/.env .env
npm install
npm run dev
```

## 4. Webhook Setup
Set IPN callback to: `https://yourdomain.com/api/crypto/webhook`
