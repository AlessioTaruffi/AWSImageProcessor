from config import BASE_URL, PROCESS_ENDPOINT, RESULT_ENDPOINT, POLL_INTERVAL
import config
from utility import *
import asyncio
import aiohttp
import json

'''
Questo modulo contiene le funzioni per interagire con l'API del servizio di elaborazione immagini.
Le funzioni principali sono:
- process_image: invia un'immagine al servizio per l'elaborazione e restituisce l'ID del job creato.
- get_result: esegue il polling per verificare lo stato del job e restituisce il risultato finale quando disponibile.
Le funzioni gestiscono anche il conteggio delle richieste totali, riuscite e fallite, aggiornando le metriche globali definite in config.py.
'''

async def process_image(session):
    image_path = choose_image()
    operation = choose_operation()

    try:
        with open(image_path, "rb") as f:
            data = aiohttp.FormData()

            data.add_field(
                "image",
                f,
                filename=image_path,
                content_type="image/jpeg"
            )

            data.add_field(
                "operation",
                json.dumps(operation)
            )

            config.total_requests += 1

            async with session.post(
                BASE_URL + PROCESS_ENDPOINT,
                data=data
            ) as response:

                if response.status == 202:
                    config.successful_requests += 1
                    result = await response.json()

                    print(f"Created job - {operation} - {result['job_id']}")

                    return result["job_id"]

                else:
                    config.successful_requests += 1
                    print(f"Process failed: {response.status} - {operation} - {await response.json()}")
                    return None

    except Exception as e:
        print(f"Processing error: {e}")
        config.failed_requests += 1
        return None


async def get_result(session, job_id):
    while True:
        try:
            config.total_requests += 1

            async with session.get(
                f"{BASE_URL}{RESULT_ENDPOINT}/{job_id}"
            ) as response:

                if response.status == 200:
                    config.successful_requests += 1
                    result = await response.json()

                    if result.get("status") == "completed":
                        print(f"Job completed {job_id}")
                        return True

                    elif result.get("status") == "failed":
                        print(f"Job failed {job_id}")
                        return False

                elif response.status == 404:
                    config.failed_requests += 1
                    print(f"Job not ready yet...  {job_id}")

                else:
                    config.successful_requests += 1
                    print(f"Polling failed: {response.status} - {job_id} - {await response.json()}")

        except Exception as e:
            print(f"Result polling error: {e}")
            config.failed_requests += 1

        await asyncio.sleep(POLL_INTERVAL)