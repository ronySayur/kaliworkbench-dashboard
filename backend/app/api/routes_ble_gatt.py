from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.schemas.ble_gatt import BleScanOut, BleScanRequest, GattParseOut, GattParseRequest
from app.services.ble_adapter import scan_ble, summarize_scan
from app.services.gatt_parser import gatt_summary, parse_bluetoothctl_gatt

router = APIRouter(prefix="/api", tags=["ble-gatt"], dependencies=[Depends(verify_token)])


@router.post("/ble/scan", response_model=BleScanOut)
async def ble_scan_endpoint(payload: BleScanRequest) -> BleScanOut:
    devices = await scan_ble(timeout=payload.timeout)
    return BleScanOut(summary=summarize_scan(devices), devices=devices)


@router.post("/gatt/parse", response_model=GattParseOut)
async def gatt_parse_endpoint(payload: GattParseRequest) -> GattParseOut:
    services = parse_bluetoothctl_gatt(payload.text)
    return GattParseOut(summary=gatt_summary(services), services=services)
