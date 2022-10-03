from __future__ import annotations

from datetime import date
from typing import Optional

from domain_modelling.adapters.repository import AbstractRepository
from domain_modelling.domain import model
from domain_modelling.domain.model import Batch, OrderLine
from domain_modelling.service_layer import unit_of_work


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


# def allocate(
#     orderid: str, sku: str, qty: int, repo: AbstractRepository, session
# ) -> str:
#     batches = repo.list()
#     if not is_valid_sku(sku, batches):
#         raise InvalidSku(f"Invalid sku {sku}")
#     line = OrderLine(orderid, sku, qty)
#     batchref = model.allocate(line, batches)
#     session.commit()
#     return batchref
#


# def allocate(orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork):
#     line = OrderLine(orderid, sku, qty)
#     with uow:
#         batches = uow.batches.list()
#         if not is_valid_sku(sku, batches):
#             raise InvalidSku(f"Invalid sku {sku}")
#         batchref = model.allocate(line, batches)
#         uow.commit()
#     return batchref


# def add_batch(
#     ref: str, sku: str, qty: int, eta: Optional[date], repo: AbstractRepository, session
# ):
#     repo.add(Batch(ref, sku, qty, eta))
#     session.commit()


def add_batch(
    ref: str,
    sku: str,
    qty: int,
    eta: Optional[date],
    uow: unit_of_work.AbstractUnitOfWork,
):
    with uow:
        product = uow.products.get(sku=sku)
        if product is None:
            product = model.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(Batch(ref, sku, qty, eta))
        uow.commit()


def allocate(
    orderid: str, sku: str, qty: int, uow: unit_of_work.AbstractUnitOfWork
) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku=line.sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref
