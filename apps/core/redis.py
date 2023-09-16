from os import getenv

from redis import StrictRedis


def get_redis_client() -> "StrictRedis":
    return StrictRedis(
        host="localhost",
        port=int(getenv("REDIS_PORT", "6379")),
        decode_responses=True,
    )
