from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.models import Customer, LicenseLine, SellPrice


@dataclass
class LineMargin:
    line: LicenseLine
    unit_price: Optional[Decimal]
    unit_margin: Optional[Decimal]
    total_cost: Decimal
    total_price: Optional[Decimal]
    total_margin: Optional[Decimal]
    margin_pct: Optional[Decimal]


@dataclass
class Totals:
    total_cost: Decimal
    total_price: Optional[Decimal]
    total_margin: Optional[Decimal]
    margin_pct: Optional[Decimal]
    line_count: int = 0


def line_margin(line: LicenseLine, price: Optional[SellPrice]) -> LineMargin:
    unit_cost = Decimal(line.unit_cost)
    quantity = Decimal(line.quantity)
    total_cost = unit_cost * quantity

    if price is None:
        return LineMargin(
            line=line, unit_price=None, unit_margin=None,
            total_cost=total_cost, total_price=None, total_margin=None, margin_pct=None,
        )

    unit_price = Decimal(price.unit_price)
    unit_margin = unit_price - unit_cost
    total_price = unit_price * quantity
    total_margin = total_price - total_cost
    margin_pct = (unit_margin / unit_price * 100) if unit_price != 0 else None

    return LineMargin(
        line=line, unit_price=unit_price, unit_margin=unit_margin,
        total_cost=total_cost, total_price=total_price, total_margin=total_margin, margin_pct=margin_pct,
    )


def aggregate_totals(line_margins: list[LineMargin]) -> Totals:
    total_cost = sum((lm.total_cost for lm in line_margins), Decimal("0"))
    priced = [lm for lm in line_margins if lm.total_price is not None]

    if not priced:
        return Totals(total_cost=total_cost, total_price=None, total_margin=None, margin_pct=None, line_count=len(line_margins))

    total_price = sum((lm.total_price for lm in priced), Decimal("0"))
    total_margin = sum((lm.total_margin for lm in priced), Decimal("0"))
    margin_pct = (total_margin / total_price * 100) if total_price != 0 else None

    return Totals(
        total_cost=total_cost, total_price=total_price, total_margin=total_margin,
        margin_pct=margin_pct, line_count=len(line_margins),
    )


def sell_price_lookup(prices: list[SellPrice]) -> dict[tuple[int, str], SellPrice]:
    return {(p.customer_id, p.sku): p for p in prices}


def is_customer_empty(customer: Customer, line_count: int) -> bool:
    """No license lines, no NinjaOne devices, no Acronis backup data - nothing worth showing."""
    return (
        line_count == 0
        and not customer.device_count
        and not customer.backup_used_bytes
        and not customer.backup_machines_count
        and not customer.backup_mailboxes_count
    )
