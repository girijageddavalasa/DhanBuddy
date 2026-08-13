from pathlib import Path


class OCRUnavailableError(RuntimeError):
    pass


def extract_text(image_path: Path) -> str:
    """Extract text through the optional local Tesseract provider."""
    try:
        import pytesseract
        from PIL import Image

        with Image.open(image_path) as image:
            return pytesseract.image_to_string(image).strip()
    except (ImportError, OSError) as error:
        raise OCRUnavailableError("Local OCR is unavailable.") from error
