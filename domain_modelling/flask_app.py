from flask import Flask

from domain_modelling.model import Batch, OrderLine
from domain_modelling.repository import SqlAlchemyRepository

app = Flask(__name__)


@flask.route.gubbins
def allocate_endpoint():
    batches = SqlAlchemyRepository.list()
    lines = [OrderLine(l["orderid"], l["sku"], l["qty"]) for l in request.params]
    allocate(lines, batches)
    session.commit()
    return 201
