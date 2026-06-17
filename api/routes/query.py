from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from rag.engine import RAGResult, answer

router = APIRouter(tags=["query"])


class QueryRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=512)


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest) -> QueryResponse:
    try:
        result: RAGResult = await answer(req.q)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return QueryResponse(answer=result.answer, sources=result.sources)
