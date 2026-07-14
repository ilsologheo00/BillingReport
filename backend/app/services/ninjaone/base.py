from typing import Protocol

from pydantic import BaseModel


class NinjaOrgStatsDTO(BaseModel):
    org_name: str
    device_count: int
    sentinelone_count: int


class NinjaApiError(Exception):
    """Raised when the NinjaOne API call fails (auth, network, or unexpected response shape)."""


class NinjaOneProvider(Protocol):
    def get_org_stats(self) -> list[NinjaOrgStatsDTO]: ...
