from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any


def parse_nmap_xml(xml_text: str) -> list[dict[str, Any]]:
    text = (xml_text or "").strip()
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []

    assets: list[dict[str, Any]] = []
    for host in root.findall("host"):
        state = host.find("status")
        if state is not None and state.get("state") not in (None, "up"):
            continue
        addr = host.find("address")
        ip = addr.get("addr") if addr is not None else None
        if not ip:
            continue
        os_name = None
        os_node = host.find("os")
        if os_node is not None:
            match = os_node.find("osmatch")
            if match is not None:
                os_name = match.get("name")
        for port in host.findall("./ports/port"):
            state_node = port.find("state")
            if state_node is not None and state_node.get("state") != "open":
                continue
            portid = port.get("portid")
            protocol = port.get("protocol") or "tcp"
            service = port.find("service")
            service_name = service.get("name") if service is not None else None
            version = service.get("version") if service is not None else None
            product = service.get("product") if service is not None else None
            identifier = f"{ip}:{protocol}/{portid}"
            fingerprint = f"{identifier}|{service_name or ''}|{product or ''}|{version or ''}"
            assets.append(
                {
                    "asset_type": "port",
                    "identifier": identifier,
                    "fingerprint": fingerprint,
                    "metadata": {
                        "host": ip,
                        "protocol": protocol,
                        "port": portid,
                        "service": service_name,
                        "product": product,
                        "version": version,
                        "os": os_name,
                    },
                }
            )
    return assets


def diff_assets(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    prev_map = {str(a.get("identifier")): a for a in previous}
    curr_map = {str(a.get("identifier")): a for a in current}

    added = [a for identifier, a in curr_map.items() if identifier not in prev_map]
    removed = [a for identifier, a in prev_map.items() if identifier not in curr_map]
    changed = []
    for identifier in set(prev_map) & set(curr_map):
        before = prev_map[identifier]
        after = curr_map[identifier]
        if before.get("fingerprint") != after.get("fingerprint"):
            changed.append({"before": before, "after": after})
    return {"added": added, "removed": removed, "changed": changed}
