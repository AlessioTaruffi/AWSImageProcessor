from api_requests import get_result
from config import *
from markov_user_simulation import process_image

'''
Questo modulo implementa la simulazione dello stress test, in cui un numero elevato di richieste viene inviato al servizio in un breve periodo di tempo.
'''

async def stress_request(session):
    job_id = await process_image(session)

    if job_id:
        await get_result(session, job_id)