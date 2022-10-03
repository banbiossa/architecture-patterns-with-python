from datetime import date, timedelta

import pytest

from domain_modelling.adapters import repository
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


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches):
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


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


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "RETRO_CLOCK", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed


def test_returns_allocation():
    repo = FakeRepository.for_batch("b1", "COMPLICATED_LAMP", 20, None)

    result = services.allocate("o1", "COMPLICATED_LAMP", 10, repo, FakeSession())
    assert result == "b1"


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "RETRO_CLOCK", 100, None, repo, session)
    result = services.allocate("o1", "RETRO_CLOCK", 10, repo, session)
    assert result == "b1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, session)


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


from domain_modelling.service_layer import unit_of_work


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "RETRO_CLOCK", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "RETRO_CLOCK", 100, None, uow)
    result = services.allocate("o1", "RETRO_CLOCK", 10, uow)
    assert result == "b1"
