import os
import httpx
import asyncio
from fastapi import FastAPI, Request, HTTPException

app = FastAPI(title="domain-ms-account-load")

# Downstream services
CRUD_DB_URL = os.getenv("CRUD_DB_URL", "http://crud-db:8004")
CRUD_FDR_URL = os.getenv("CRUD_FDR_URL", "http://crud-fdr:8005")


@app.post("/account/load")
async def domain_account_load(request: Request):
    payload = await request.json()

    customer_id = payload.get("customerId")
    account_id = payload.get("accountId")

    if not customer_id or not account_id:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: customerId, accountId"
        )

    payload["domainProcessed"] = True

    async with httpx.AsyncClient(timeout=10.0) as client:
        db_call = client.get(f"{CRUD_DB_URL}/demographic/{customer_id}")
        fdr_call = client.get(f"{CRUD_FDR_URL}/fdr/account/{account_id}")

        resp_db, resp_fdr = await asyncio.gather(db_call, fdr_call)

    if resp_db.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"CRUD-DB failure for customer {customer_id}"
        )

    if resp_fdr.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"FDR service failure for account {account_id}"
        )

    demographic = resp_db.json()
    fdr_data = resp_fdr.json()

    # Validate important DB fields
    required_fields = ["name", "address", "email"]
    missing = [f for f in required_fields if f not in demographic]
    if missing:
        raise HTTPException(
            status_code=502,
            detail=f"CRUD-DB missing required fields: {missing}"
        )

    # Compute new tier logic (triggers cross-service impact)
    balance = fdr_data.get("balance", 0)
    customer_tier = "BASIC"
    if balance > 50000:
        customer_tier = "GOLD"
    if balance > 150000:
        customer_tier = "PLATINUM"

    # Final unified response
    return {
        "status": "ok",
        "domainProcessed": True,
        "validatedAt": "2025-01-12T12:00:00Z",
        "customerTier": customer_tier,
        "customer": demographic,
        "account": fdr_data
    }


# New placeholder feature to trigger PR detection
def new_feature():
    return "placeholder for future extension"

# New placeholder feature to trigger PR detection
def new_featureDetail():
    return "placeholder for future extension"


@app.get("/health")
async def health():
    return {"status": "domain-up"}
