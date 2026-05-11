BASE_URL = "http://54.162.232.91/"


PROCESS_ENDPOINT = "/process-image"
RESULT_ENDPOINT = "/result"
# immagini di test
SMALL_IMAGE = "images/small.jpg"      # 21 KB
MEDIUM_IMAGE = "images/medium.jpg"    # 159 KB
LARGE_IMAGE = "images/large.jpg"      # 7.8 MB

# polling ogni 5 secondi
POLL_INTERVAL = 5

# workload per test autoscaling
# WORKLOAD_PATTERN = [
#     (60, 20),    # 1 minuto -> 20 utenti
#     (120, 50),   # 2 minuti -> 50 utenti
#     (120, 100),  # 2 minuti -> picco
#     (60, 20)     # ritorno a carico basso
# ]

WORKLOAD_PATTERN = [
    (60, 1),    # 1 minuto -> 20 utenti
    (120, 2),   # 2 minuti -> 50 utenti
    (120, 5),  # 2 minuti -> picco
    (60, 2)     # ritorno a carico basso
]

# metriche globali
total_requests = 0
successful_requests = 0
failed_requests = 0