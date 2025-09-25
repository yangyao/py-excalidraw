from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from datetime import datetime, timezone


router = APIRouter()

# in-memory for demo; adjust to persistent store if needed
saved_items: dict[str, object] = {}


@router.post("/v1/projects/{project}/databases/{db}/documents:commit")
async def firebase_commit(project: str, db: str, request: Request):
    # content-type may be text/plain while body is json
    payload = await request.json()
    writes = payload.get("writes", [])
    if not writes:
        return JSONResponse(status_code=400, content={"detail": "no writes"})
    update = writes[0].get("update", {})
    name = update.get("name", "")
    fields = update.get("fields", {})
    if not name:
        return JSONResponse(status_code=400, content={"detail": "missing name"})

    saved_items[name] = fields
    now = datetime.now(timezone.utc).isoformat()
    return {
        "writeResults": [{"updateTime": now}],
        "commitTime": now,
    }


@router.post("/v1/projects/{project}/databases/{db}/documents:batchGet")
async def firebase_batch_get(project: str, db: str, request: Request):
    payload = await request.json()
    docs = payload.get("documents", [])
    if not docs:
        return JSONResponse(status_code=400, content={"detail": "no documents"})
    key = docs[0]
    now = datetime.now(timezone.utc).isoformat()
    if key in saved_items:
        return JSONResponse(
            content=[
                {
                    "found": {
                        "name": key,
                        "fields": saved_items[key],
                        "createTime": now,
                        "updateTime": now,
                    },
                    "readTime": now,
                }
            ]
        )
    return JSONResponse(
        content=[{"missing": key, "readTime": now}]
    )

