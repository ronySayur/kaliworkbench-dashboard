from app.services.gatt_parser import gatt_summary, parse_bluetoothctl_gatt

BLUETOOTHCTL_MENU_GATT = """
Menu GATT

Primary Service: 0000180a-0000-1000-8000-00805f9b34fb
\tDevice Name
\t00002a29-0000-1000-8000-00805f9b34fb

Primary Service: 0000180f-0000-1000-8000-00805f9b34fb
\tBattery Level
"""

BLUETOOTHCTL_WITH_PROPS = """
Service: 0000180d-0000-1000-8000-00805f9b34fb
    00002a37-0000-1000-8000-00805f9b34fb
"""

def test_parse_primary_service_blocks_with_characteristics() -> None:
    tree = parse_bluetoothctl_gatt(BLUETOOTHCTL_MENU_GATT)
    assert [s["name"] for s in tree] == ["Device Information", "Battery Service"]
    names = [c["name"] for c in tree[0]["characteristics"]]
    assert "Device Name" in names
    assert "Manufacturer Name String" in names


def test_parse_uuid_characteristic_rows() -> None:
    tree = parse_bluetoothctl_gatt(BLUETOOTHCTL_WITH_PROPS)
    assert tree[0]["name"] == "Heart Rate"
    assert tree[0]["characteristics"][0]["uuid"] == "00002a37-0000-1000-8000-00805f9b34fb"
    assert tree[0]["characteristics"][0]["name"] == "Heart Rate Measurement"


def test_gatt_summary_counts_services_and_characteristics() -> None:
    tree = parse_bluetoothctl_gatt(BLUETOOTHCTL_MENU_GATT)
    summary = gatt_summary(tree)
    assert summary["services"] == 2
    assert summary["characteristics"] == 3


def test_parse_empty_text_returns_empty_tree() -> None:
    assert parse_bluetoothctl_gatt("") == []
    assert gatt_summary([]) == {"services": 0, "characteristics": 0}
