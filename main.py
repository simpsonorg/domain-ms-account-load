from fastapi import FastAPI, Request
import httpx, os, asyncio

app = FastAPI(title="domain-ms-account-load")

CRUD_DB_URL = os.getenv("CRUD_DB_URL", "http://crud-db:8004")
CRUD_FDR_URL = os.getenv("CRUD_FDR_URL", "http://crud-fdr:8005")

@app.post("/account/load")
async def domain_account_load(request: Request):
    payload = await request.json()
    payload["domainProcessed"] = True
    async with httpx.AsyncClient() as client:
        db_call = client.get(CRUD_DB_URL + "/demographic/" + str(payload.get("customerId")))
        fdr_call = client.get(CRUD_FDR_URL + "/fdr/account/" + str(payload.get("accountId")))
        resp_db, resp_fdr = await asyncio.gather(db_call, fdr_call)
    return {
        "status": "ok",
        "db": resp_db.json(),
        "fdr": resp_fdr.json()
    }
# domain-ms-account-load/main.py
def new_feature():
    pass


@app.get("/health")
async def health():
    return {"status": "domain-up"}
