from __future__ import annotations

import ipaddress

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.allowed_scope import AllowedScope


def _normalize_domain(value: str) -> str:
    return value.strip().lower().rstrip(".")


async def validate_target(
    session: AsyncSession, workspace_id: int, target: str
) -> tuple[bool, str]:
    target = (target or "").strip()
    if not target:
        return False, "empty target"

    result = await session.execute(
        select(AllowedScope).where(AllowedScope.workspace_id == workspace_id)
    )
    scopes = list(result.scalars().all())
    if not scopes:
        return False, "no allowlist entries for workspace"

    # IP address target
    try:
        ip_obj = ipaddress.ip_address(target)
        for scope in scopes:
            value = scope.value.strip()
            if scope.target_type == "IP":
                try:
                    if ipaddress.ip_address(value) == ip_obj:
                        return True, f"matched IP scope {value}"
                except ValueError:
                    continue
            elif scope.target_type == "CIDR":
                try:
                    if ip_obj in ipaddress.ip_network(value, strict=False):
                        return True, f"matched CIDR scope {value}"
                except ValueError:
                    continue
    except ValueError:
        ip_obj = None

    # Domain/hostname target
    norm_target = _normalize_domain(target)
    for scope in scopes:
        if scope.target_type == "Domain":
            norm_scope = _normalize_domain(scope.value)
            if norm_target == norm_scope or norm_target.endswith("." + norm_scope):
                return True, f"matched Domain scope {scope.value}"

    # CIDR target must be within an allowed CIDR
    try:
        net_obj = ipaddress.ip_network(target, strict=False)
        for scope in scopes:
            if scope.target_type == "CIDR":
                try:
                    allowed_net = ipaddress.ip_network(scope.value.strip(), strict=False)
                    if net_obj.version == allowed_net.version and net_obj.subnet_of(allowed_net):
                        return True, f"matched CIDR scope {scope.value}"
                except ValueError:
                    continue
    except ValueError:
        pass

    return False, "target not in allowlist"
