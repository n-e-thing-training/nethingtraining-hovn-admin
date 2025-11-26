import os
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from db import get_db
from models import (
    Student,
    Booking,
    Order,
    Session as SessionModel,
    Certificate,
)

from redcross import scrape_certs_for_email
from emailer import (
    send_cert_report,
    send_one_off_lookup,
    send_migration_notice,
    send_cert_lookup_reply,
)

# ------------------------------------------------------
# FASTAPI APP
# ------------------------------------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
ASSETS_DIR = os.path.join(FRONTEND_DIST, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


def spa_index():
    return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))

# ------------------------------------------------------
# HELPERS
# ------------------------------------------------------

def _parse_date(x: str | None) -> date | None:
    if not x:
        return None
    for fmt in ("%m/%d/%Y", "%b %d, %Y", "%b %d, %y"):
        try:
            return datetime.strptime(x.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _serialize_cert(cert: Certificate, student: Student | None = None) -> Dict[str, Any]:
    def fmt(d: date | None) -> str | None:
        return d.strftime("%m/%d/%Y") if d else None

    out = {
        "cert_id": cert.cert_id,
        "course_name": cert.course_name,
        "course_code": cert.course_code,
        "format": cert.format,
        "issue_date": fmt(cert.issue_date),
        "expiry_date": fmt(cert.expiry_date),
        "issuer_org": cert.issuer_org,
        "instructor_name": cert.instructor_name,
    }
    if student:
        out["student_id"] = student.id
        name = f"{student.first_name or ''} {student.last_name or ''}".strip()
        out["student_name"] = name or student.email
    return out


def _serialize_cert_ephemeral(c: dict) -> dict:
    """Used for store=false external checks."""
    # Special 90‑day skills session rule (ephemeral mode)
    issue = _parse_date(c.get("issue_date"))
    special_expiry = None
    name_str = (c.get("course_name") or "").lower()
    if "eligible for skills session within 90 days" in name_str:
        if issue:
            special_expiry = issue + timedelta(days=90)
    return {
        "cert_id": c.get("cert_id"),
        "course_name": c.get("course_name"),
        "course_code": c.get("course_code"),
        "format": c.get("format"),
        "issue_date": c.get("issue_date"),
        "expiry_date": (
            special_expiry.strftime("%m/%d/%Y") if special_expiry
            else c.get("expiry_date")
        ),
        "issuer_org": c.get("issuer_org")
            or c.get("agency_org_name")
            or c.get("org_name"),
        "instructor_name": c.get("instructor_name"),
    }


def _upsert_certs_for_student(db: Session, student: Student, certs: List[Dict[str, Any]]):
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

        # Special rule: Skills Session eligible within 90 days
        name_str = (c.get("course_name") or "").lower()
        if "eligible for skills session within 90 days" in name_str:
            if obj.issue_date:
                obj.expiry_date = obj.issue_date + timedelta(days=90)

        obj.issuer_org = (
            c.get("issuer_org")
            or c.get("agency_org_name")
            or c.get("org_name")
        )

        obj.instructor_name = c.get("instructor_name")

    db.commit()

    return db.query(Certificate).filter(Certificate.student_id == student.id).all()


def _extract_first_email(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return m.group(0).lower() if m else None


def _is_internal(sender: str) -> bool:
    return sender.lower().endswith("@nethingtraining.com")


# ------------------------------------------------------
# API ROUTES
# ------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


# -------------------- STUDENTS -------------------------

@app.get("/api/students")
def list_students(db: Session = Depends(get_db)):
    return [
        {
            "id": s.id,
            "hovn_student_id": s.hovn_student_id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "phone": s.phone_e164,
        }
        for s in db.query(Student).all()
    ]



@app.post("/api/students/create")
def create_student(payload: dict, db: Session = Depends(get_db)):
    s = Student(
        hovn_student_id=payload.get("hovn_student_id"),
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
        email=(payload.get("email") or "").lower().strip(),
        phone_e164=payload.get("phone"),
    )
    db.add(s)
    db.commit()
    db.refresh(s)

    # Scrape certs
    scraped = scrape_certs_for_email(s.email) or []
    saved = []
    if scraped:
        saved = _upsert_certs_for_student(db, s, scraped)

    # Email YOU internally
    send_cert_report(s, [_serialize_cert(c, s) for c in saved])

    return {"status": "ok", "student_id": s.id}


# PATCH endpoint to update student fields
@app.patch("/api/students/{student_id}")
def update_student(student_id: int, payload: dict, db: Session = Depends(get_db)):
    s = db.query(Student).filter(Student.id == student_id).one_or_none()
    if not s:
        return {"error": "not found"}

    # Update allowed fields
    for field in ["first_name", "last_name", "email", "phone_e164"]:
        if field in payload:
            setattr(s, field, payload[field])

    db.commit()
    db.refresh(s)

    return {
        "status": "ok",
        "student": {
            "id": s.id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "email": s.email,
            "phone": s.phone_e164,
        }
    }


# -------------------- MIGRATION -------------------------

@app.post("/api/migrate/bookings")
def migrate_students_by_booking_refs(payload: dict, db: Session = Depends(get_db)):
    refs = payload.get("booking_refs") or []
    refs = [str(x).strip() for x in refs if str(x).strip()]

    if not refs:
        return {"status": "ok", "processed_students": 0}

    bookings = (
        db.query(Booking)
        .filter(Booking.hovn_booking_ref.in_(refs))
        .all()
    )

    students = {}
    for b in bookings:
        if b.student and b.student.id not in students:
            students[b.student.id] = b.student

    processed = 0
    for s in students.values():
        if not s.email:
            continue
        scraped = scrape_certs_for_email(s.email) or []
        if scraped:
            saved = _upsert_certs_for_student(db, s, scraped)
            processed += 1

    return {
        "status": "ok",
        "processed_students": processed,
        "processed_bookings": len(bookings),
    }


# -------------------- CERT LOOKUP -------------------------

@app.post("/api/certs/lookup")
def lookup_certs(email: str, db: Session = Depends(get_db)):
    """
    DB-first lookup used by StudentDetailPage and CertLookupPage.
    """
    email = (email or "").lower().strip()
    if not email:
        return []

    student = db.query(Student).filter(Student.email.ilike(email)).one_or_none()

    # Student exists + has certs → use DB
    if student:
        existing = db.query(Certificate).filter(
            Certificate.student_id == student.id
        ).all()
        if existing:
            return [_serialize_cert(c, student) for c in existing]

    # Otherwise scrape
    scraped = scrape_certs_for_email(email) or []

    # Save only if student exists
    if student and scraped:
        saved = _upsert_certs_for_student(db, student, scraped)
        return [_serialize_cert(c, student) for c in saved]

    # No student → ephemeral
    return [_serialize_cert_ephemeral(c) for c in scraped]


@app.post("/api/certs/check-email")
def cert_check_safe(payload: dict):
    """
    For Zoho → Deluge invoke. ALWAYS store=false.
    """
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return {"error": "missing email"}

    scraped = scrape_certs_for_email(email) or []
    clean = [_serialize_cert_ephemeral(x) for x in scraped]

    return {"email": email, "count": len(clean), "certs": clean}


@app.get("/api/certs/all")
def cert_database(db: Session = Depends(get_db)):
    rows = (
        db.query(Certificate, Student)
        .join(Student, Certificate.student_id == Student.id)
        .order_by(Certificate.added_at.desc())
        .all()
    )
    return [_serialize_cert(c, s) for c, s in rows]


# -------------------- EMAIL WEBHOOK -------------------------

@app.post("/api/email-webhook/cert-lookup")
def inbound_email(payload: dict):
    """
    Handles inbound cert lookup emails.
    """
    sender = (payload.get("from") or payload.get("sender") or "").lower().strip()
    subject = (payload.get("subject") or "")
    body = (payload.get("text") or "")

    target = (
        _extract_first_email(subject)
        or _extract_first_email(body)
    )

    if not target:
        send_cert_lookup_reply(
            to_email=sender,
            subject="Certification lookup error",
            body="No valid email address found in your message."
        )
        return {"status": "no-email"}

    scraped = scrape_certs_for_email(target) or []
    normalized = [_serialize_cert_ephemeral(c) for c in scraped]

    internal = _is_internal(sender)

    # internal → all certs
    if internal:
        lines = [f"Cert lookup for {target}", ""]
        if not normalized:
            lines.append("No certifications found.")
        else:
            for c in normalized:
                lines.append(
                    f"- {c['course_name']}  "
                    f"(ID {c['cert_id']})  "
                    f"Issued {c['issue_date']}  "
                    f"Expires {c['expiry_date']}  "
                    f"Provider: {c['issuer_org']}"
                )
        reply = "\n".join(lines)
    else:
        # external → only n.e. thing training-issued
        issued_by_net = [
            c for c in normalized
            if "n.e. thing training" in (c.get("issuer_org") or "").lower()
        ]
        lines = [f"Certification lookup for {target}", ""]
        if not issued_by_net:
            lines.append(
                "No n.e. thing training certifications were found."
            )
        else:
            for c in issued_by_net:
                lines.append(
                    f"- {c['course_name']} (ID {c['cert_id']})\n"
                    f"  Issued: {c['issue_date']}  Expires: {c['expiry_date']}\n"
                    f"  Provider: {c['issuer_org']}"
                )
        reply = "\n".join(lines)

    send_cert_lookup_reply(
        to_email=sender,
        subject=f"Certification lookup for {target}",
        body=reply,
    )

    return {"status": "ok", "email": target}


# ------------------------------------------------------
# SPA ROUTES
# ------------------------------------------------------

@app.get("/")
def root():
    return spa_index()

@app.get("/{path:path}")
def catch_all(path: str):
    if path.startswith("api/"):
        return {"detail": "Not Found"}
    return spa_index()