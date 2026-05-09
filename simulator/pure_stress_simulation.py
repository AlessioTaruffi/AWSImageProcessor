from simulator.api_requests import upload_image
from simulator.config import *
from simulator.markov_user_simulation import process_image
import random

async def stress_request(session):
    job_id = await upload_image(session)

    if not job_id:
        return

    operation = random.choice([
        RESIZE_ENDPOINT,
        GRAYSCALE_ENDPOINT,
        ROTATE_ENDPOINT,
        BLUR_ENDPOINT
    ])

    await process_image(session, operation, job_id)