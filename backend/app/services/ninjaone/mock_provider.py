from app.services.ninjaone.base import NinjaOrgStatsDTO

_ORG_STATS = [
    NinjaOrgStatsDTO(org_name="Acme Corp", device_count=42, sentinelone_count=38),
    NinjaOrgStatsDTO(org_name="Northwind Traders", device_count=17, sentinelone_count=17),
    NinjaOrgStatsDTO(org_name="Contoso Ltd", device_count=63, sentinelone_count=50),
    NinjaOrgStatsDTO(org_name="Globex Inc", device_count=9, sentinelone_count=0),
]


class MockNinjaOneProvider:
    """Deterministic fake NinjaOne data so the integration is demoable without real API credentials."""

    def get_org_stats(self) -> list[NinjaOrgStatsDTO]:
        return list(_ORG_STATS)
