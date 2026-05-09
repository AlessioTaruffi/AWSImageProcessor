BASE_URL = "http://YOUR_LOAD_BALANCER_DNS"

UPLOAD_ENDPOINT = "/upload"
RESIZE_ENDPOINT = "/resize"
GRAYSCALE_ENDPOINT = "/grayscale"
ROTATE_ENDPOINT = "/rotate"
BLUR_ENDPOINT = "/blur"
STATUS_ENDPOINT = "/job-status"

# immagini di test
SMALL_IMAGE = "images/small.jpg"      # 21 KB
MEDIUM_IMAGE = "images/medium.jpg"    # 159 KB
LARGE_IMAGE = "images/large.jpg"      # 7.8 MB

# polling ogni 5 secondi
POLL_INTERVAL = 5

# workload per test autoscaling
WORKLOAD_PATTERN = [
    (60, 20),    # 1 minuto -> 20 utenti
    (120, 50),   # 2 minuti -> 50 utenti
    (120, 100),  # 2 minuti -> picco
    (60, 20)     # ritorno a carico basso
]

# metriche globali
total_requests = 0
successful_requests = 0
failed_requests = 0