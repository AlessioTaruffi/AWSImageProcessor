"""
Cloud Image Processing API — Image processor module.

Workload condiviso tra path EC2 (Flask backend) e path Lambda.
Espone una singola funzione `process_image()` che applica una pipeline
configurabile di operazioni a un'immagine.

Operazioni supportate (concordate con il team):
    resize:     width
    blur:       radius
    grayscale:  (nessun parametro)
    rotate:     angle (gradi, senso ORARIO)
"""

from io import BytesIO
from typing import Any

from PIL import Image, ImageFilter


# ---------------------------------------------------------------------------
# Eccezioni custom
# ---------------------------------------------------------------------------

class ProcessorError(Exception):
    """Base exception del modulo."""


class UnknownOperationError(ProcessorError):
    """Sollevata se la pipeline contiene un'operazione non registrata."""


class InvalidParametersError(ProcessorError):
    """Sollevata se i parametri di un'operazione sono mancanti o invalidi."""


class ImageProcessingError(ProcessorError):
    """Sollevata se Pillow fallisce durante una trasformazione."""


# ---------------------------------------------------------------------------
# Operazioni
# ---------------------------------------------------------------------------

def _op_resize(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Ridimensiona l'immagine. Richiede `width`. L'altezza è calcolata
    automaticamente mantenendo l'aspect ratio originale."""
    width = params.get("width")
    if width is None:
        raise InvalidParametersError("resize: 'width' è obbligatorio")
    if not isinstance(width, (int, float)) or width <= 0:
        raise InvalidParametersError(f"resize: 'width' invalido ({width})")

    orig_w, orig_h = img.size
    height = int(orig_h * (width / orig_w))
    return img.resize((int(width), height), resample=Image.LANCZOS)


def _op_blur(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Applica un Gaussian blur. Richiede `radius` (>=0)."""
    radius = params.get("radius")
    if radius is None:
        raise InvalidParametersError("blur: 'radius' è obbligatorio")
    if not isinstance(radius, (int, float)) or radius < 0:
        raise InvalidParametersError(f"blur: 'radius' invalido ({radius})")
    return img.filter(ImageFilter.GaussianBlur(radius=radius))


def _op_grayscale(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Converte l'immagine in scala di grigi. Nessun parametro."""
    return img.convert("L").convert("RGB")


def _op_rotate(img: Image.Image, params: dict[str, Any]) -> Image.Image:
    """Ruota l'immagine. Richiede `angle` in gradi, in senso ORARIO.
    Internamente Pillow usa l'antiorario, quindi neghiamo l'angolo.
    `expand=True` ridimensiona il canvas per non tagliare i bordi."""
    angle = params.get("angle")
    if angle is None:
        raise InvalidParametersError("rotate: 'angle' è obbligatorio")
    if not isinstance(angle, (int, float)):
        raise InvalidParametersError(f"rotate: 'angle' invalido ({angle})")
    return img.rotate(-angle, expand=True, resample=Image.BICUBIC)


# ---------------------------------------------------------------------------
# Registry delle operazioni
# ---------------------------------------------------------------------------

OPERATIONS = {
    "resize": _op_resize,
    "blur": _op_blur,
    "grayscale": _op_grayscale,
    "rotate": _op_rotate,
}


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

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
                    Ogni dict deve contenere la chiave 'op' con il nome
                    dell'operazione e gli eventuali parametri.
                    Esempio:
                        [
                            {"op": "resize", "width": 1024},
                            {"op": "blur", "radius": 5},
                            {"op": "grayscale"},
                            {"op": "rotate", "angle": 90}
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

    output = BytesIO()
    try:
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(output, format=output_format, quality=output_quality)
    except Exception as e:
        raise ImageProcessingError(f"errore durante il salvataggio: {e}") from e

    return output.getvalue()
