from app.services.acronis.base import AcronisTenantStatsDTO

_GIB = 1024**3

_TENANT_STATS = [
    AcronisTenantStatsDTO(
        tenant_id="mock-tenant-001", tenant_name="Acme Corp",
        backup_total_bytes=500 * _GIB, backup_used_bytes=210 * _GIB,
        backup_machines_count=12, backup_mailboxes_count=2,
    ),
    AcronisTenantStatsDTO(
        tenant_id="mock-tenant-002", tenant_name="Northwind Traders",
        backup_total_bytes=200 * _GIB, backup_used_bytes=180 * _GIB,
        backup_machines_count=4, backup_mailboxes_count=1,
    ),
    AcronisTenantStatsDTO(
        tenant_id="mock-tenant-003", tenant_name="Contoso Ltd",
        backup_total_bytes=1024 * _GIB, backup_used_bytes=640 * _GIB,
        backup_machines_count=25, backup_mailboxes_count=0,
    ),
]


class MockAcronisProvider:
    """Deterministic fake Acronis data so the integration is demoable without real API credentials."""

    def get_tenant_stats(self) -> list[AcronisTenantStatsDTO]:
        return list(_TENANT_STATS)
