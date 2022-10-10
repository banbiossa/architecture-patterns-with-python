import json
import logging

import redis

from domain_modelling import config
from domain_modelling.domain import events

logger = logging.getLogger(__name__)
r = redis.Redis(**config.get_redis_host_and_port())


def publish(channel, event: events.Event):
    logger.debug("publishing %s to %s", event, channel)
    r.publish(channel, json.dumps(asdict(event)))