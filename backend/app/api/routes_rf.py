from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.schemas.asm import AirodumpAnalyzeOut, AirodumpAnalyzeRequest
from app.services.airodump import detect_rogue_aps, parse_airodump_csv

router = APIRouter(prefix="/api", tags=["rf"], dependencies=[Depends(verify_token)])


@router.post("/rf/analyze", response_model=AirodumpAnalyzeOut)
async def analyze_rf(payload: AirodumpAnalyzeRequest) -> AirodumpAnalyzeOut:
    parsed = parse_airodump_csv(payload.csv_text)
    return AirodumpAnalyzeOut(
        networks=parsed["networks"],
        clients=parsed["clients"],
        anomalies=detect_rogue_aps(payload.trusted_bssids, parsed["networks"]),
    )
