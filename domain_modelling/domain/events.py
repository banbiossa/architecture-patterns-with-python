from dataclasses import dataclass
from datetime import date
from typing import Optional


class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[date]


@dataclass
class AllocationRequired(Event):
    orderid: str
    sku: str
    qty: int


@dataclass
class BatchQuantityChanged(Event):
    ref: str
    qty: int


@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str
