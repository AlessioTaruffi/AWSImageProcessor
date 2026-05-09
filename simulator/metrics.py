from simulator.config import *

def print_metrics():
    print("\n========= RESULTS =========")
    print(f"Total requests: {total_requests}")
    print(f"Successful requests: {successful_requests}")
    print(f"Failed requests: {failed_requests}")

    if total_requests > 0:
        success_rate = (
            successful_requests / total_requests
        ) * 100

        print(f"Success rate: {success_rate:.2f}%")