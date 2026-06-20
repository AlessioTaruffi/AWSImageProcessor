import config

'''
Questo modulo contiene la funzione per stampare le metriche raccolte durante l'esecuzione del simulatore.
'''

def print_metrics():
    print("\n========= RESULTS =========")
    print(f"Total requests: {config.total_requests}")
    print(f"Successful requests: {config.successful_requests}")
    print(f"Failed requests: {config.failed_requests}")

    if config.total_requests > 0:
        success_rate = (
            config.successful_requests / config.total_requests
        ) * 100

        print(f"Success rate: {success_rate:.2f}%")