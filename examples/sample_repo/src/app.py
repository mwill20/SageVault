"""Minimal FastAPI app used for SageVault sample data."""
from fastapi import FastAPI

app = FastAPI(title="Sample Widget Service")

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/widgets")
async def list_widgets() -> dict[str, list[dict[str, str]]]:
    """Return hard-coded widgets so we have deterministic content."""
    return {
        "widgets": [
            {"id": "w-001", "name": "Telemetry Primer", "tier": "starter"},
            {"id": "w-002", "name": "Secure Gateway", "tier": "enterprise"},
        ]
    }
