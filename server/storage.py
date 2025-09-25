from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from typing import Protocol, Optional, List, Dict
from datetime import datetime
import json


class DocumentStore(Protocol):
    def find_id(self, id_: str) -> Optional[bytes]:
        ...

    def create(self, data: bytes) -> str:
        ...

    def list(self) -> List["DocumentInfo"]:
        ...

    def delete(self, id_: str) -> bool:
        ...

    def set_name(self, id_: str, name: Optional[str]) -> bool:
        ...

    def get_name(self, id_: str) -> Optional[str]:
        ...


@dataclass
class DocumentInfo:
    id: str
    size: int
    created_at: Optional[datetime] = None
    name: Optional[str] = None


class MemoryStore:
    def __init__(self) -> None:
        self._data: Dict[str, bytes] = {}
        self._meta: Dict[str, datetime] = {}
        self._names: Dict[str, str] = {}

    def find_id(self, id_: str) -> Optional[bytes]:
        return self._data.get(id_)

    def create(self, data: bytes) -> str:
        id_ = uuid.uuid4().hex
        self._data[id_] = data
        self._meta[id_] = datetime.utcnow()
        return id_

    def list(self) -> List[DocumentInfo]:
        items: List[DocumentInfo] = []
        for k, v in self._data.items():
            items.append(DocumentInfo(id=k, size=len(v), created_at=self._meta.get(k), name=self._names.get(k)))
        # sort by created_at desc when available
        items.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        return items

    def delete(self, id_: str) -> bool:
        existed = id_ in self._data
        self._data.pop(id_, None)
        self._meta.pop(id_, None)
        self._names.pop(id_, None)
        return existed

    def set_name(self, id_: str, name: Optional[str]) -> bool:
        if id_ not in self._data:
            return False
        if name is None or name == "":
            self._names.pop(id_, None)
        else:
            self._names[id_] = name
        return True

    def get_name(self, id_: str) -> Optional[str]:
        return self._names.get(id_)


@dataclass
class FilesystemStore:
    base_path: str

    def __post_init__(self) -> None:
        os.makedirs(self.base_path, exist_ok=True)

    def _path(self, id_: str) -> str:
        # keep ID as filename; no extension required
        return os.path.join(self.base_path, id_)

    def find_id(self, id_: str) -> Optional[bytes]:
        p = self._path(id_)
        if not os.path.exists(p):
            return None
        with open(p, "rb") as f:
            return f.read()

    def create(self, data: bytes) -> str:
        id_ = uuid.uuid4().hex
        p = self._path(id_)
        with open(p, "wb") as f:
            f.write(data)
        return id_

    def _meta_path(self, id_: str) -> str:
        return self._path(f"{id_}.meta.json")

    def list(self) -> List[DocumentInfo]:
        items: List[DocumentInfo] = []
        try:
            for name in os.listdir(self.base_path):
                fp = self._path(name)
                if not os.path.isfile(fp):
                    continue
                st = os.stat(fp)
                info = DocumentInfo(
                    id=name,
                    size=st.st_size,
                    created_at=datetime.utcfromtimestamp(int(st.st_mtime)),
                )
                # try read name from meta
                meta_file = self._meta_path(name)
                if os.path.isfile(meta_file):
                    try:
                        with open(meta_file, "r", encoding="utf-8") as mf:
                            meta = json.load(mf)
                            info.name = meta.get("name")
                    except Exception:
                        pass
                items.append(info)
        except FileNotFoundError:
            return []
        items.sort(key=lambda x: x.created_at or datetime.min, reverse=True)
        return items

    def delete(self, id_: str) -> bool:
        p = self._path(id_)
        if os.path.exists(p) and os.path.isfile(p):
            os.remove(p)
            # remove meta too
            mp = self._meta_path(id_)
            if os.path.isfile(mp):
                try:
                    os.remove(mp)
                except Exception:
                    pass
            return True
        return False

    def set_name(self, id_: str, name: Optional[str]) -> bool:
        p = self._path(id_)
        if not (os.path.exists(p) and os.path.isfile(p)):
            return False
        mp = self._meta_path(id_)
        if name is None or name == "":
            # clear name by deleting meta or setting empty
            try:
                if os.path.isfile(mp):
                    os.remove(mp)
            except Exception:
                pass
            return True
        try:
            with open(mp, "w", encoding="utf-8") as mf:
                json.dump({"name": name}, mf, ensure_ascii=False)
            return True
        except Exception:
            return False

    def get_name(self, id_: str) -> Optional[str]:
        mp = self._meta_path(id_)
        if os.path.isfile(mp):
            try:
                with open(mp, "r", encoding="utf-8") as mf:
                    meta = json.load(mf)
                    n = meta.get("name")
                    if isinstance(n, str):
                        return n
            except Exception:
                return None
        return None


def get_store(storage_type: str, local_path: str) -> DocumentStore:
    if storage_type == "filesystem":
        return FilesystemStore(local_path)
    return MemoryStore()
