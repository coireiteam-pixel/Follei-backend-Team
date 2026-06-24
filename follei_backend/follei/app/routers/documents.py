import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.core.ids import short_id
from app.models.knowledge.document import Document, DocumentChunk, DocumentPage, KnowledgeSource
from app.models.tenancy import User
from app.routers.auth import get_current_user
from app.schemas.document import (
    DocumentChunkRead,
    DocumentChunkCreateItem,
    DocumentChunkListItem,
    DocumentChunksCreate,
    DocumentChunksCreateResponse,
    DocumentChunksListResponse,
    DocumentCreate,
    DocumentCreateResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentRead,
    DocumentUpdate,
)
from app.services.qdrant import delete_document_vectors

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_ROOT = Path(os.getenv("FOLLEI_UPLOAD_DIR", "uploads/documents"))
SUPPORTED_UPLOAD_TYPES = {
    ".csv": {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"},
    ".doc": {"application/msword", "application/octet-stream"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"},
    ".pdf": {"application/pdf", "application/octet-stream"},
    ".txt": {"text/plain", "application/octet-stream"},
    ".xls": {"application/vnd.ms-excel", "application/octet-stream"},
    ".xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/octet-stream"},
}
UPLOAD_TYPE_LABELS = {
    ".csv": "csv",
    ".doc": "document",
    ".docx": "document",
    ".pdf": "document",
    ".txt": "document",
    ".xls": "excel",
    ".xlsx": "excel",
}


def _unique_document_id(db: Session) -> str:
    for _ in range(100):
        document_id = short_id()
        if db.get(Document, document_id) is None:
            return document_id
    raise HTTPException(status_code=500, detail="Unable to generate unique document id")


def _document_value(document: Document, *names: str) -> Any:
    for name in names:
        if hasattr(document, name):
            value = getattr(document, name)
            if value is not None:
                return value
    return None


def _chunk_text(chunk: DocumentChunk) -> str:
    return _document_value(chunk, "text", "content") or ""


def _safe_filename(filename: str) -> str:
    cleaned = Path(filename).name.strip()
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", cleaned)
    return cleaned or "upload.bin"


def _validate_upload_type(filename: str, content_type: str) -> tuple[str, str]:
    extension = Path(filename).suffix.lower()
    allowed_content_types = SUPPORTED_UPLOAD_TYPES.get(extension)
    if allowed_content_types is None:
        supported = ", ".join(sorted(SUPPORTED_UPLOAD_TYPES))
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Supported extensions: {supported}")

    if content_type not in allowed_content_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported content type '{content_type}' for {extension} files",
        )

    return extension, UPLOAD_TYPE_LABELS[extension]


def _parse_upload_metadata(metadata: Optional[str]) -> dict[str, Any]:
    if not metadata:
        return {}

    try:
        parsed = json.loads(metadata)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=422, detail="metadata must be valid JSON") from exc

    if not isinstance(parsed, dict):
        raise HTTPException(status_code=422, detail="metadata must be a JSON object")
    return parsed


