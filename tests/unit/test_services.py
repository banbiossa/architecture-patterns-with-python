from datetime import date, timedelta

import pytest

from domain_modelling.adapters.repository import FakeRepository
from domain_modelling.domain import model
from domain_modelling.domain.model import Batch, OrderLine
from domain_modelling.service_layer import services

today = date.today()
tomorrow = date.today() + timedelta(days=1)
later = date.today() + timedelta(days=20)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


# domain layer test
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO_CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO_CLOCK", 100, eta=tomorrow)

    line = OrderLine("order-123", "RETRO_CLOCK", 10)
    model.allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


# service-layer test
def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO_CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO_CLOCK", 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    line = OrderLine("order-123", "RETRO_CLOCK", 10)
    services.allocate(line, repo, session)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_returns_allocation():
    line = model.OrderLine("o1", "COMPLICATED_LAMP", 10)
    batch = model.Batch("b1", "COMPLICATED_LAMP", 20, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 20, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMNIOUS_MIRROR", 10)
    batch = model.Batch("b1", "OMNIOUS_MIRROR", 20, eta=None)

    repo = FakeRepository([batch])
    session = FakeSession()

    services.allocate(line, repo, session)
    assert session.committed is True
