#!/usr/bin/env python3
import sys
import json
import os

from sqlalchemy.orm import Session

# --- existing internal modules you already have ---
from hovn_scraper import scrape_booking_and_session
from normalize import normalize_full_bundle
from db_pipeline import persist_full_normalized_bundle
from db import get_db
from models import Student, Certificate
from redcross import scrape_certs_for_email

# ---------------------------------------------------------
# Helper: upsert ARC certs (copied from main.py)
# ---------------------------------------------------------
from datetime import datetime, date

def _parse_date(x: str | None):
    if not x:
        return None
    for fmt in ("%m/%d/%Y", "%b %d, %Y", "%b %d, %y"):
        try:
            return datetime.strptime(x.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _upsert_certs_for_student(db: Session, student: Student, certs):
    """Exact same logic as main.py — ARC cert_id is unique key."""
    if not certs:
        return []

    for c in certs:
        cert_id = c.get("cert_id")
        if not cert_id:
            continue

        obj = db.query(Certificate).filter(Certificate.cert_id == cert_id).one_or_none()
        if obj is None:
            obj = Certificate(student_id=student.id, cert_id=cert_id)
            db.add(obj)

        obj.course_name = c.get("course_name")
        obj.course_code = c.get("course_code")
        obj.format = c.get("format")

        obj.issue_date = _parse_date(c.get("issue_date"))
        obj.expiry_date = _parse_date(c.get("expiry_date"))

        obj.issuer_org = (
            c.get("issuer_org")
            or c.get("agency_org_name")
            or c.get("org_name")
        )
        obj.instructor_name = c.get("instructor_name")

    db.commit()
    return db.query(Certificate).filter(Certificate.student_id == student.id).all()


# ---------------------------------------------------------
# Main runner for ONE booking ref
# ---------------------------------------------------------
def process_single_ref(booking_ref: str, db: Session):
    print(f"\n🔎  Processing {booking_ref}...")

    # 1) SCRAPE BOOKING + SESSION
    try:
        scraped = scrape_booking_and_session(booking_ref)
    except Exception as e:
        print(f"❌ ERROR scraping {booking_ref}: {e}")
        return

    if not scraped:
        print("❌ No data returned from scraper.")
        return

    print(f"📥 Scraped OK for {booking_ref}")

    # 2) NORMALIZE
    normalized = normalize_full_bundle(scraped)
    print("📐 Normalized bundle ready.")

    # 3) WRITE BOOKING, SESSION, ORDER, STUDENT into DB
    try:
        persist_full_normalized_bundle(normalized)
        print("🗄️  DB write successful (HOVN bundle).")
    except Exception as e:
        print(f"❌ ERROR writing to DB: {e}")
        return

    # 4) ARC CERT SCRAPE + STORE (NO EMAILS)
    student_email = normalized.get("student", {}).get("email")
    if not student_email:
        print("⚠️ No student email found — skipping ARC certs.")
        return

    student_email = student_email.lower().strip()

    # Find student in DB
    student = (
        db.query(Student)
        .filter(Student.email.ilike(student_email))
        .one_or_none()
    )

    if not student:
        print(f"⚠️ Student for {student_email} not found after persist() — skipping certs.")
        return

    print(f"📡 Scraping ARC certs for {student_email}...")

    arc = scrape_certs_for_email(student_email) or []
    if not arc:
        print("ℹ️ No ARC certifications found.")
        return

    print(f"📄 Found {len(arc)} ARC certs. Saving...")
    _upsert_certs_for_student(db, student, arc)

    print(f"✅ DONE {booking_ref}: Student {student_email} fully synced.")


# ---------------------------------------------------------
# MAIN: process txt file or command arguments
# ---------------------------------------------------------
def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python hovn_sync_full.py refs.txt")
        print("  python hovn_sync_full.py brn_ABC123 brn_DEF456 ...")
        sys.exit(1)

    # Load booking refs
    args = sys.argv[1:]

    # Case A: they passed a txt file
    if len(args) == 1 and os.path.isfile(args[0]) and args[0].endswith(".txt"):
        with open(args[0], "r") as f:
            booking_refs = [
                line.strip()
                for line in f.readlines()
                if line.strip()
            ]
    else:
        # Case B: direct arguments
        booking_refs = args

    print(f"🚀 Starting sync for {len(booking_refs)} booking refs...")

    db = next(get_db())

    for ref in booking_refs:
        process_single_ref(ref, db)

    print("\n🎉 ALL DONE — Migration complete.\n")


if __name__ == "__main__":
    main()