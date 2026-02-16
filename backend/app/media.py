# media.py
import hashlib
import os
from pathlib import Path
from typing import Optional, Tuple

try:
    from PIL import Image  # type: ignore
    import imagehash  # type: ignore

    _PHASH_AVAILABLE = True
except Exception:
    Image = None  # type: ignore
    imagehash = None  # type: ignore
    _PHASH_AVAILABLE = False


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def compute_phash(path: str) -> Optional[str]:
    if not _PHASH_AVAILABLE:
        return None
    try:
        img = Image.open(path)
        return str(imagehash.phash(img))
    except Exception:
        return None


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def guess_ext(filename: str, mime_type: Optional[str]) -> str:
    fn = (filename or "").lower()
    if fn.endswith(".png"):
        return ".png"
    if fn.endswith(".jpg") or fn.endswith(".jpeg"):
        return ".jpg"
    if fn.endswith(".webp"):
        return ".webp"
    if mime_type == "image/png":
        return ".png"
    if mime_type == "image/jpeg":
        return ".jpg"
    if mime_type == "image/webp":
        return ".webp"
    return ""


def store_upload_bytes(
    data: bytes,
    upload_dir: str,
    original_filename: Optional[str] = None,
    mime_type: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Stores upload bytes into upload_dir.
    Returns (sha256, saved_path).
    """
    ensure_dir(upload_dir)

    sha = sha256_bytes(data)
    ext = guess_ext(original_filename or "", mime_type)
    stored_name = f"{sha}{ext}" if ext else sha
    saved_path = str(Path(upload_dir) / stored_name)

    if not os.path.exists(saved_path):
        with open(saved_path, "wb") as f:
            f.write(data)

    return sha, saved_path
