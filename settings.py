import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# Postgres connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_xlz8Uq2omAMW@ep-weathered-waterfall-a82hrp3w-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require",
)

# Hovn admin provider slug
HOVN_PROVIDER_SLUG = os.getenv("HOVN_PROVIDER_SLUG", "ne-thing-training")

# Session cookie for Hovn admin (copy from browser devtools)
# Example format:
#   hsid=...; ssid=...; other_cookie=...
HOVN_SESSION_COOKIE = os.getenv("HOVN_SESSION_COOKIE", "")
