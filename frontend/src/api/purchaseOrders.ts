import { apiFetch } from "./client";

export function updatePurchaseOrder(licenseLineId: number, poName: string): Promise<unknown> {
  return apiFetch("/api/purchase-orders", {
    method: "PUT",
    body: JSON.stringify({ license_line_id: licenseLineId, po_name: poName }),
  });
}
