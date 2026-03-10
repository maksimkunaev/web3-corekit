# app.py — web3-corekit
# Minimal FastAPI app. Register only the modules you need.

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="web3-corekit", description="Modular Web3 backend toolkit")

# CORS
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def register_module(module_path: str, prefix: str = ""):
    """Register an API module by import path. Comment out modules you don't need."""
    try:
        from importlib import import_module
        module = import_module(module_path)
        if hasattr(module, "router"):
            app.include_router(module.router, prefix=prefix)
            print(f"✅ Registered: {module_path} at {prefix}")
        else:
            print(f"⚠️ Module {module_path} has no 'router'")
    except ImportError as e:
        print(f"❌ Failed to import {module_path}: {e}")


# === Register modules (comment out what you don't need) ===
register_module("modules.auth", "/api")              # Required: SIWE auth
register_module("modules.crypto_payment", "/api")     # Optional: subscriptions
register_module("modules.balance_check", "/api")      # Optional: token balance


# Health check
@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        if hasattr(route, "methods"):
            print(f"  {route.methods} {route.path}")
    print("=========================\n")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "9000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"

    if debug:
        uvicorn.run("app:app", host=host, port=port, reload=True)
    else:
        uvicorn.run(app, host=host, port=port)
