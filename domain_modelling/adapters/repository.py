import abc

from domain_modelling.domain import model


class AbstractProductRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, sku) -> model.Product:
        raise NotImplementedError


class SqlAlchemyRepository(AbstractProductRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product):
        self.session.add(product)

    def get(self, sku):
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
        self._batches = set(batches)

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)
