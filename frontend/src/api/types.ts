export interface SyncLog {
  id: number;
  started_at: string;
  finished_at: string | null;
  status: "running" | "success" | "failed";
  customers_synced: number;
  lines_synced: number;
  error_message: string | null;
}

export interface CustomerSummary {
  id: number;
  name: string;
  ion_customer_id: string;
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
  line_count: number;
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
}

export interface CustomerDetail {
  id: number;
  name: string;
  ion_customer_id: string;
  license_lines: LicenseLine[];
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
}

export interface ReportSummary {
  customer_count: number;
  total_cost: string;
  total_price: string | null;
  total_margin: string | null;
  margin_pct: string | null;
}
