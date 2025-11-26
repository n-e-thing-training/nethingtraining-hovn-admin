# hovn_sync.py
# -------------
# Usage:
#   python hovn_sync.py brn_WFI79F brn_123ABC brn_456DEF
#
# Pulls students from DB using booking refs,
# scrapes ARC certs, stores them, emails internal summary.

import sys
from db import SessionLocal
from models import Booking, Student
from redcross import scrape_certs_for_email
from main import _upsert_certs_for_student  # reuse existing logic
from emailer import send_migration_notice


def run_sync(booking_refs: list[str]):
    db = SessionLocal()
    print(f"🔍 Starting sync for {len(booking_refs)} booking refs...")

    # Normalize refs
    refs = [r.strip() for r in booking_refs if r.strip()]
    if not refs:
        print("No valid booking refs. Exiting.")
        return

    # Pull bookings
    bookings = (
        db.query(Booking)
        .filter(Booking.hovn_booking_ref.in_(refs))
        .all()
    )

    if not bookings:
        print("No matching bookings found in DB.")
        return

    # Collect unique students
    students = {}
    for b in bookings:
        if b.student:
            students[b.student.id] = b.student

    print(f"Found {len(students)} unique students to sync.")

    # Process each student
    for student in students.values():
        if not student.email:
            print(f"Skipping student {student.id} (no email)")
            continue

        print(f"→ Scraping ARC certs for {student.email}...")
        scraped = scrape_certs_for_email(student.email) or []

        if scraped:
            saved = _upsert_certs_for_student(db, student, scraped)
            print(f"   ✓ Saved {len(saved)} certs")

            # Internal-only migration email
            send_migration_notice(
                ref=";".join(refs),
                student=student,
                certs=[{
                    "course_name": c.course_name,
                    "issuer_org": c.issuer_org,
                    "format": c.format,
                    "issue_date": c.issue_date,
                    "expiry_date": c.expiry_date,
                } for c in saved],
            )
        else:
            print("   ⚠ No certs found on ARC.")

    print("🎉 Migration complete!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python hovn_sync.py <booking_ref1> <booking_ref2> ...")
        sys.exit(1)

    booking_refs = sys.argv[1:]
    run_sync(booking_refs)