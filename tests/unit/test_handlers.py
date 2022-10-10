from datetime import date, timedelta

import pytest

from domain_modelling.adapters import repository
from domain_modelling.domain import events, model
from domain_modelling.domain.model import Batch, OrderLine
from domain_modelling.service_layer import handlers, messagebus, unit_of_work

today = date.today()
tomorrow = date.today() + timedelta(days=1)
later = date.today() + timedelta(days=20)


class FakeSession:
    committed = False

    def commit(self):
        self.committed = True


class FakeRepository(repository.AbstractProductRepository):
    def __init__(self, products):
        super(FakeRepository, self).__init__()
        self._products = set(products)

    def _add(self, batch):
        self._products.add(batch)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref: str) -> model.Product:
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


class FakeUnitOfWorkWithFakeMessageBus(FakeUnitOfWork):
    def __init__(self):
        super().__init__()
        self.events_published = []

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                self.events_published.append(product.events.pop(0))


# domain layer test
def test_prefers_current_stock_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO_CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO_CLOCK", 100, eta=tomorrow)

    line = OrderLine("order-123", "RETRO_CLOCK", 10)
    model.allocate(line, [in_stock_batch, shipment_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


# handlers-layer test
def test_prefers_warehouse_batches_to_shipments():
    in_stock_batch = Batch("in-stock-batch", "RETRO_CLOCK", 100, eta=None)
    shipment_batch = Batch("shipment-batch", "RETRO_CLOCK", 100, eta=tomorrow)
    repo = FakeRepository([in_stock_batch, shipment_batch])
    session = FakeSession()

    line = OrderLine("order-123", "RETRO_CLOCK", 10)
    handlers.allocate(line, repo, session)

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    handlers.add_batch("b1", "RETRO_CLOCK", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.committed


def test_returns_allocation():
    repo = FakeRepository.for_batch("b1", "COMPLICATED_LAMP", 20, None)

    result = handlers.allocate("o1", "COMPLICATED_LAMP", 10, repo, FakeSession())
    assert result == "b1"


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    handlers.add_batch("b1", "RETRO_CLOCK", 100, None, repo, session)
    result = handlers.allocate("o1", "RETRO_CLOCK", 10, repo, session)
    assert result == "b1"


def test_allocate_errors_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    handlers.add_batch("b1", "AREALSKU", 100, None, repo, session)

    with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        handlers.allocate("o1", "NONEXISTENTSKU", 10, repo, session)


def test_error_for_invalid_sku():
    line = model.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = model.Batch("b1", "AREALSKU", 20, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(handlers.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        handlers.allocate(line, repo, FakeSession())


def test_commits():
    line = model.OrderLine("o1", "OMNIOUS_MIRROR", 10)
    batch = model.Batch("b1", "OMNIOUS_MIRROR", 20, eta=None)

    repo = FakeRepository([batch])
    session = FakeSession()

    handlers.allocate(line, repo, session)
    assert session.committed is True


class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


def test_add_batch():
    uow = FakeUnitOfWork()
    handlers.add_batch("b1", "RETRO_CLOCK", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow = FakeUnitOfWork()
    handlers.add_batch("b1", "RETRO_CLOCK", 100, None, uow)
    result = handlers.allocate("o1", "RETRO_CLOCK", 10, uow)
    assert result == "b1"


class TestAddBatch:
    def test_for_new_product(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("b1", "RETRO-CLOCK", 100, None), uow)
        assert uow.products.get(sku="RETRO-CLOCK") is not None
        assert uow.committed is True


class TestAllocate:
    def test_returns_allocation(self):
        uow = FakeUnitOfWork()
        messagebus.handle(
            events.BatchCreated("batch1", "COMPLICATED-LAMP", 100, None), uow
        )
        results = messagebus.handle(
            events.AllocationRequired("o1", "COMPLICATED-LAMP", 10), uow
        )
        assert results.pop(0) == "batch1"


class TestChangeBatchQuantity:
    def test_changes_avaiable_quantity(self):
        uow = FakeUnitOfWork()
        messagebus.handle(events.BatchCreated("batch1", "ELEGANT-LAMP", 100, None), uow)
        [batch] = uow.products.get(sku="ELEGANT-LAMP").batches

        messagebus.handle(events.BatchQuantityChanged("batch1", 50), uow)

        assert uow.products.get(sku="ELEGANT-LAMP").batches[0].available_quantity == 50

    def test_reallocates_if_necessary(self):
        uow = FakeUnitOfWork()
        events_history = [
            events.BatchCreated("batch1", "ELEGANT-LAMP", 50, None),
            events.BatchCreated("batch2", "ELEGANT-LAMP", 50, date.today()),
            events.AllocationRequired("o1", "ELEGANT-LAMP", 20),
            events.AllocationRequired("o2", "ELEGANT-LAMP", 20),
        ]
        for e in events_history:
            messagebus.handle(e, uow)
        [batch1, batch2] = uow.products.get(sku="ELEGANT-LAMP").batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

        assert batch1.available_quantity == 5
        assert batch2.available_quantity == 30


def test_reallocates_if_necessary_isolated():
    uow = FakeUnitOfWorkWithFakeMessageBus()

    events_history = [
        events.BatchCreated("batch1", "ELEGANT-LAMP", 50, None),
        events.BatchCreated("batch2", "ELEGANT-LAMP", 50, date.today()),
        events.AllocationRequired("o1", "ELEGANT-LAMP", 20),
        events.AllocationRequired("o2", "ELEGANT-LAMP", 20),
    ]

    for e in events_history:
        messagebus.handle(e, uow)
    [batch1, batch2] = uow.products.get(sku="ELEGANT-LAMP").batches
    assert batch1.available_quantity == 10
    assert batch2.available_quantity == 50

    messagebus.handle(events.BatchQuantityChanged("batch1", 25), uow)

    [reallocation_event] = uow.events_published
    assert isinstance(reallocation_event, events.AllocationRequired)
    assert reallocation_event.orderid in {"order1", "order2"}
    assert reallocation_event.sku == "ELEGANT-LAMP"
