export interface SyncLog {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed";
  customers_synced: number;
  lines_synced: number;
  error_message: string | null;
}

export interface NinjaSyncLog {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed";
  orgs_matched: number;
  orgs_unmatched: number;
  error_message: string | null;
}

export interface CustomerSummary {
  id: number;
  name: string;
  ion_customer_id: string | null;
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
  line_count: number;
  device_count: number | null;
  sentinelone_count: number | null;
  backup_total_bytes: string | null;
  backup_used_bytes: string | null;
  backup_available_bytes: string | null;
  backup_server_count: number | null;
  backup_workstation_count: number | null;
  backup_vm_count: number | null;
  backup_mailboxes_count: number | null;
}

export interface LicenseLine {
  id: number;
  sku: string;
  product_name: string;
  vendor: string;
  quantity: number;
  unit_cost: string;
  unit_price: string | null;
  unit_margin: string | null;
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
  term_start: string | null;
  term_end: string | null;
  billing_period: string | null;
  last_synced_at: string;
  po_name: string | null;
}

export interface CustomerDetail {
  id: number;
  name: string;
  ion_customer_id: string | null;
  license_lines: LicenseLine[];
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
  device_count: number | null;
  sentinelone_count: number | null;
  backup_total_bytes: string | null;
  backup_used_bytes: string | null;
  backup_available_bytes: string | null;
  backup_server_count: number | null;
  backup_workstation_count: number | null;
  backup_vm_count: number | null;
  backup_mailboxes_count: number | null;
  dr_storage_total_bytes: string | null;
  dr_storage_used_bytes: string | null;
  dr_storage_available_bytes: string | null;
  consolidate_license_lines: boolean;
}

export interface ReportSummary {
  customer_count: number;
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
}

export interface NinjaOrgStat {
  org_name: string;
  device_count: number;
  sentinelone_count: number;
  synced_at: string;
}

export interface AcronisSyncLog {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed";
  tenants_matched: number;
  tenants_unmatched: number;
  error_message: string | null;
}

export interface AcronisOrgStat {
  tenant_id: string;
  tenant_name: string;
  backup_total_bytes: string | null;
  backup_used_bytes: string;
  backup_server_count: number;
  backup_workstation_count: number;
  backup_vm_count: number;
  backup_mailboxes_count: number;
  synced_at: string;
}
