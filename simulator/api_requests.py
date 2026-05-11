from simulator.config import *
from simulator.utility import *
import asyncio
import aiohttp
import json

async def process_image(session):
    global total_requests, successful_requests, failed_requests

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

            total_requests += 1

            async with session.post(
                BASE_URL + PROCESS_ENDPOINT,
                data=data
            ) as response:

                if response.status == 200:
                    successful_requests += 1
                    result = await response.json()

                    print(f"Created job: {result['job_id']}")

                    return result["job_id"]

                else:
                    failed_requests += 1
                    print(f"Process failed: {response.status}")
                    return None

    except Exception as e:
        print(f"Processing error: {e}")
        failed_requests += 1
        return None


async def get_result(session, job_id):
    global total_requests, successful_requests, failed_requests

    while True:
        try:
            total_requests += 1

            async with session.get(
                f"{BASE_URL}{RESULT_ENDPOINT}/{job_id}"
            ) as response:

                if response.status == 200:
                    successful_requests += 1
                    result = await response.json()

                    if result.get("status") == "completed":
                        print(f"Job {job_id} completed")
                        return True

                    elif result.get("status") == "failed":
                        print(f"Job {job_id} failed")
                        return False

                elif response.status == 404:
                    print(f"Job {job_id} not ready yet...")

                else:
                    failed_requests += 1

        except Exception as e:
            print(f"Result polling error: {e}")
            failed_requests += 1

        await asyncio.sleep(POLL_INTERVAL)