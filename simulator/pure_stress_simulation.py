from api_requests import get_result
from config import *
from markov_user_simulation import process_image

async def stress_request(session):
    job_id = await process_image(session)

    if job_id:
        await get_result(session, job_id)