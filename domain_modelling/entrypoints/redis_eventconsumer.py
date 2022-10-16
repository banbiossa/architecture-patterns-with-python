import json
import logging

import redis

from domain_modelling import config
from domain_modelling.adapters import orm
from domain_modelling.domain import commands
from domain_modelling.service_layer import messagebus, unit_of_work

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("domain_modelling.redis")
logger.setLevel(logging.DEBUG)
r = redis.Redis(**config.get_redis_host_and_port())


def main():
    orm.start_mappers()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("change_batch_quantity")

    for m in pubsub.listen():
        handle_change_batch_quantity(m)


def handle_change_batch_quantity(m):
    logger.debug("handling %s", m)

    data = json.loads(m["data"])
    cmd = commands.ChangeBatchQuantity(ref=data["batchref"], qty=data["qty"])
    messagebus.handle(cmd, uow=unit_of_work.SqlAlchemyUnitOfWork())


if __name__ == "__main__":
    main()
