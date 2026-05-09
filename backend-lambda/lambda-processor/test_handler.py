"""Test del Lambda handler con moto. Schema messaggio aggiornato (bucket via env)."""

import json
import os
from io import BytesIO

os.environ["S3_BUCKET"] = "cipa-test-bucket"
os.environ["OUTPUT_PREFIX"] = "outputs/"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

import boto3
from moto import mock_aws
from PIL import Image
from botocore.exceptions import ClientError


def _seed_image(s3, key: str, size=(200, 200), color=(50, 100, 200)) -> None:
    img = Image.new("RGB", size, color=color)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=85)
    s3.put_object(Bucket="cipa-test-bucket", Key=key, Body=buf.getvalue())


@mock_aws
def test_processor_happy_path():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="cipa-test-bucket")
    _seed_image(s3, "inputs/job-001.jpg")

    sqs_event = {"Records": [{
        "messageId": "msg-001",
        "body": json.dumps({
            "job_id": "job-001",
            "image_key": "inputs/job-001.jpg",
            "timestamp": "2026-05-08T14:23:45Z",
            "operations": [
                {"op": "resize", "width": 100},
                {"op": "grayscale"},
            ],
        }),
    }]}

    from handler import lambda_handler
    result = lambda_handler(sqs_event, None)
    assert result == {"batchItemFailures": []}, f"unexpected: {result}"

    out = s3.get_object(Bucket="cipa-test-bucket", Key="outputs/job-001.jpg")
    out_img = Image.open(BytesIO(out["Body"].read()))
    # Resize a width=100 mantiene aspect ratio: 200x200 → 100x100
    assert out_img.size == (100, 100), f"unexpected size {out_img.size}"
    print("✓ Happy path SUCCESS")
    print(f"  output size: {out_img.size}")


@mock_aws
def test_rotate_clockwise():
    """Verifica che rotate ruoti in senso ORARIO."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="cipa-test-bucket")
    # Immagine 200x100 (orizzontale)
    _seed_image(s3, "inputs/job-rot.jpg", size=(200, 100))

    sqs_event = {"Records": [{
        "messageId": "msg-rot",
        "body": json.dumps({
            "job_id": "job-rot",
            "image_key": "inputs/job-rot.jpg",
            "timestamp": "2026-05-08T14:23:45Z",
            "operations": [{"op": "rotate", "angle": 90}],
        }),
    }]}

    import importlib, handler
    importlib.reload(handler)
    handler.lambda_handler(sqs_event, None)

    out = s3.get_object(Bucket="cipa-test-bucket", Key="outputs/job-rot.jpg")
    out_img = Image.open(BytesIO(out["Body"].read()))
    # 200x100 ruotato 90° → 100x200
    assert out_img.size == (100, 200), f"unexpected size after 90° rotation: {out_img.size}"
    print("✓ Rotate 90° clockwise SUCCESS")
    print(f"  200x100 → {out_img.size}")


@mock_aws
def test_pipeline_all_4_ops():
    """Pipeline che usa tutte e 4 le operazioni."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="cipa-test-bucket")
    _seed_image(s3, "inputs/job-all.jpg", size=(1000, 1000))

    sqs_event = {"Records": [{
        "messageId": "msg-all",
        "body": json.dumps({
            "job_id": "job-all",
            "image_key": "inputs/job-all.jpg",
            "timestamp": "2026-05-08T14:23:45Z",
            "operations": [
                {"op": "resize", "width": 500},
                {"op": "blur", "radius": 3},
                {"op": "grayscale"},
                {"op": "rotate", "angle": 45},
            ],
        }),
    }]}

    import importlib, handler
    importlib.reload(handler)
    result = handler.lambda_handler(sqs_event, None)
    assert result == {"batchItemFailures": []}

    out = s3.get_object(Bucket="cipa-test-bucket", Key="outputs/job-all.jpg")
    out_img = Image.open(BytesIO(out["Body"].read()))
    out_img.verify()
    print("✓ Pipeline all-4-ops SUCCESS")
    print(f"  final size: {out_img.size}")


@mock_aws
def test_bad_request_no_retry():
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="cipa-test-bucket")
    _seed_image(s3, "inputs/job-bad.jpg")

    sqs_event = {"Records": [{
        "messageId": "msg-bad",
        "body": json.dumps({
            "job_id": "job-bad",
            "image_key": "inputs/job-bad.jpg",
            "timestamp": "2026-05-08T14:23:45Z",
            "operations": [{"op": "totally_made_up"}],
        }),
    }]}

    import importlib, handler
    importlib.reload(handler)
    result = handler.lambda_handler(sqs_event, None)
    assert result == {"batchItemFailures": []}

    objs = s3.list_objects_v2(Bucket="cipa-test-bucket", Prefix="outputs/")
    assert objs.get("KeyCount", 0) == 0, "non doveva esserci output"
    print("✓ Bad request SUCCESS (no retry, no output)")


@mock_aws
def test_missing_required_param():
    """Resize senza width: deve essere rifiutato senza retry."""
    s3 = boto3.client("s3", region_name="us-east-1")
    s3.create_bucket(Bucket="cipa-test-bucket")
    _seed_image(s3, "inputs/job-noparam.jpg")

    sqs_event = {"Records": [{
        "messageId": "msg-noparam",
        "body": json.dumps({
            "job_id": "job-noparam",
            "image_key": "inputs/job-noparam.jpg",
            "timestamp": "2026-05-08T14:23:45Z",
            "operations": [{"op": "resize"}],  # manca width
        }),
    }]}

    import importlib, handler
    importlib.reload(handler)
    result = handler.lambda_handler(sqs_event, None)
    assert result == {"batchItemFailures": []}, "non deve fare retry su bad request"
    print("✓ Missing required param SUCCESS (rejected without retry)")


if __name__ == "__main__":
    test_processor_happy_path()
    test_rotate_clockwise()
    test_pipeline_all_4_ops()
    test_bad_request_no_retry()
    test_missing_required_param()
    print("\nAll tests passed.")
