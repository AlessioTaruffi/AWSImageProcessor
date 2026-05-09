import argparse
import asyncio

from simulator.metrics import print_metrics
from simulator.workload_execution import run_workload


async def main(mode):
    print(f"Starting simulator in {mode} mode...")
    await run_workload(mode)
    print_metrics()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["stress", "markov"],
        required=True
    )

    args = parser.parse_args()

    asyncio.run(
        main(args.mode)
    )