def _document_create_kwargs(
    *,
    tenant_id: str,
    source_id: Optional[str],
    filename: str,
    file_path: Optional[str],
    file_type: str,
    file_size: Optional[int],
    status_value: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    tags = metadata.get("tags") if isinstance(metadata.get("tags"), list) else []
    kwargs: dict[str, Any] = {
        "tenant_id": tenant_id,
        "source_id": source_id,
        "status": status_value,
        "metadata_": metadata,
    }

    if hasattr(Document, "filename"):
        kwargs.update(filename=filename, file_path=file_path, file_type=file_type, file_size=file_size)
    else:
        kwargs.update(title=filename, path=file_path, source_type=file_type, mime_type=file_type, tags=tags)
    return kwargs


def _chunk_create_kwargs(
    *,
    tenant_id: str,
    document_id: str,
    chunk_index: int,
    text: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "tenant_id": tenant_id,
        "document_id": document_id,
        "chunk_index": chunk_index,
        "metadata_": metadata,
    }
    if hasattr(DocumentChunk, "text"):
        kwargs["text"] = text
    else:
        kwargs["content"] = text
    return kwargs


def _ensure_tenant(current_user: User, tenant_id: str) -> None:
    if tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")


def _get_document_or_404(db: Session, current_user: User, document_id: str) -> Document:
    document = (
        db.query(Document)
        .options(selectinload(Document.chunks), selectinload(Document.pages))
        .filter(Document.id == document_id, Document.tenant_id == current_user.tenant_id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _validate_source(db: Session, tenant_id: str, source_id: Optional[str]) -> None:
    if source_id is None:
        return

    source = (
        db.query(KnowledgeSource)
        .filter(KnowledgeSource.id == source_id, KnowledgeSource.tenant_id == tenant_id)
        .first()
    )
    if not source:
        raise HTTPException(status_code=404, detail="Knowledge source not found")


def _document_response(document: Document) -> DocumentCreateResponse:
    return DocumentCreateResponse(
        id=document.id,
        source_id=document.source_id,
        filename=_document_value(document, "filename", "title"),
        file_type=_document_value(document, "file_type", "source_type", "mime_type") or "application/octet-stream",
        status=document.status,
        total_pages=len(document.pages or []),
        total_chunks=len(document.chunks or []),
        tenant_id=document.tenant_id,
        created_at=document.created_at,
    )


def _chunk_response(chunk: DocumentChunk) -> DocumentChunkRead:
    metadata: dict[str, Any] = chunk.metadata_ or {}
    return DocumentChunkRead(
        id=chunk.id,
        index=chunk.chunk_index,
        page=_document_value(chunk, "page") or metadata.get("page") or metadata.get("page_number"),
        heading=metadata.get("heading"),
    )


def _chunk_list_item(chunk: DocumentChunk) -> DocumentChunkListItem:
    metadata: dict[str, Any] = chunk.metadata_ or {}
    tags = _document_value(chunk, "tags")
    if tags is None:
        tags = metadata.get("tags") if isinstance(metadata.get("tags"), list) else []
    return DocumentChunkListItem(
        id=chunk.id,
        index=chunk.chunk_index,
        page=_document_value(chunk, "page") or metadata.get("page") or metadata.get("page_number"),
        heading=_document_value(chunk, "heading") or metadata.get("heading"),
        text=_chunk_text(chunk),
        section=_document_value(chunk, "section") or metadata.get("section"),
        tags=tags,
        embedding_hash=_document_value(chunk, "embedding_hash") or metadata.get("embedding_hash"),
        vector_id=_document_value(chunk, "vector_id") or metadata.get("vector_id"),
    )


@router.post("", response_model=DocumentCreateResponse, status_code=status.HTTP_201_CREATED)
def create_document(
    payload: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentCreateResponse:
    _ensure_tenant(current_user, payload.tenant_id)
    _validate_source(db, current_user.tenant_id, payload.source_id)

    document = Document(
        id=_unique_document_id(db),
        **_document_create_kwargs(
            tenant_id=current_user.tenant_id,
            source_id=payload.source_id,
            filename=payload.filename,
            file_path=payload.file_path,
            file_type=payload.file_type,
            file_size=payload.file_size,
            status_value="pending",
            metadata=dict(payload.metadata),
        )
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return _document_response(document)


@router.post("/upload", response_model=DocumentCreateResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(..., description="Upload CSV, Excel, PDF, Word, or text documents"),
    tenant_id: Optional[str] = Form(default=None),
    source_id: Optional[str] = Form(default=None),
    metadata: Optional[str] = Form(default=None, description='Optional JSON object, for example {"tags":["pricing"]}'),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentCreateResponse:
    if tenant_id is not None:
        _ensure_tenant(current_user, tenant_id)
    _validate_source(db, current_user.tenant_id, source_id)

    filename = _safe_filename(file.filename or "")
    parsed_metadata = _parse_upload_metadata(metadata)
    content_type = file.content_type or "application/octet-stream"
    extension, upload_type = _validate_upload_type(filename, content_type)

    document = Document(
        id=_unique_document_id(db),
        **_document_create_kwargs(
            tenant_id=current_user.tenant_id,
            source_id=source_id,
            filename=filename,
            file_path=None,
            file_type=content_type,
            file_size=None,
            status_value="uploaded",
            metadata={
                **parsed_metadata,
                "file_extension": extension,
                "upload_type": upload_type,
                "original_filename": file.filename,
                "upload_content_type": content_type,
            },
        )
    )
    db.add(document)
    db.flush()

    document_dir = UPLOAD_ROOT / current_user.tenant_id / document.id
    document_dir.mkdir(parents=True, exist_ok=True)
    destination = document_dir / filename

    size = 0
    with destination.open("wb") as output:
        while chunk := file.file.read(1024 * 1024):
            size += len(chunk)
            output.write(chunk)

    if hasattr(document, "file_path"):
        document.file_path = str(destination)
    else:
        document.path = str(destination)
    if hasattr(document, "file_size"):
        document.file_size = size

    metadata_value = dict(document.metadata_ or {})
    metadata_value["stored_path"] = str(destination)
    metadata_value["size_bytes"] = size
    document.metadata_ = metadata_value
    db.commit()
    db.refresh(document)
    return _document_response(document)


@router.get("", response_model=DocumentListResponse)
def list_documents(
    tenant_id: Optional[str] = None,
    source_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    if tenant_id is not None:
        _ensure_tenant(current_user, tenant_id)

    page = max(page, 1)
    chunk_counts = (
        db.query(DocumentChunk.document_id, func.count(DocumentChunk.id).label("total_chunks"))
        .filter(DocumentChunk.tenant_id == current_user.tenant_id)
        .group_by(DocumentChunk.document_id)
        .subquery()
    )
    query = (
        db.query(Document, func.coalesce(chunk_counts.c.total_chunks, 0))
        .outerjoin(chunk_counts, Document.id == chunk_counts.c.document_id)
        .filter(Document.tenant_id == current_user.tenant_id)
    )
    if source_id is not None:
        query = query.filter(Document.source_id == source_id)
    if status is not None:
        query = query.filter(Document.status == status)

    rows = query.order_by(Document.created_at.desc()).offset((page - 1) * 20).limit(20).all()
    return DocumentListResponse(
        items=[
            DocumentListItem(
                id=document.id,
                filename=_document_value(document, "filename", "title"),
                status=document.status,
                total_chunks=total_chunks,
            )
            for document, total_chunks in rows
        ]
    )


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = _get_document_or_404(db, current_user, document_id)
    base = _document_response(document).model_dump()
    return DocumentRead(
        **base,
        summary=document.summary,
        keywords=document.keywords or [],
        metadata=document.metadata_ or {},
        chunks=[_chunk_response(chunk) for chunk in sorted(document.chunks, key=lambda item: item.chunk_index)],
        indexed_at=document.indexed_at,
    )


@router.patch("/{document_id}", response_model=DocumentRead)
def update_document(
    document_id: str,
    payload: DocumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentRead:
    document = _get_document_or_404(db, current_user, document_id)
    update_data = payload.model_dump(exclude_unset=True)

    if "metadata" in update_data:
        document.metadata_ = update_data["metadata"] or {}
        tags = document.metadata_.get("tags")
        if hasattr(document, "tags") and isinstance(tags, list):
            document.tags = tags
    if "status" in update_data:
        document.status = update_data["status"]

    db.commit()
    db.refresh(document)
    return get_document(document_id, current_user, db)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    document = _get_document_or_404(db, current_user, document_id)
    delete_document_vectors(current_user.tenant_id, document.id)
    db.delete(document)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{document_id}/chunks",
    response_model=DocumentChunksCreateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Chunks"],
)
def create_document_chunks(
    document_id: str,
    payload: DocumentChunksCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentChunksCreateResponse:
    document = _get_document_or_404(db, current_user, document_id)
    existing_indexes = {
        chunk_index
        for (chunk_index,) in db.query(DocumentChunk.chunk_index)
        .filter(DocumentChunk.document_id == document.id, DocumentChunk.tenant_id == current_user.tenant_id)
        .all()
    }
    requested_indexes = [chunk.index for chunk in payload.chunks]
    if len(requested_indexes) != len(set(requested_indexes)):
        raise HTTPException(status_code=409, detail="Duplicate chunk index in request")
    duplicates = sorted(set(requested_indexes).intersection(existing_indexes))
    if duplicates:
        raise HTTPException(status_code=409, detail=f"Chunk index already exists: {duplicates[0]}")

    created_chunks: list[DocumentChunk] = []
    seen_pages = set()
    for chunk_in in payload.chunks:
        metadata = {
            "page": chunk_in.page,
            "section": chunk_in.section,
            "heading": chunk_in.heading,
            "tags": chunk_in.tags,
            "embedding_hash": chunk_in.embedding_hash,
            "vector_id": chunk_in.vector_id,
        }
        metadata = {key: value for key, value in metadata.items() if value is not None}
        chunk = DocumentChunk(
            **_chunk_create_kwargs(
                tenant_id=current_user.tenant_id,
                document_id=document.id,
                chunk_index=chunk_in.index,
                text=chunk_in.text,
                metadata=metadata,
            ),
        )
        db.add(chunk)
        created_chunks.append(chunk)

        if chunk_in.page is not None and chunk_in.page not in seen_pages:
            seen_pages.add(chunk_in.page)
            existing_page = (
                db.query(DocumentPage)
                .filter(
                    DocumentPage.document_id == document.id,
                    DocumentPage.tenant_id == current_user.tenant_id,
                    DocumentPage.page_number == chunk_in.page,
                )
                .first()
            )
            if existing_page is None:
                db.add(
                    DocumentPage(
                        tenant_id=current_user.tenant_id,
                        document_id=document.id,
                        page_number=chunk_in.page,
                        metadata_={"source": "chunk_ingestion"},
                    )
                )

    document.status = "indexed"
    document.indexed_at = datetime.utcnow()
    db.commit()
    for chunk in created_chunks:
        db.refresh(chunk)

    return DocumentChunksCreateResponse(
        document_id=document.id,
        chunks_created=len(created_chunks),
        chunks=[
            DocumentChunkCreateItem(
                id=chunk.id,
                index=chunk.chunk_index,
                page=(chunk.metadata_ or {}).get("page"),
            )
            for chunk in sorted(created_chunks, key=lambda item: item.chunk_index)
        ],
    )


@router.get("/{document_id}/chunks", response_model=DocumentChunksListResponse, tags=["Chunks"])
def list_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentChunksListResponse:
    document = _get_document_or_404(db, current_user, document_id)
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id, DocumentChunk.tenant_id == current_user.tenant_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    return DocumentChunksListResponse(items=[_chunk_list_item(chunk) for chunk in chunks])
