# modules/auth.py
# Module 1: SIWE (Sign-In with Ethereum) wallet authentication
# Provides: require_auth dependency, nonce/verify/session/signout routes
# Shared by other modules — always register this one.

import os
import re
import secrets
import time
from typing import Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import JSONResponse

from services.mock_db import get, save

IS_DEVELOPMENT = str(os.getenv("IS_DEVELOPMENT", "True")).lower() == "true"

router = APIRouter()

# --- Config ---
SESSION_EXPIRY = 48 * 3600  # 48 hours
IS_SECURE_COOKIE = not IS_DEVELOPMENT


# --- Helpers ---

def generate_nonce():
    nonce = secrets.token_hex(16)
    nonces = get("siwe_nonces", "all") or {}
    nonces[nonce] = {"created_at": time.time(), "used": False}
    save("siwe_nonces", "all", nonces)
    return nonce


def parse_message(message: str):
    try:
        address_match = re.search(
            r"wants you to sign in with your (0x[a-fA-F0-9]{40}) account:", message
        )
        if not address_match:
            address_match = re.search(r"(0x[a-fA-F0-9]{40})", message)
        if not address_match:
            return None, None

        address = address_match.group(1).lower()

        chain_match = re.search(r"Chain ID: (\d+)", message)
        if chain_match and chain_match.group(1) != "undefined":
            chain_id = chain_match.group(1)
        else:
            chain_id = "1"

        return address, chain_id
    except Exception as e:
        print(f"Error parsing message: {e}")
        return None, None


async def require_auth(siwe_session_id: Optional[str] = Cookie(None)):
    """FastAPI dependency — inject into any route that needs authentication.
    Returns dict with 'id', 'address', 'chain_id', 'created_at'.
    Replace this module entirely to swap auth systems."""
    if not siwe_session_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    sessions = get("siwe_sessions", "all") or {}
    session_data = sessions.get(siwe_session_id)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid session")

    if time.time() - session_data["created_at"] > SESSION_EXPIRY:
        del sessions[siwe_session_id]
        save("siwe_sessions", "all", sessions)
        raise HTTPException(status_code=401, detail="Session expired")

    return {"id": siwe_session_id, **session_data}


# --- Routes ---

@router.get("/nonce")
async def get_nonce():
    """Generate and return a nonce for SIWE message signing"""
    nonce = generate_nonce()
    return {"nonce": nonce}


@router.post("/verify")
async def verify_message(data: dict):
    """Verify SIWE signature and create session"""
    try:
        message = data.get("message")
        signature = data.get("signature")

        if not message or not signature:
            raise HTTPException(status_code=400, detail="Missing message or signature")

        address, chain_id = parse_message(message)
        if not address:
            raise HTTPException(status_code=400, detail="Could not parse address")

        nonce_match = re.search(r"Nonce: ([a-fA-F0-9]+)", message)
        if not nonce_match:
            raise HTTPException(status_code=400, detail="No nonce found in message")

        nonce = nonce_match.group(1)
        nonces = get("siwe_nonces", "all") or {}
        nonce_data = nonces.get(nonce)
        if not nonce_data:
            raise HTTPException(status_code=400, detail="Invalid nonce")
        if nonce_data["used"]:
            raise HTTPException(status_code=400, detail="Nonce already used")
        if time.time() - nonce_data["created_at"] > 300:
            raise HTTPException(status_code=400, detail="Nonce expired")

        # Verify signature
        message_hash = encode_defunct(text=message)
        recovered_address = Account.recover_message(message_hash, signature=signature)

        if recovered_address.lower() != address:
            raise HTTPException(status_code=400, detail="Signature verification failed")

        # Mark nonce used
        nonces[nonce]["used"] = True
        save("siwe_nonces", "all", nonces)

        # Create session
        session_id = secrets.token_hex(32)
        sessions = get("siwe_sessions", "all") or {}
        sessions[session_id] = {
            "address": address,
            "chain_id": chain_id,
            "created_at": time.time(),
        }
        save("siwe_sessions", "all", sessions)

        response = JSONResponse(
            {"valid": True, "address": address, "chain_id": chain_id}
        )
        response.set_cookie(
            key="siwe_session_id",
            value=session_id,
            httponly=True,
            secure=IS_SECURE_COOKIE,
            samesite="none" if not IS_DEVELOPMENT else "lax",
            max_age=SESSION_EXPIRY,
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal verification error")


@router.get("/session")
async def get_session(session=__import__("fastapi").Depends(require_auth)):
    """Get current session"""
    return {
        "session": {
            "address": session["address"],
            "chains": [session["chain_id"]],
        }
    }


@router.post("/signout")
async def sign_out(session=__import__("fastapi").Depends(require_auth)):
    """Sign out — delete session"""
    sessions = get("siwe_sessions", "all") or {}
    if session["id"] in sessions:
        del sessions[session["id"]]
        save("siwe_sessions", "all", sessions)

    response = JSONResponse({"success": True})
    response.delete_cookie("siwe_session_id")
    return response


@router.get("/status")
async def status():
    """Health check for auth module"""
    sessions = get("siwe_sessions", "all") or {}
    nonces = get("siwe_nonces", "all") or {}
    return {
        "status": "ok",
        "active_sessions": len(sessions),
        "active_nonces": len([n for n in nonces.values() if not n["used"]]),
    }
