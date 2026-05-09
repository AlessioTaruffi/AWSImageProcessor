from simulator.markov_states import UserState
from simulator.api_requests import upload_image, process_image, poll_status
from simulator.config import *
from simulator.utility import choose_next_state
import asyncio

async def simulated_user(session, user_id):
    state = UserState.START
    job_id = None

    while state != UserState.EXIT:

        if state == UserState.START:
            state = choose_next_state(state)

        elif state == UserState.UPLOAD:
            job_id = await upload_image(session)

            if job_id:
                state = choose_next_state(state)
            else:
                state = UserState.EXIT

        elif state == UserState.RESIZE:
            await process_image(session, RESIZE_ENDPOINT, job_id)
            await poll_status(session, job_id)
            state = UserState.EXIT

        elif state == UserState.GRAYSCALE:
            await process_image(session, GRAYSCALE_ENDPOINT, job_id)
            await poll_status(session, job_id)
            state = UserState.EXIT

        elif state == UserState.ROTATE:
            await process_image(session, ROTATE_ENDPOINT, job_id)
            await poll_status(session, job_id)
            state = UserState.EXIT

        elif state == UserState.BLUR:
            await process_image(session, BLUR_ENDPOINT, job_id)
            await poll_status(session, job_id)
            state = UserState.EXIT

        # simula tempo umano
        await asyncio.sleep(1)