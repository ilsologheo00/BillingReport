import { apiFetch } from "./client";
import type { CustomerDetail, CustomerSummary, ReportSummary } from "./types";

export function getCustomers(): Promise<CustomerSummary[]> {
  return apiFetch<CustomerSummary[]>("/api/customers");
}

export function getCustomer(id: number): Promise<CustomerDetail> {
  return apiFetch<CustomerDetail>(`/api/customers/${id}`);
}

export function getReportSummary(): Promise<ReportSummary> {
  return apiFetch<ReportSummary>("/api/report/summary");
}
