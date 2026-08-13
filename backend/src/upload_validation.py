MAX_UPLOAD_BYTES = 8 * 1024 * 1024
SIGNATURES = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"RIFF", ".webp"),
)


def validate_image(content: bytes) -> str:
    if not content or len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Image must be between 1 byte and 8 MB.")
    for signature, extension in SIGNATURES:
        if content.startswith(signature):
            if extension == ".webp" and content[8:12] != b"WEBP":
                break
            return extension
    raise ValueError("Upload a valid JPG, PNG, or WEBP image.")
