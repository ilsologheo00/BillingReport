from app.services.acronis.base import AcronisTenantStatsDTO

_GIB = 1024**3

_TENANT_STATS = [
    AcronisTenantStatsDTO(
        tenant_id="mock-tenant-001", tenant_name="Acme Corp",
        backup_total_bytes=500 * _GIB, backup_used_bytes=210 * _GIB,
        backup_server_count=2, backup_workstation_count=8, backup_vm_count=2, backup_mailboxes_count=2,
        dr_storage_total_bytes=None, dr_storage_used_bytes=50 * _GIB,
    ),
    AcronisTenantStatsDTO(
        tenant_id="mock-tenant-002", tenant_name="Northwind Traders",
        backup_total_bytes=200 * _GIB, backup_used_bytes=180 * _GIB,
        backup_server_count=1, backup_workstation_count=3, backup_vm_count=0, backup_mailboxes_count=1,
        dr_storage_total_bytes=None, dr_storage_used_bytes=0,
    ),
    AcronisTenantStatsDTO(
        tenant_id="mock-tenant-003", tenant_name="Contoso Ltd",
        backup_total_bytes=1024 * _GIB, backup_used_bytes=640 * _GIB,
        backup_server_count=3, backup_workstation_count=14, backup_vm_count=8, backup_mailboxes_count=0,
        dr_storage_total_bytes=None, dr_storage_used_bytes=120 * _GIB,
    ),
]


class MockAcronisProvider:
    """Deterministic fake Acronis data so the integration is demoable without real API credentials."""

    def get_tenant_stats(self) -> list[AcronisTenantStatsDTO]:
        return list(_TENANT_STATS)
