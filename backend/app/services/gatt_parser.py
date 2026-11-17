from __future__ import annotations

import re
from typing import Any

# Honored by bluez's bluetoothctl `menu gatt` session output, e.g.:
#   Service: 0000180a-0000-1000-8000-00805f9b34fb
#       Device Name
#       Manufacturer Name String
# Older dumps use "Primary Service: 0000180a-...".
_SERVICE_RE = re.compile(
    r"^\s*(?:primary\s+)?service\s*:?\s*(?P<uuid>[0-9a-fA-F-]{4,36}|0x[0-9a-fA-F]{4})\b",
    re.IGNORECASE,
)
_UUID_LINE_RE = re.compile(r"^\s*(?P<uuid>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|0x[0-9a-fA-F]{4})\s*$")
_CHAR_RE = re.compile(
    r"^\s+(?P<label>[A-Za-z0-9 ._-]+?)\s*(?:\((?P<uuid>[0-9a-fA-F-]{4,36})\))?\s*$"
)

_KNOWN_SERVICES = {
    "1800": "Generic Access",
    "1801": "Generic Attribute",
    "180a": "Device Information",
    "180d": "Heart Rate",
    "180f": "Battery Service",
    "1812": "Human Interface Device",
    "1816": "Cycling Speed and Cadence",
}

_KNOWN_CHARACTERISTICS = {
    "2a00": "Device Name",
    "2a05": "Service Changed",
    "2a19": "Battery Level",
    "2a29": "Manufacturer Name String",
    "2a37": "Heart Rate Measurement",
    "2a63": "Cycling Measurement",
}


def _short_uuid(uuid: str | None) -> str:
    if not uuid:
        return ""
    uuid = uuid.lower()
    if uuid.startswith("0x"):
        return uuid[2:]
    if uuid == "-":
        return uuid
    if len(uuid) == 4:
        return uuid
    parts = uuid.split("-")
    return parts[0][4:] if parts and parts[0].startswith("0000") else parts[0]


def _lookup(table: dict[str, str], uuid: str | None) -> str | None:
    if not uuid:
        return None
    return table.get(_short_uuid(uuid))


def parse_bluetoothctl_gatt(text: str) -> list[dict[str, Any]]:
    services: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw in (text or "").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue

        match = _SERVICE_RE.match(line)
        if match:
            if current:
                services.append(current)
            uuid = match.group("uuid")
            current = {
                "uuid": uuid,
                "name": _lookup(_KNOWN_SERVICES, uuid) or "Unknown Service",
                "characteristics": [],
            }
            continue

        if current is not None and (line.startswith(" ") or line.startswith("\t")):
            uuid_match = _UUID_LINE_RE.match(line)
            if uuid_match:
                uuid = uuid_match.group("uuid")
                name = _lookup(_KNOWN_CHARACTERISTICS, uuid) or "Unknown Characteristic"
                current["characteristics"].append({"uuid": uuid, "name": name, "properties": "unknown"})
                continue
            char_match = _CHAR_RE.match(line)
            if not char_match:
                continue
            label = char_match.group("label").strip()
            uuid = char_match.group("uuid")
            name = label or _lookup(_KNOWN_CHARACTERISTICS, uuid) or "Unknown Characteristic"
            current["characteristics"].append({"uuid": uuid, "name": name, "properties": "unknown"})

    if current:
        services.append(current)
    return services


def gatt_summary(tree: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "services": len(tree),
        "characteristics": sum(len(s.get("characteristics") or []) for s in tree),
    }
