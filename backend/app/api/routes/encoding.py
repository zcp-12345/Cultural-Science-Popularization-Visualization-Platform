"""编码权威源接口。"""
from fastapi import APIRouter, HTTPException

from app.schemas.encoding import (
    CharDescription,
    DescribeRequest,
    SummarizeRequest,
    TextSummary,
)
from app.services.encoding import describe_char, summarize_text

router = APIRouter(prefix="/encoding", tags=["encoding"])


@router.post("/describe", response_model=CharDescription)
def describe(request: DescribeRequest) -> CharDescription:
    if len(request.char) != 1:
        raise HTTPException(status_code=422, detail="char 必须是单个 Unicode 码位")
    return describe_char(request.char)


@router.post("/summarize", response_model=TextSummary)
def summarize(request: SummarizeRequest) -> TextSummary:
    return summarize_text(request.text)
