# modules/balance_check.py
# Module 3: ERC-20 token balance verification via Alchemy
# Provides: /balance, /is-holder endpoints
# Requires: modules.auth (require_auth)

import os
import time
from functools import lru_cache

from fastapi import APIRouter, Depends
from web3 import Web3

from modules.auth import require_auth

router = APIRouter()

# --- Config from env ---
ALCHEMY_KEY = os.getenv("ALCHEMY_KEY", "")
TOKEN_CONTRACT = os.getenv("TOKEN_CONTRACT", "")
TOKEN_SYMBOL = os.getenv("TOKEN_SYMBOL", "$TOKEN")
TOKEN_DECIMALS = int(os.getenv("TOKEN_DECIMALS", "18"))
MIN_HOLDER_BALANCE = float(os.getenv("MIN_HOLDER_BALANCE", "0"))

# Web3 provider
w3 = Web3(Web3.HTTPProvider(f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_KEY}"))

ERC20_ABI = [
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"type": "address"}],
        "outputs": [{"type": "uint256"}],
    }
]


# --- Core logic ---

def get_token_balance(wallet_address: str) -> float:
    """Get token balance with 5-min cache window"""
    time_window = int(time.time() // 300)
    return _get_cached_balance(wallet_address, time_window)


@lru_cache(maxsize=1024)
def _get_cached_balance(wallet_address: str, time_window: int) -> float:
    try:
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(TOKEN_CONTRACT), abi=ERC20_ABI
        )
        balance = contract.functions.balanceOf(
            Web3.to_checksum_address(wallet_address)
        ).call()
        return balance / 10**TOKEN_DECIMALS
    except Exception as e:
        print(f"Error checking token balance: {e}")
        return 0.0


def is_holder(wallet_address: str) -> bool:
    """Check if wallet holds minimum required tokens"""
    return get_token_balance(wallet_address) >= MIN_HOLDER_BALANCE


# --- Routes ---

@router.get("/balance")
async def get_balance(session=Depends(require_auth)):
    """Get ERC-20 token balance for authenticated user"""
    try:
        balance = get_token_balance(session["address"])
        return {"balance": balance, "symbol": TOKEN_SYMBOL}
    except Exception as e:
        print(f"Error fetching balance for {session['address']}: {e}")
        return {"balance": 0, "symbol": TOKEN_SYMBOL}


@router.get("/is-holder")
async def check_holder(session=Depends(require_auth)):
    """Check if authenticated user is a token holder"""
    try:
        holder = is_holder(session["address"])
        balance = get_token_balance(session["address"])
        return {
            "is_holder": holder,
            "balance": balance,
            "min_required": MIN_HOLDER_BALANCE,
            "symbol": TOKEN_SYMBOL,
        }
    except Exception as e:
        print(f"Error checking holder status: {e}")
        return {"is_holder": False, "balance": 0, "min_required": MIN_HOLDER_BALANCE}
