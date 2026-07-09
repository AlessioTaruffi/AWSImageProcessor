"""
Cloud Image Processing API — Image processor module.

Workload condiviso tra path EC2 (Flask backend) e path Lambda.
Espone una singola funzione `process_image()` che applica una pipeline
configurabile di operazioni a un'immagine.

Le operazioni sono volutamente CPU-intensive (Pillow è single-threaded
puro Python/C) per stressare le risorse di calcolo nei benchmark.
"""

from io import BytesIO
from typing import Any

from PIL import Image, ImageFilter, ImageOps

# Eccezioni custom

class ProcessorError(Exception):
    """Base exception del modulo."""


class UnknownOperationError(ProcessorError):
    """Sollevata se la pipeline contiene un'operazione non registrata."""


class InvalidParametersError(ProcessorError):
    """Sollevata se i parametri di un'operazione sono mancanti o invalidi."""


class ImageProcessingError(ProcessorError):
    """Sollevata se Pillow fallisce durante una trasformazione."""


# Operazioni atomiche
# Ogni operazione prende (Image, dict_di_parametri) e ritorna una nuova Image.

def _op_resize(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Ridimensiona l'immagine. Accetta `width` e/o `height`.
    Se ne è specificato solo uno, l'altro è calcolato mantenendo l'aspect ratio.
    """
    width = params.get("width")
    height = params.get("height")

    if width is None and height is None:
        raise InvalidParametersError("resize: serve almeno 'width' o 'height'")

    orig_w, orig_h = img.size
    if width is None:
        width = int(orig_w * (height / orig_h))
    elif height is None:
        height = int(orig_h * (width / orig_w))

    return img.resize((int(width), int(height)), resample=Image.LANCZOS)


def _op_grayscale(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Converte l'immagine in scala di grigi (mode L), poi torna in RGB
    per mantenere coerenza nei salvataggi successivi."""
    return img.convert("L").convert("RGB")


def _op_blur(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Applica un Gaussian blur. Parametro `radius` (default 5).
    Più alto è il radius, più pesante è il calcolo."""
    radius = params.get("radius", 5)
    if not isinstance(radius, (int, float)) or radius < 0:
        raise InvalidParametersError(f"blur: 'radius' invalido ({radius})")
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def _op_edge_enhance(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Esalta i bordi tramite il filtro EDGE_ENHANCE_MORE di Pillow.
    Esegue una convoluzione 3x3 sull'intera immagine."""
    return img.filter(ImageFilter.EDGE_ENHANCE_MORE)


def _op_composite(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Applica una pipeline composta. Esiste un set di pipeline pre-definite
    selezionabili via `preset` (default 'heavy'), oppure una pipeline custom
    via `pipeline` (lista di operazioni come quella accettata da process_image).
    """
    preset = params.get("preset", "heavy")
    custom_pipeline = params.get("pipeline")

    if custom_pipeline is not None:
        ops = custom_pipeline
    elif preset == "heavy":
        # Pipeline pesante: blur grosso + enhance + grayscale + resize finale
        ops = [
            {"op": "blur", "radius": 8},
            {"op": "edge_enhance"},
            {"op": "grayscale"},
            {"op": "resize", "width": 1024},
        ]
    elif preset == "light":
        ops = [
            {"op": "resize", "width": 800},
            {"op": "grayscale"},
        ]
    else:
        raise InvalidParametersError(f"composite: preset sconosciuto '{preset}'")

    for sub_op in ops:
        op_name = sub_op.get("op")
        if op_name not in OPERATIONS:
            raise UnknownOperationError(f"composite: op interna sconosciuta '{op_name}'")
        img = OPERATIONS[op_name](img, sub_op)
    return img


# Registry delle operazioni
# Aggiungere qui nuove operazioni per renderle utilizzabili nelle pipeline.

OPERATIONS = {
    "resize": _op_resize,
    "grayscale": _op_grayscale,
    "blur": _op_blur,
    "edge_enhance": _op_edge_enhance,
    "composite": _op_composite,
}


# API pubblica

def process_image(
    image_bytes: bytes,
    operations: list[dict[str, Any]],
    output_format: str = "JPEG",
    output_quality: int = 90,
) -> bytes:
    """Applica una pipeline di operazioni a un'immagine in input.

    Args:
        image_bytes: bytes dell'immagine in input (qualsiasi formato Pillow legga).
        operations: lista di dict che descrivono la pipeline.
                    Ogni dict deve contenere almeno la chiave 'op' con il nome
                    dell'operazione e gli eventuali parametri.
                    Esempio:
                        [
                            {"op": "resize", "width": 1024},
                            {"op": "blur", "radius": 5},
                            {"op": "grayscale"}
                        ]
        output_format: formato di output (default 'JPEG').
        output_quality: qualità JPEG 1-100 (default 90).

    Returns:
        bytes dell'immagine processata.

    Raises:
        UnknownOperationError: operazione non registrata in OPERATIONS.
        InvalidParametersError: parametri mancanti o non validi.
        ImageProcessingError: Pillow ha sollevato un'eccezione durante il processing.
    """
    if not isinstance(operations, list):
        raise InvalidParametersError("'operations' deve essere una lista")

    try:
        img = Image.open(BytesIO(image_bytes))
        img.load()
    except Exception as e:
        raise ImageProcessingError(f"Impossibile aprire l'immagine: {e}") from e

    for idx, op_spec in enumerate(operations):
        if not isinstance(op_spec, dict):
            raise InvalidParametersError(f"operazione #{idx}: deve essere un dict")
        op_name = op_spec.get("op")
        if op_name is None:
            raise InvalidParametersError(f"operazione #{idx}: manca la chiave 'op'")
        if op_name not in OPERATIONS:
            raise UnknownOperationError(
                f"operazione #{idx}: '{op_name}' non riconosciuta. "
                f"Disponibili: {list(OPERATIONS.keys())}"
            )

        try:
            img = OPERATIONS[op_name](img, op_spec)
        except ProcessorError:
            raise
        except Exception as e:
            raise ImageProcessingError(
                f"errore in operazione #{idx} '{op_name}': {e}"
            ) from e

    # Salvataggio: converte sempre in RGB per evitare problemi con JPEG
    output = BytesIO()
    try:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output, format=output_format, quality=output_quality)
    except Exception as e:
        raise ImageProcessingError(f"errore durante il salvataggio: {e}") from e

    return output.getvalue()
