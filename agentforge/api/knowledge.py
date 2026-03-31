"""知识库 API 端点

提供知识库管理的 RESTful API 接口。
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..knowledge import (
    ObsidianClient,
    NotionClient,
    SyncEngine,
    SyncDirection,
    NoteType
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

obsidian_client: Optional[ObsidianClient] = None
notion_client: Optional[NotionClient] = None
sync_engine: Optional[SyncEngine] = None


async def get_obsidian_client() -> ObsidianClient:
    global obsidian_client
    if obsidian_client is None:
        obsidian_client = ObsidianClient()
        await obsidian_client.initialize()
    return obsidian_client


async def get_sync_engine() -> SyncEngine:
    global sync_engine, notion_client, obsidian_client

    if sync_engine is None:
        obsidian = await get_obsidian_client()
        notion_client = NotionClient()
        sync_engine = SyncEngine(
            obsidian_client=obsidian,
            notion_client=notion_client,
            notion_database_id=""
        )
        await sync_engine.initialize()

    return sync_engine


class CreateNoteRequest(BaseModel):
    title: str
    content: str
    folder: Optional[str] = ""
    tags: Optional[List[str]] = None
    frontmatter: Optional[Dict[str, Any]] = None


class UpdateNoteRequest(BaseModel):
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    frontmatter: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query: str
    tags: Optional[List[str]] = None
    note_type: Optional[str] = None
    limit: Optional[int] = 20


class SyncRequest(BaseModel):
    direction: str = "bidirectional"
    force: bool = False


class ResolveConflictRequest(BaseModel):
    record_id: str
    resolution: str


@router.get("/notes")
async def list_notes(
    note_type: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    client: ObsidianClient = Depends(get_obsidian_client)
):
    notes = client.list_notes(
        note_type=NoteType(note_type) if note_type else None,
        limit=limit,
        offset=offset
    )
    return {
        "notes": [n.to_dict() for n in notes],
        "total": len(client._notes),
        "limit": limit,
        "offset": offset
    }


@router.get("/notes/{note_id}")
async def get_note(
    note_id: str,
    client: ObsidianClient = Depends(get_obsidian_client)
):
    note = client.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note.to_dict()


@router.post("/notes")
async def create_note(
    request: CreateNoteRequest,
    client: ObsidianClient = Depends(get_obsidian_client)
):
    note = await client.create_note(
        title=request.title,
        content=request.content,
        folder=request.folder,
        tags=request.tags,
        frontmatter_data=request.frontmatter
    )
    return note.to_dict()


@router.put("/notes/{note_id}")
async def update_note(
    note_id: str,
    request: UpdateNoteRequest,
    client: ObsidianClient = Depends(get_obsidian_client)
):
    note = await client.update_note(
        note_id=note_id,
        content=request.content,
        tags=request.tags,
        frontmatter_data=request.frontmatter
    )
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note.to_dict()


@router.delete("/notes/{note_id}")
async def delete_note(
    note_id: str,
    client: ObsidianClient = Depends(get_obsidian_client)
):
    success = await client.delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {"deleted": True, "note_id": note_id}


@router.post("/search")
async def search_notes(
    request: SearchRequest,
    client: ObsidianClient = Depends(get_obsidian_client)
):
    results = await client.search(
        query=request.query,
        tags=request.tags,
        note_type=NoteType(request.note_type) if request.note_type else None,
        limit=request.limit
    )
    return {
        "results": [
            {
                "note": r.note.to_dict(),
                "score": r.score,
                "highlights": r.highlights,
                "match_type": r.match_type
            }
            for r in results
        ],
        "query": request.query,
        "count": len(results)
    }


@router.get("/tags")
async def list_tags(
    client: ObsidianClient = Depends(get_obsidian_client)
):
    return {
        "tags": [
            {"name": tag, "count": len(notes)}
            for tag, notes in client._tag_index.items()
        ],
        "total": len(client._tag_index)
    }


@router.get("/notes/{note_id}/backlinks")
async def get_backlinks(
    note_id: str,
    client: ObsidianClient = Depends(get_obsidian_client)
):
    backlinks = client.get_backlinks(note_id)
    return {
        "note_id": note_id,
        "backlinks": [n.to_dict() for n in backlinks],
        "count": len(backlinks)
    }


@router.get("/graph")
async def get_knowledge_graph(
    client: ObsidianClient = Depends(get_obsidian_client)
):
    return client.get_graph_data()


@router.get("/stats")
async def get_stats(
    client: ObsidianClient = Depends(get_obsidian_client)
):
    return client.get_stats()


@router.post("/sync")
async def sync_knowledge(
    request: SyncRequest,
    engine: SyncEngine = Depends(get_sync_engine)
):
    direction_map = {
        "to_notion": SyncDirection.TO_NOTION,
        "to_obsidian": SyncDirection.TO_OBSIDIAN,
        "bidirectional": SyncDirection.BIDIRECTIONAL
    }

    result = await engine.sync(
        direction=direction_map.get(request.direction, SyncDirection.BIDIRECTIONAL),
        force=request.force
    )

    return result.to_dict()


@router.get("/sync/status")
async def get_sync_status(
    engine: SyncEngine = Depends(get_sync_engine)
):
    return engine.get_sync_status()


@router.post("/sync/conflicts")
async def detect_conflicts(
    engine: SyncEngine = Depends(get_sync_engine)
):
    conflicts = engine.detect_conflicts()
    return {
        "conflicts": [c.to_dict() for c in conflicts],
        "count": len(conflicts)
    }


@router.post("/sync/resolve")
async def resolve_conflict(
    request: ResolveConflictRequest,
    engine: SyncEngine = Depends(get_sync_engine)
):
    success = await engine.resolve_conflict(
        record_id=request.record_id,
        resolution=request.resolution
    )
    if not success:
        raise HTTPException(status_code=400, detail="解决冲突失败")
    return {"resolved": True, "record_id": request.record_id}


@router.get("/export/{note_id}")
async def export_note(
    note_id: str,
    format: str = Query("markdown"),
    client: ObsidianClient = Depends(get_obsidian_client)
):
    note = client.get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if format == "markdown":
        content = f"# {note.title}\n\n{note.content}"
        return PlainTextResponse(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{note.title}.md"'
            }
        )
    elif format == "json":
        return note.to_dict()
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式")
