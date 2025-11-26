import sys
import json

from hovn_scraper import scrape_booking_and_session
from normalize import normalize_full_bundle
from db_pipeline import persist_full_normalized_bundle


def run_pipeline(booking_ref: str):
    print(f"[PIPELINE] Starting full pipeline for {booking_ref}...")

    # 1) Scrape Booking + Session
    scraped = scrape_booking_and_session(booking_ref)
    print("[PIPELINE] Raw scraped:")
    print(json.dumps(scraped, indent=2))

    # 2) Normalize (enterprise normalization)
    normalized = normalize_full_bundle(scraped)
    print("[PIPELINE] Normalized:")
    print(json.dumps(normalized, indent=2))

    # 3) Persist to Postgres
    persist_full_normalized_bundle(normalized)
    print("[PIPELINE] Database write complete.")

    print("[PIPELINE] DONE.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_pipeline.py <BOOKING_REF>")
        sys.exit(1)

    run_pipeline(sys.argv[1])


if __name__ == "__main__":
    main()