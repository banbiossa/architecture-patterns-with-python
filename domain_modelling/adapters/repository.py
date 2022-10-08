import abc

from domain_modelling.domain import model


class AbstractProductRepository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku: str) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractProductRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        # return self.session.query(model.Batch).filter_by(reference=reference).one()
        # return self.session.query(model.Product).filter_by(sku=sku).first()
        return (
            self.session.query(model.Product).filter_by(sku=sku)
            # .with_for_update()
            .first()
        )

    def list(self):
        return self.session.query(model.Product).all()


class FakeRepository(AbstractProductRepository):
    def __init__(self, batches):
        super().__init__()
        self._batches = set(batches)

    def _add(self, batch):
        self._batches.add(batch)

    def _get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
