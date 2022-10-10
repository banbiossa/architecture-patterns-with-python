from dataclasses import dataclass
from datetime import date
from typing import List, Optional, Union


class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date]


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
