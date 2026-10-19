import json
import os

from apps.battleparser import worker
from apps.core.redis import get_redis_client
from apps.mapgenerator.app import app

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def _run_queued_job(redis):
    job_id = redis.rpop(worker.QUEUE_KEY)
    assert job_id
    worker.process_job(redis, job_id)
    return job_id


def test_parse_endpoint_round_trip():
    redis = get_redis_client()
    redis.delete(worker.QUEUE_KEY)
    with open(os.path.join(FIXTURES, "arcoscephale.webp"), "rb") as f:
        image = f.read()

    _, response = app.test_client.post(
        "/dom6/battle-report/parse/", files={"image": ("report.webp", image)}
    )
    assert response.status == 202
    job_id = response.json["job_id"]

    _, response = app.test_client.get(f"/dom6/battle-report/parse/{job_id}/")
    assert response.json["status"] == worker.QUEUED

    assert _run_queued_job(redis) == job_id

    _, response = app.test_client.get(f"/dom6/battle-report/parse/{job_id}/")
    assert response.status == 200
    assert response.json["status"] == worker.DONE
    assert response.json["warnings"] == []
    with open(os.path.join(FIXTURES, "arcoscephale.json"), encoding="utf-8") as f:
        assert response.json["result"] == json.load(f)
    # The image is dropped once the job is finished.
    assert redis.hget(worker.JOB_KEY.format(job_id), "image") is None


def test_parse_endpoint_reports_bad_image():
    redis = get_redis_client()
    redis.delete(worker.QUEUE_KEY)
    _, response = app.test_client.post(
        "/dom6/battle-report/parse/", files={"image": ("x.png", b"not an image")}
    )
    job_id = response.json["job_id"]
    _run_queued_job(redis)
    _, response = app.test_client.get(f"/dom6/battle-report/parse/{job_id}/")
    assert response.json["status"] == worker.ERROR
    assert "decode" in response.json["error"]


def test_parse_endpoint_without_image():
    _, response = app.test_client.post("/dom6/battle-report/parse/")
    assert response.status == 400


def test_unknown_job():
    _, response = app.test_client.get("/dom6/battle-report/parse/nope/")
    assert response.status == 404


def test_upload_page():
    _, response = app.test_client.get("/dom6/battle-report/")
    assert response.status == 200
    assert 'id="fileInput"' in response.text
    assert 'id="cropModal"' in response.text
    assert "/static/vendor/cropperjs-1.6.2/cropper.min.js" in response.text
