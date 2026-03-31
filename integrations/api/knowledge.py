"""
Knowledge API Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from loguru import logger

from integrations.api.auth import verify_token_dependency


router = APIRouter()


class KnowledgeItem(BaseModel):
    id: str
    title: str
    content: str
    source: str
    tags: List[str]
    created_at: str
    updated_at: Optional[str] = None


class KnowledgeListResponse(BaseModel):
    items: List[KnowledgeItem]
    total: int


class KnowledgeCreate(BaseModel):
    title: str
    content: str
    source: str = "manual"
    tags: List[str] = []


class KnowledgeSearch(BaseModel):
    query: str
    limit: int = 10


knowledge_store: Dict[str, KnowledgeItem] = {}
item_counter = 0


def generate_id() -> str:
    global item_counter
    item_counter += 1
    return f"kb_{item_counter:04d}"


@router.get("", response_model=KnowledgeListResponse)
async def list_knowledge(
    tag: Optional[str] = Query(None, description="Filter by tag"),
    source: Optional[str] = Query(None, description="Filter by source"),
    payload: dict = Depends(verify_token_dependency)
):
    """List all knowledge items"""
    items = list(knowledge_store.values())
    
    if tag:
        items = [i for i in items if tag in i.tags]
    if source:
        items = [i for i in items if i.source == source]
    
    return KnowledgeListResponse(
        items=items,
        total=len(items)
    )


@router.get("/search")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    payload: dict = Depends(verify_token_dependency)
):
    """Search knowledge items"""
    items = list(knowledge_store.values())
    
    query_lower = query.lower()
    results = [
        i for i in items
        if query_lower in i.title.lower() or query_lower in i.content.lower()
    ]
    
    return KnowledgeListResponse(
        items=results[:limit],
        total=len(results)
    )


@router.post("", response_model=KnowledgeItem)
async def create_knowledge(
    item: KnowledgeCreate,
    payload: dict = Depends(verify_token_dependency)
):
    """Create new knowledge item"""
    now = datetime.now().isoformat()
    
    new_item = KnowledgeItem(
        id=generate_id(),
        title=item.title,
        content=item.content,
        source=item.source,
        tags=item.tags,
        created_at=now
    )
    
    knowledge_store[new_item.id] = new_item
    logger.info(f"Created knowledge item: {new_item.id}")
    
    return new_item


@router.get("/{item_id}", response_model=KnowledgeItem)
async def get_knowledge(
    item_id: str,
    payload: dict = Depends(verify_token_dependency)
):
    """Get specific knowledge item"""
    if item_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    return knowledge_store[item_id]


@router.put("/{item_id}", response_model=KnowledgeItem)
async def update_knowledge(
    item_id: str,
    item: KnowledgeCreate,
    payload: dict = Depends(verify_token_dependency)
):
    """Update knowledge item"""
    if item_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    existing = knowledge_store[item_id]
    now = datetime.now().isoformat()
    
    updated = KnowledgeItem(
        id=existing.id,
        title=item.title,
        content=item.content,
        source=item.source,
        tags=item.tags,
        created_at=existing.created_at,
        updated_at=now
    )
    
    knowledge_store[item_id] = updated
    logger.info(f"Updated knowledge item: {item_id}")
    
    return updated


@router.delete("/{item_id}")
async def delete_knowledge(
    item_id: str,
    payload: dict = Depends(verify_token_dependency)
):
    """Delete knowledge item"""
    if item_id not in knowledge_store:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    
    del knowledge_store[item_id]
    logger.info(f"Deleted knowledge item: {item_id}")
    
    return {"status": "deleted", "id": item_id}


@router.get("/tags/list")
async def list_tags(payload: dict = Depends(verify_token_dependency)):
    """List all unique tags"""
    tags = set()
    for item in knowledge_store.values():
        tags.update(item.tags)
    
    return {"tags": sorted(list(tags))}


@router.post("/sync/{source}")
async def sync_knowledge(
    source: str,
    payload: dict = Depends(verify_token_dependency)
):
    """Sync knowledge from external source"""
    logger.info(f"Syncing knowledge from: {source}")
    
    return {
        "status": "synced",
        "source": source,
        "items_added": 0,
        "items_updated": 0
    }
