from typing import Protocol

from pydantic import BaseModel


class AcronisTenantStatsDTO(BaseModel):
    tenant_id: str
    tenant_name: str
    backup_total_bytes: int | None  # None means no fixed quota (e.g. per-workload billing)
    backup_used_bytes: int
    backup_server_count: int
    backup_workstation_count: int
    backup_vm_count: int
    backup_mailboxes_count: int  # protected Microsoft 365 seats; Acronis's API does not expose individual mailbox addresses


class AcronisApiError(Exception):
    """Raised when the Acronis API call fails (auth, network, or unexpected response shape)."""


class AcronisProvider(Protocol):
    def get_tenant_stats(self) -> list[AcronisTenantStatsDTO]: ...
