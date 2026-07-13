from decimal import Decimal

from app.models import LicenseLine, SellPrice
from app.services.margin_service import aggregate_totals, line_margin


def _line(**overrides):
    defaults = dict(id=1, sku="SKU1", product_name="Product", vendor="Vendor", quantity=10, unit_cost=Decimal("10.00"))
    defaults.update(overrides)
    return LicenseLine(**defaults)


def test_line_margin_without_price():
    line = _line()
    result = line_margin(line, None)
    assert result.total_cost == Decimal("100.00")
    assert result.unit_price is None
    assert result.total_margin is None


def test_line_margin_with_price():
    line = _line(quantity=10, unit_cost=Decimal("10.00"))
    price = SellPrice(customer_id=1, sku="SKU1", unit_price=Decimal("15.00"))
    result = line_margin(line, price)
    assert result.unit_margin == Decimal("5.00")
    assert result.total_cost == Decimal("100.00")
    assert result.total_price == Decimal("150.00")
    assert result.total_margin == Decimal("50.00")
    assert round(result.margin_pct, 2) == Decimal("33.33")


def test_aggregate_totals_mixed_priced_and_unpriced():
    priced_line = _line(id=1, sku="A", quantity=2, unit_cost=Decimal("5.00"))
    priced = line_margin(priced_line, SellPrice(customer_id=1, sku="A", unit_price=Decimal("10.00")))

    unpriced_line = _line(id=2, sku="B", quantity=3, unit_cost=Decimal("4.00"))
    unpriced = line_margin(unpriced_line, None)

    totals = aggregate_totals([priced, unpriced])
    assert totals.total_cost == Decimal("22.00")  # 2*5 + 3*4
    assert totals.total_price == Decimal("20.00")  # only priced line counted
    assert totals.total_margin == Decimal("10.00")
    assert totals.line_count == 2
