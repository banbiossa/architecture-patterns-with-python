import pytest

from domain_modelling.model import Batch, OrderLine, allocate, OutOfStock
from datetime import date, timedelta

today = date.today()
tomorrow = date.today() + timedelta(days=1)
later = date.today() + timedelta(days=20)


def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO_CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO_CLOCK", 100, eta=tomorrow)

    line = OrderLine("order-123", "RETRO_CLOCK", 10)
    allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    earliest = Batch("speedy-batch", "MINIMALIST_SPOON", 100, eta=today)
    medium = Batch("normal-batch", "MINIMALIST_SPOON", 100, eta=tomorrow)
    latest = Batch("slow-batch", "MINIMALIST_SPOON", 100, eta=later)
    line = OrderLine("order-1", "MINIMALIST_SPOON", 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    in_stock_batch = Batch("in-stock-batch-ref", "HIGHBROW_POSTER", 100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", "HIGHBROW_POSTER", 100, eta=tomorrow)
    line = OrderLine("oref", "HIGHBROW_POSTER", 10)
    allocation = allocate(line, [in_stock_batch, shipment_batch])
    assert allocation == in_stock_batch.reference


def test_lt():
    none = Batch("speedy-batch", "MINIMALIST_SPOON", 100, eta=None)
    earliest = Batch("speedy-batch", "MINIMALIST_SPOON", 100, eta=today)
    same = Batch("speedy-batch", "MINIMALIST_SPOON", 100, eta=today)
    medium = Batch("normal-batch", "MINIMALIST_SPOON", 100, eta=tomorrow)

    assert earliest < medium
    assert none < earliest
    assert earliest < same


def test_raised_out_of_stock_exception_if_can_not_allocate():
    batch = Batch("batch-001", "SMALL_TABLE", qty=20, eta=today)
    allocate(OrderLine("order-1", "SMALL_TABLE", qty=20), [batch])

    with pytest.raises(OutOfStock, match="SMALL_TABLE"):
        allocate(OrderLine("order-2", "SMALL_TABLE", qty=1), [batch])
