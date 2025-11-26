import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Postgres connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:admin@localhost:5432/hovn",
)

# Hovn admin provider slug
HOVN_PROVIDER_SLUG = os.getenv("HOVN_PROVIDER_SLUG", "ne-thing-training")

# Session cookie for Hovn admin (copy from browser devtools)
# Example format:
#   hsid=...; ssid=...; other_cookie=...
HOVN_SESSION_COOKIE = os.getenv("HOVN_SESSION_COOKIE", "")