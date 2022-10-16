import json
import logging

import redis

from domain_modelling import config

logger = logging.getLogger(__name__)
r = redis.Redis(**config.get_redis_host_and_port())


def subscribe_to(channel):
    pubsub = r.pubsub()
    pubsub.subscribe(channel)
    confirmation = pubsub.get_message(timeout=3)
    assert confirmation["type"] == "subscribe"
    logger.debug("subscribed to %s", channel)
    return pubsub


def publish_message(channel, message):
    num = r.publish(channel, json.dumps(message))
    logger.debug("published%s to %s with %d subscribers", message, channel, num)
