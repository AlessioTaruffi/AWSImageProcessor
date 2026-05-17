import asyncio
import time
import aiohttp

from config import WORKLOAD_PATTERN
from markov_user_simulation import simulated_user
from pure_stress_simulation import stress_request 

async def run_workload(mode):
    timeout = aiohttp.ClientTimeout(total=300)

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:

        for duration, users in WORKLOAD_PATTERN:
            print(
                f"\nRunning {users} users "
                f"for {duration} seconds"
            )

            start_time = time.time()

            while time.time() - start_time < duration:
                tasks = []

                for i in range(users):

                    if mode == "markov":
                        tasks.append(
                            simulated_user(session, i)
                        )

                    elif mode == "stress":
                        tasks.append(
                            stress_request(session)
                        )

                await asyncio.gather(*tasks)
                await asyncio.sleep(0.1)