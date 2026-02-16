import os
from pathlib import Path

try:
    # Optional dependency; used only to load a local .env file in development.
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

# Storage / DB
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "riskcheck.db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "storage"))

# Google Programmable Search Engine (Custom Search JSON API)
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
GOOGLE_CSE_CX = os.getenv("GOOGLE_CSE_CX", "").strip()
GOOGLE_CSE_GL = os.getenv("GOOGLE_CSE_GL", "pk").strip()  # bias results to Pakistan by default
GOOGLE_CSE_HL = os.getenv("GOOGLE_CSE_HL", "en").strip()

# Admin actions (approve/reject community reports)
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

# CORS
FRONTEND_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173",
    ).split(",")
    if o.strip()
]

# Security: block SSRF to internal networks when fetching URLs
BLOCK_PRIVATE_NETS = os.getenv("BLOCK_PRIVATE_NETS", "1").strip() not in ("0", "false", "False")

# Networking
HTTP_TIMEOUT_S = float(os.getenv("HTTP_TIMEOUT_S", "8"))

# Google search cache (seconds)
SEARCH_CACHE_TTL_S = int(os.getenv("SEARCH_CACHE_TTL_S", str(12 * 60 * 60)))

# App branding
APP_NAME = os.getenv("APP_NAME", "RiskCheck")
BRAND_OWNER = os.getenv("BRAND_OWNER", "UMERON Technologies")
BRAND_URL = os.getenv("BRAND_URL", "https://umerontechnologies.com")
