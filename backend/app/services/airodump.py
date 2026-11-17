from __future__ import annotations

import csv
import io
from typing import Any


def parse_airodump_csv(csv_text: str) -> dict[str, list[dict[str, Any]]]:
    blocks: list[list[dict[str, Any]]] = []
    current_rows: list[dict[str, Any]] = []
    fieldnames: list[str] | None = None

    def flush() -> None:
        nonlocal current_rows, fieldnames
        if current_rows:
            blocks.append(current_rows)
        current_rows = []
        fieldnames = None

    reader = csv.reader(io.StringIO(csv_text or ""))
    for raw_fields in reader:
        fields = [f.strip() for f in raw_fields]
        if not fields or all(not f for f in fields):
            flush()
            continue
        if fieldnames is None:
            fieldnames = [f.upper() for f in fields]
            continue
        row = dict(zip(fieldnames, fields))
        current_rows.append(row)
    flush()

    networks = blocks[0] if blocks else []
    clients = blocks[1] if len(blocks) > 1 else []

    parsed_networks: list[dict[str, Any]] = []
    for net in networks:
        ssid = net.get("ESSID") or net.get("ESSID ") or ""
        if ssid == "<length: 0>":
            ssid = ""
        try:
            rssi = int(net.get("POWER") or "0")
        except (TypeError, ValueError):
            rssi = 0
        parsed_networks.append(
            {
                "bssid": (net.get("BSSID") or "").upper(),
                "ssid": ssid,
                "channel": net.get("CHANNEL"),
                "rssi": rssi,
                "encryption": net.get("PRIVACY"),
                "cipher": net.get("CIPHER"),
                "auth": net.get("AUTH"),
            }
        )

    parsed_clients: list[dict[str, Any]] = []
    for client in clients:
        station = (client.get("STATION") or client.get("STATION MAC") or "").upper()
        ap = (client.get("BSSID") or "").upper()
        try:
            power = int(client.get("POWER") or "0")
        except (TypeError, ValueError):
            power = 0
        parsed_clients.append(
            {
                "station": station,
                "ap": ap,
                "power": power,
                "packets": client.get("# PACKETS"),
                "probed_essids": client.get("PROBED ESSIDS"),
            }
        )

    return {"networks": parsed_networks, "clients": parsed_clients}


def detect_rogue_aps(
    trusted_bssids: list[str],
    networks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    trusted = {b.upper() for b in trusted_bssids}
    seen_by_ssid: dict[str, list[str]] = {}
    for net in networks:
        ssid = str(net.get("ssid") or "").strip().lower()
        if not ssid:
            continue
        seen_by_ssid.setdefault(ssid, []).append(str(net.get("bssid") or "").upper())

    anomalies: list[dict[str, Any]] = []
    for ssid, bssids in seen_by_ssid.items():
        untrusted = sorted({b for b in bssids if b not in trusted})
        if untrusted:
            anomalies.append(
                {
                    "ssid": ssid,
                    "bssids": untrusted,
                    "reason": "SSID present on unrecognized BSSID(s) (possible evil twin)",
                }
            )
    return anomalies
