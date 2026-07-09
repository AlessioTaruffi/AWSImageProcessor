"""
Unit test per il modulo processor.

Per lanciarli (dalla root del repo, con venv attivo):
    pytest processor/test_processor.py -v

I test usano le immagini reali in processor/test_images/, ma includono
anche un test che genera un'immagine sintetica al volo, così che il file
sia eseguibile anche prima che le immagini siano state aggiunte al repo.
"""

from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from processor import (
    process_image,
    UnknownOperationError,
    InvalidParametersError,
    ImageProcessingError,
)

# Fixtures

TEST_IMAGES_DIR = Path(__file__).parent / "test_images"


@pytest.fixture
def synthetic_image_bytes() -> bytes:
    """Genera una piccola immagine sintetica RGB per i test base.
    Non richiede file su disco, utile come fallback."""
    img = Image.new("RGB", (200, 200), color=(128, 64, 200))
    # Aggiungi un po' di "rumore" così che operazioni come blur abbiano effetto
    pixels = img.load()
    for x in range(0, 200, 10):
        for y in range(200):
            pixels[x, y] = (255, 255, 255)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@pytest.fixture
def small_image_bytes() -> bytes:
    """Carica small.jpg se presente, altrimenti salta il test."""
    path = TEST_IMAGES_DIR / "small.jpg"
    if not path.exists():
        pytest.skip(f"{path} non trovato — aggiungere immagine reale per testare")
    return path.read_bytes()

# Test di base

def test_empty_pipeline_returns_valid_image(synthetic_image_bytes):
    """Una pipeline vuota deve comunque restituire un'immagine valida (re-encoded)."""
    result = process_image(synthetic_image_bytes, [])
    img = Image.open(BytesIO(result))
    img.verify()
    assert img.format == "JPEG"


def test_resize_operation(synthetic_image_bytes):
    """Resize deve produrre un'immagine con le dimensioni richieste."""
    result = process_image(
        synthetic_image_bytes,
        [{"op": "resize", "width": 100, "height": 100}],
    )
    img = Image.open(BytesIO(result))
    assert img.size == (100, 100)


def test_resize_preserves_aspect_ratio_with_one_dimension(synthetic_image_bytes):
    """Se passo solo width, height va calcolato mantenendo l'aspect ratio."""
    # Immagine sintetica è 200x200, quindi aspect ratio 1:1
    result = process_image(
        synthetic_image_bytes,
        [{"op": "resize", "width": 100}],
    )
    img = Image.open(BytesIO(result))
    assert img.size == (100, 100)


def test_grayscale_operation(synthetic_image_bytes):
    """Grayscale deve produrre un'immagine in cui R = G = B per ogni pixel."""
    result = process_image(synthetic_image_bytes, [{"op": "grayscale"}])
    img = Image.open(BytesIO(result))
    # Campioniamo qualche pixel
    for x in [10, 50, 100, 150]:
        r, g, b = img.getpixel((x, 100))
        # Tolleriamo piccoli errori di compressione JPEG
        assert abs(r - g) <= 2 and abs(g - b) <= 2


def test_blur_operation(synthetic_image_bytes):
    """Blur deve produrre un'immagine valida (test funzionale, non visivo)."""
    result = process_image(synthetic_image_bytes, [{"op": "blur", "radius": 3}])
    img = Image.open(BytesIO(result))
    img.verify()
    assert img.size == (200, 200)


def test_edge_enhance_operation(synthetic_image_bytes):
    """Edge enhance deve completare senza errori."""
    result = process_image(synthetic_image_bytes, [{"op": "edge_enhance"}])
    img = Image.open(BytesIO(result))
    img.verify()


# Test di pipeline composte

def test_pipeline_multiple_operations(synthetic_image_bytes):
    """Una pipeline con più operazioni in cascata deve funzionare end-to-end."""
    pipeline = [
        {"op": "resize", "width": 150, "height": 150},
        {"op": "blur", "radius": 2},
        {"op": "grayscale"},
    ]
    result = process_image(synthetic_image_bytes, pipeline)
    img = Image.open(BytesIO(result))
    assert img.size == (150, 150)


def test_composite_preset_heavy(synthetic_image_bytes):
    """Il preset 'heavy' deve completare senza errori."""
    result = process_image(
        synthetic_image_bytes,
        [{"op": "composite", "preset": "heavy"}],
    )
    img = Image.open(BytesIO(result))
    img.verify()
    # heavy fa resize finale a width=1024, ma se l'input è 200x200,
    # l'aspect ratio porterebbe a 1024x1024
    assert img.size[0] == 1024


def test_composite_preset_light(synthetic_image_bytes):
    """Il preset 'light' deve completare senza errori."""
    result = process_image(
        synthetic_image_bytes,
        [{"op": "composite", "preset": "light"}],
    )
    img = Image.open(BytesIO(result))
    img.verify()
    assert img.size[0] == 800


def test_composite_with_custom_pipeline(synthetic_image_bytes):
    """Composite con pipeline custom annidata."""
    result = process_image(
        synthetic_image_bytes,
        [
            {
                "op": "composite",
                "pipeline": [
                    {"op": "resize", "width": 50, "height": 50},
                    {"op": "blur", "radius": 1},
                ],
            }
        ],
    )
    img = Image.open(BytesIO(result))
    assert img.size == (50, 50)


# Test di error handling

def test_unknown_operation_raises(synthetic_image_bytes):
    with pytest.raises(UnknownOperationError):
        process_image(synthetic_image_bytes, [{"op": "nonsense_op"}])


def test_missing_op_key_raises(synthetic_image_bytes):
    with pytest.raises(InvalidParametersError):
        process_image(synthetic_image_bytes, [{"width": 100}])  # senza 'op'


def test_resize_without_dimensions_raises(synthetic_image_bytes):
    with pytest.raises(InvalidParametersError):
        process_image(synthetic_image_bytes, [{"op": "resize"}])


def test_blur_with_invalid_radius_raises(synthetic_image_bytes):
    with pytest.raises(InvalidParametersError):
        process_image(synthetic_image_bytes, [{"op": "blur", "radius": -1}])


def test_corrupt_image_raises(synthetic_image_bytes):
    corrupt = b"this is not a valid image"
    with pytest.raises(ImageProcessingError):
        process_image(corrupt, [{"op": "resize", "width": 100}])


def test_operations_must_be_list(synthetic_image_bytes):
    with pytest.raises(InvalidParametersError):
        process_image(synthetic_image_bytes, "not a list")  # type: ignore


# Test su immagini reali (skippati se i file non esistono)

def test_real_image_resize(small_image_bytes):
    """Smoke test su small.jpg reale."""
    result = process_image(
        small_image_bytes,
        [{"op": "resize", "width": 400}],
    )
    img = Image.open(BytesIO(result))
    assert img.size[0] == 400


def test_real_image_full_pipeline(small_image_bytes):
    """Pipeline completa su small.jpg."""
    result = process_image(
        small_image_bytes,
        [
            {"op": "resize", "width": 600},
            {"op": "blur", "radius": 3},
            {"op": "edge_enhance"},
            {"op": "grayscale"},
        ],
    )
    img = Image.open(BytesIO(result))
    img.verify()
