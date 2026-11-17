from __future__ import annotations

import json

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.asset import Asset
from app.models.workspace import Workspace
from app.services.nmap import diff_assets, parse_nmap_xml
from app.services.asset_inventory import list_workspace_assets, upsert_workspace_assets
from app.services.subfinder import parse_subfinder_output
from app.services.airodump import detect_rogue_aps, parse_airodump_csv

NMAP_XML = """
<nmaprun>
  <host>
    <status state="up"/>
    <address addr="127.0.0.1" addrtype="ipv4"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh" product="OpenSSH" version="8.9"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
        <service name="https" product="nginx" version="1.22"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="closed"/>
        <service name="http"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""


def test_parse_nmap_xml_extracts_open_ports() -> None:
    assets = parse_nmap_xml(NMAP_XML)
    assert len(assets) == 2
    identifiers = {a["identifier"] for a in assets}
    assert identifiers == {"127.0.0.1:tcp/22", "127.0.0.1:tcp/443"}
    assert assets[0]["asset_type"] == "port"


def test_parse_nmap_xml_garbage_returns_empty() -> None:
    assert parse_nmap_xml("<not-xml><open>") == []
    assert parse_nmap_xml("") == []


def test_diff_assets_reports_added_and_changed() -> None:
    prev = [{"identifier": "a:tcp/22", "fingerprint": "old", "asset_type": "port"}]
    curr = [
        {"identifier": "a:tcp/22", "fingerprint": "new", "asset_type": "port"},
        {"identifier": "a:tcp/443", "fingerprint": "fresh", "asset_type": "port"},
    ]
    diff = diff_assets(prev, curr)
    assert [a["identifier"] for a in diff["added"]] == ["a:tcp/443"]
    assert [c["after"]["fingerprint"] for c in diff["changed"]] == ["new"]
    assert diff["removed"] == []


def test_parse_subfinder_strips_wildcards_and_dupes() -> None:
    out = parse_subfinder_output("*.example.com\na.example.com\nB.example.com\n#comment\na.example.com")
    assert out == ["example.com", "a.example.com", "b.example.com"]


def test_parse_airodump_csv_blocks() -> None:
    csv_text = (
        "BSSID, First time seen, Last time seen, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key\n"
        "AA:BB:CC:DD:EE:FF, 2026, 2026, 6, 130, WPA2, CCMP, PSK, -42, 100, 0, 192.168.1.1, 8, OfficeWiFi,\n"
        "11:22:33:44:55:66, 2026, 2026, 11, 130, WPA2, CCMP, PSK, -77, 90, 0, 192.168.1.2, 8, OfficeWiFi,\n"
        "\n"
        "Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs\n"
        "DE:AD:BE:EF:00:01, 2026, 2026, -60, 50, AA:BB:CC:DD:EE:FF, OfficeWiFi\n"
    )
    parsed = parse_airodump_csv(csv_text)
    assert len(parsed["networks"]) == 2
    assert parsed["networks"][0]["ssid"] == "OfficeWiFi"
    assert len(parsed["clients"]) == 1
    assert parsed["clients"][0]["station"] == "DE:AD:BE:EF:00:01"
    anomalies = detect_rogue_aps(["AA:BB:CC:DD:EE:FF"], parsed["networks"])
    assert len(anomalies) == 1
    assert anomalies[0]["ssid"] == "officewifi"
    assert anomalies[0]["bssids"] == ["11:22:33:44:55:66"]


@pytest.mark.asyncio
async def test_upsert_workspace_assets_roundtrip(tmp_path) -> None:
    db_path = tmp_path / "assets.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as session:
        ws = Workspace(name="assets-ws", description=None)
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        snapshot = [
            {
                "asset_type": "port",
                "identifier": "127.0.0.1:tcp/22",
                "fingerprint": "127.0.0.1:tcp/22|ssh|OpenSSH|8.9",
                "metadata": {"host": "127.0.0.1", "port": "22"},
            }
        ]
        diff1 = await upsert_workspace_assets(session, ws.id, snapshot)
        await session.commit()
        assert len(diff1["added"]) == 1
        diff2 = await upsert_workspace_assets(session, ws.id, snapshot)
        await session.commit()
        assert diff2["added"] == []
        assert diff2["changed"] == []
        assets = await list_workspace_assets(session, ws.id)
        assert len(assets) == 1
        assert assets[0].identifier == "127.0.0.1:tcp/22"
    await engine.dispose()
