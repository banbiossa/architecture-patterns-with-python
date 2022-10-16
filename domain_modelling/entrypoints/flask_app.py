import logging
from datetime import datetime

from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain_modelling import config
from domain_modelling.adapters import orm, repository
from domain_modelling.domain import commands, events, model
from domain_modelling.service_layer import handlers, messagebus, unit_of_work
from domain_modelling.service_layer.handlers import InvalidSku

orm.start_mappers()
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("domain_modelling.flask_app")
logger.setLevel(logging.DEBUG)


@app.route("/add_batch", methods=["POST"])
def add_batch():
    eta = request.json["eta"]
    if eta is not None:
        eta = datetime.fromisoformat(eta).date()
    cmd = commands.CreateBatch(
        request.json["ref"], request.json["sku"], request.json["qty"], eta
    )
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    messagebus.handle(cmd, uow)
    return "OK", 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    try:
        cmd = commands.Allocate(
            request.json["orderid"], request.json["sku"], request.json["qty"]
        )
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        results = messagebus.handle(cmd, uow)
        batchref = results.pop(0)
    except InvalidSku as e:
        return {"message": str(e)}, 400
    return {"batchref": batchref}, 201
