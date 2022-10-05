from datetime import date

from domain_modelling.domain import events
from domain_modelling.domain.model import Batch, OrderLine, Product

today = date(year=2020, month=1, day=1)
tomorrow = date(year=2020, month=1, day=2)


def test_records_out_of_stock_event_if_can_not_allocate():
    batch = Batch("batch1", "COMPLICATED-LAMP", 10, eta=today)
    product = Product(sku="COMPLICATED-LAMP", batches=[batch])
    product.allocate(OrderLine("order1", "COMPLICATED-LAMP", 10))

    allocation = product.allocate(OrderLine("order2", "COMPLICATED-LAMP", 1))
    assert product.events[-1] == events.OutOfStock(sku="COMPLICATED-LAMP")
    assert allocation is None
