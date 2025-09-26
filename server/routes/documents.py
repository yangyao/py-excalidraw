from fastapi import APIRouter, Response, Request, HTTPException
from urllib.parse import quote
from pydantic import BaseModel

from ..config import settings
from ..storage import get_store


router = APIRouter()
store = get_store(settings.STORAGE_TYPE, settings.LOCAL_STORAGE_PATH)


@router.post("/api/v2/post/")
@router.post("/api/v2/post")
async def create_document(request: Request):
    data = await request.body()
    doc_id = store.create(data)
    return {"id": doc_id}


@router.get("/api/v2/{id}/")
@router.get("/api/v2/{id}")
def get_document(id: str):
    data = store.find_id(id)
    if data is None:
        raise HTTPException(status_code=404, detail="not found")
    return Response(content=data, media_type="application/octet-stream")


@router.get("/api/v2/admin/documents")
def list_documents():
    # Only canvases that can be opened (key present)
    items_all = store.list()
    origin = settings.PUBLIC_ORIGIN or ""
    out = []
    for it in items_all:
        key = store.get_key(it.id)
        if not key:
            continue
        share = f"{origin}/#json={it.id},{quote(key)}"
        out.append({
            "id": it.id,
            "size": it.size,
            "createdAt": it.created_at.isoformat() if it.created_at else None,
            "name": it.name,
            "shareLink": share,
        })
    return out


@router.delete("/api/v2/{id}/")
@router.delete("/api/v2/{id}")
def delete_document(id: str):
    ok = store.delete(id)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return Response(status_code=204)


class NameBody(BaseModel):
    name: str | None = None


@router.post("/api/v2/admin/documents/{id}/name")
def set_document_name(id: str, body: NameBody):
    ok = store.set_name(id, body.name)
    if not ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": id, "name": body.name}


## key endpoints removed (no longer needed by admin UI)


class MetaBody(BaseModel):
    name: str | None = None
    key: str | None = None


@router.post("/api/v2/admin/documents/{id}/meta")
def set_document_meta(id: str, body: MetaBody):
    # Both fields optional, but at least one must be provided
    if body.name is None and body.key is None:
        raise HTTPException(status_code=400, detail="name or key required")
    key_ok = True
    if body.key is not None:
        key_ok = store.set_key(id, body.key)
    name_ok = True
    if body.name is not None:
        name_ok = store.set_name(id, body.name)
    if not key_ok and not name_ok:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": id, "name": body.name if body.name is not None else store.get_name(id)}
