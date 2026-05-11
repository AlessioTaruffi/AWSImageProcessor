from simulator.api_requests import get_result
from simulator.config import *
from simulator.markov_user_simulation import process_image
import random

async def stress_request(session):
    job_id = await process_image(session)

    if job_id:
        await get_result(session, job_id)