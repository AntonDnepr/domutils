"""Background job queue for parsing battle report screenshots.

The web app stores the uploaded image in Redis and pushes the job id to a list;
a single worker process (``python -m apps.battleparser.worker``) pops ids and
parses one image at a time, which keeps memory use low and predictable.
"""

import base64
import json
import logging
import uuid
from typing import List, Optional

QUEUE_KEY = "battlejobs:queue"
JOB_KEY = "battlejob:{}"
JOB_TTL_SECONDS = 60 * 60
MAX_IMAGE_BYTES = 5 * 1024 * 1024

QUEUED, RUNNING, DONE, ERROR = "queued", "running", "done", "error"

logger = logging.getLogger(__name__)


def enqueue(redis, image: bytes) -> str:
    job_id = uuid.uuid4().hex
    key = JOB_KEY.format(job_id)
    # The shared client decodes responses as text, so store the image as base64.
    redis.hset(
        key,
        mapping={"status": QUEUED, "image": base64.b64encode(image).decode("ascii")},
    )
    redis.expire(key, JOB_TTL_SECONDS)
    redis.lpush(QUEUE_KEY, job_id)
    return job_id


def get_job(redis, job_id: str) -> Optional[dict]:
    job = redis.hgetall(JOB_KEY.format(job_id))
    if not job:
        return None
    response = {"job_id": job_id, "status": job.get("status")}
    if job.get("result"):
        payload = json.loads(job["result"])
        response["result"] = payload["nations"]
        response["warnings"] = payload["warnings"]
    if job.get("error"):
        response["error"] = job["error"]
    return response


def process_job(redis, job_id: str, unit_names: Optional[List[str]] = None) -> None:
    key = JOB_KEY.format(job_id)
    encoded = redis.hget(key, "image")
    if encoded is None:
        return  # expired before we got to it
    redis.hset(key, "status", RUNNING)
    try:
        # Imported here so the web app can queue jobs without loading OpenCV.
        from apps.battleparser.parser import parse_battle_image

        result = parse_battle_image(base64.b64decode(encoded), unit_names=unit_names)
    except Exception as exc:  # report any failure back to the client
        logger.exception("Battle report job %s failed", job_id)
        redis.hset(key, mapping={"status": ERROR, "error": str(exc)})
    else:
        payload = {"nations": result.nations, "warnings": result.warnings}
        redis.hset(
            key,
            mapping={"status": DONE, "result": json.dumps(payload, ensure_ascii=False)},
        )
    redis.hdel(key, "image")
    redis.expire(key, JOB_TTL_SECONDS)


def load_unit_names() -> Optional[List[str]]:
    """Dom6 unit names from Redis, used to correct small OCR mistakes."""
    try:
        from apps.dom6data.models import Dom6Unit

        return sorted({unit.name for unit in Dom6Unit.find().all()})
    except Exception:
        logger.warning("Unit names unavailable; using raw OCR names", exc_info=True)
        return None


def run_forever() -> None:
    from apps.core.redis import get_redis_client

    redis = get_redis_client()
    unit_names = load_unit_names()
    logger.info("Battle report worker started")
    while True:
        item = redis.brpop(QUEUE_KEY, timeout=30)
        if item is None:
            continue
        process_job(redis, item[1], unit_names)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
