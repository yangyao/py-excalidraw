from fastapi import APIRouter, Response, Request, HTTPException
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
    items = store.list()
    return [
        {
            "id": it.id,
            "size": it.size,
            "createdAt": it.created_at.isoformat() if it.created_at else None,
            "name": it.name,
        }
        for it in items
    ]


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
