from simulator.config import *
from simulator.utility import choose_image
import asyncio
import aiohttp

async def upload_image(session):
    global total_requests, successful_requests, failed_requests

    image_path = choose_image()

    try:
        with open(image_path, "rb") as f:
            data = aiohttp.FormData()
            data.add_field(
                "file",
                f,
                filename=image_path,
                content_type="image/jpeg"
            )

            total_requests += 1

            async with session.post(
                BASE_URL + UPLOAD_ENDPOINT,
                data=data
            ) as response:

                if response.status == 200:
                    successful_requests += 1
                    result = await response.json()
                    return result["job_id"]

                failed_requests += 1
                return None

    except Exception as e:
        print(f"Upload error: {e}")
        failed_requests += 1
        return None


async def process_image(session, endpoint, job_id):
    global total_requests, successful_requests, failed_requests

    try:
        total_requests += 1

        async with session.post(
            BASE_URL + endpoint,
            json={"job_id": job_id}
        ) as response:

            if response.status == 200:
                successful_requests += 1
                return True

            failed_requests += 1
            return False

    except Exception as e:
        print(f"Processing error: {e}")
        failed_requests += 1
        return False


async def poll_status(session, job_id):
    global total_requests, successful_requests, failed_requests

    while True:
        try:
            total_requests += 1

            async with session.get(
                BASE_URL + STATUS_ENDPOINT,
                params={"job_id": job_id}
            ) as response:

                if response.status == 200:
                    successful_requests += 1
                    result = await response.json()

                    if result["status"] == "completed":
                        return True

                    elif result["status"] == "failed":
                        return False

                else:
                    failed_requests += 1

        except Exception as e:
            print(f"Polling error: {e}")
            failed_requests += 1

        await asyncio.sleep(POLL_INTERVAL)
