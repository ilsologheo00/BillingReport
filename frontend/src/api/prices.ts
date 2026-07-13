import { apiFetch } from "./client";

export function updatePrice(customerId: number, sku: string, unitPrice: string): Promise<unknown> {
  return apiFetch("/api/prices", {
    method: "PUT",
    body: JSON.stringify({ customer_id: customerId, sku, unit_price: unitPrice }),
  });
}
