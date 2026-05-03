"""
Benchmark locale del modulo processor.

Misura il tempo di esecuzione di ogni operazione (e di alcune pipeline tipiche)
sulle 3 immagini di test (small/medium/large), facendo media e deviazione
standard su N ripetizioni.

Per lanciarlo (dalla root del repo, con venv attivo):
    python processor/benchmark_local.py

Output: tabella tempi sullo stdout + file CSV in results/local_benchmark.csv.
I numeri qui sono solo di riferimento (girano sul vostro laptop, non su EC2)
ma servono per:
  1. Avere idea di quanto un'operazione sia "pesante" rispetto alle altre
  2. Calibrare le pipeline da usare nei test cloud (non vogliamo che siano
     troppo veloci, sennò il backend non è mai stressato)
"""

import csv
import statistics
import time
from pathlib import Path

from processor import process_image


# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

REPETITIONS = 5  # numero di run per ogni (operazione, immagine)
TEST_IMAGES_DIR = Path(__file__).parent / "test_images"
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
RESULTS_FILE = RESULTS_DIR / "local_benchmark.csv"

# Operazioni e pipeline da misurare. Estendere a piacere.
BENCHMARK_CASES = [
    ("resize_1024", [{"op": "resize", "width": 1024}]),
    ("grayscale", [{"op": "grayscale"}]),
    ("blur_radius5", [{"op": "blur", "radius": 5}]),
    ("blur_radius15", [{"op": "blur", "radius": 15}]),
    ("edge_enhance", [{"op": "edge_enhance"}]),
    ("pipeline_light", [{"op": "composite", "preset": "light"}]),
    ("pipeline_heavy", [{"op": "composite", "preset": "heavy"}]),
    (
        "pipeline_realistic",
        [
            {"op": "resize", "width": 1920},
            {"op": "blur", "radius": 3},
            {"op": "edge_enhance"},
        ],
    ),
]


# ---------------------------------------------------------------------------
# Esecuzione
# ---------------------------------------------------------------------------

def measure(image_bytes: bytes, operations: list[dict]) -> float:
    """Esegue process_image() e ritorna il tempo in millisecondi."""
    start = time.perf_counter()
    process_image(image_bytes, operations)
    end = time.perf_counter()
    return (end - start) * 1000.0


def main():
    # Carica le 3 immagini
    images = {}
    for name in ["small", "medium", "large"]:
        path = TEST_IMAGES_DIR / f"{name}.jpg"
        if not path.exists():
            print(f"⚠️  {path} non trovato — saltato")
            continue
        images[name] = path.read_bytes()

    if not images:
        print("ERRORE: nessuna immagine di test trovata in test_images/")
        return

    print(f"\nBenchmark: {REPETITIONS} ripetizioni per ogni caso")
    print(f"Immagini caricate: {list(images.keys())}\n")

    rows = []  # per il CSV
    print(f"{'caso':<22} {'immagine':<10} {'media (ms)':<14} {'std (ms)':<10} {'min (ms)':<10} {'max (ms)':<10}")
    print("-" * 80)

    for case_name, operations in BENCHMARK_CASES:
        for img_name, img_bytes in images.items():
            # Warmup (un giro a vuoto, non conteggiato)
            try:
                measure(img_bytes, operations)
            except Exception as e:
                print(f"{case_name:<22} {img_name:<10} ERROR: {e}")
                continue

            # Misura vera
            timings = [measure(img_bytes, operations) for _ in range(REPETITIONS)]
            mean = statistics.mean(timings)
            stdev = statistics.stdev(timings) if len(timings) > 1 else 0.0
            mn, mx = min(timings), max(timings)

            print(
                f"{case_name:<22} {img_name:<10} "
                f"{mean:<14.1f} {stdev:<10.1f} {mn:<10.1f} {mx:<10.1f}"
            )

            rows.append({
                "case": case_name,
                "image": img_name,
                "image_size_bytes": len(img_bytes),
                "repetitions": REPETITIONS,
                "mean_ms": round(mean, 2),
                "stdev_ms": round(stdev, 2),
                "min_ms": round(mn, 2),
                "max_ms": round(mx, 2),
            })

    # Salva CSV
    with open(RESULTS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✓ Risultati salvati in {RESULTS_FILE}")


if __name__ == "__main__":
    main()
