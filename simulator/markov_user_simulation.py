from simulator.markov_states import UserState
from simulator.api_requests import *
from simulator.config import *
from simulator.utility import choose_next_state
import asyncio

async def simulated_user(session, user_id):
    state = UserState.START

    while state != UserState.EXIT:

        if state == UserState.START:
            state = choose_next_state(state)

        elif state == UserState.PROCESS_IMAGE:
            job_id = await process_image(session)

            if job_id:
                await get_result(session, job_id)

            state = UserState.EXIT

        await asyncio.sleep(1)