"""
Lambda handler — Image Processor.

Triggerata da SQS FIFO (ImageProcessingQueue.fifo).
Per ogni messaggio:
    1. Scarica l'immagine da S3 (image_key)
    2. Applica la pipeline di operazioni
    3. Salva il risultato su S3 (output: outputs/{job_id}.jpg)

Il bucket è UNICO ed è letto dalla variabile d'ambiente S3_BUCKET.

Variabili d'ambiente:
    S3_BUCKET         nome del bucket (es. "cipa-storage-850029407617")
    OUTPUT_PREFIX     prefix S3 per gli output (default "outputs/")

Schema messaggio SQS:
    {
      "job_id":      "abc-123",
      "image_key":   "inputs/abc-123.jpg",
      "timestamp":   "2026-05-08T14:23:45Z",
      "operations":  [ {"op": "resize", "width": 1024}, ... ]
    }

Permessi richiesti (sul ruolo Lambda):
    s3:GetObject, s3:PutObject sul bucket
    sqs:ReceiveMessage, DeleteMessage, GetQueueAttributes (per il trigger)
"""

import json
import os
import time

import boto3
from botocore.exceptions import ClientError

from processor import (
    process_image,
    UnknownOperationError,
    InvalidParametersError,
    ImageProcessingError,
)

# ---------------------------------------------------------------------------
# Setup (riusato tra invocazioni warm)
# ---------------------------------------------------------------------------

s3 = boto3.client("s3")
S3_BUCKET = os.environ["S3_BUCKET"]
OUTPUT_PREFIX = os.environ.get("OUTPUT_PREFIX", "outputs/")


# ---------------------------------------------------------------------------
# Logica per singolo messaggio
# ---------------------------------------------------------------------------

def process_single_message(record: dict) -> None:
    body = json.loads(record["body"])
    job_id = body["job_id"]
    image_key = body["image_key"]
    operations = body["operations"]

    print(f"[{job_id}] start, input={image_key}, ops={len(operations)}")

    # 1. Scarica immagine
    t0 = time.perf_counter()
    obj = s3.get_object(Bucket=S3_BUCKET, Key=image_key)
    image_bytes = obj["Body"].read()
    download_ms = (time.perf_counter() - t0) * 1000

    # 2. Processa
    t0 = time.perf_counter()
    try:
        output_bytes = process_image(image_bytes, operations)
    except (UnknownOperationError, InvalidParametersError) as e:
        # Bad request: NON ha senso ritentare, scarta
        print(f"[{job_id}] BAD REQUEST (skipped, no retry): {e}")
        return
    process_ms = (time.perf_counter() - t0) * 1000

    # 3. Carica risultato
    t0 = time.perf_counter()
    output_key = OUTPUT_PREFIX + job_id + ".jpg"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=output_key,
        Body=output_bytes,
        ContentType="image/jpeg",
    )
    upload_ms = (time.perf_counter() - t0) * 1000

    # Metriche per CloudWatch (parsabili dai log)
    print(
        f"[{job_id}] done. "
        f"download_ms={download_ms:.0f} "
        f"process_ms={process_ms:.0f} "
        f"upload_ms={upload_ms:.0f} "
        f"input_size={len(image_bytes)} "
        f"output_size={len(output_bytes)} "
        f"output_key={output_key}"
    )


# ---------------------------------------------------------------------------
# Handler principale
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    """Entry point. Riceve un batch di messaggi SQS."""
    batch_failures = []

    for record in event.get("Records", []):
        message_id = record["messageId"]
        try:
            process_single_message(record)
        except (ImageProcessingError, ClientError) as e:
            print(f"[{message_id}] retry: {type(e).__name__}: {e}")
            batch_failures.append({"itemIdentifier": message_id})
        except Exception as e:
            print(f"[{message_id}] UNEXPECTED {type(e).__name__}: {e}")
            batch_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_failures}
