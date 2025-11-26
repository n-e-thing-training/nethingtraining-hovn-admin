import json
import re
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from sqlalchemy.orm import Session

from settings import HOVN_PROVIDER_SLUG, HOVN_SESSION_COOKIE
from db import get_session
from models import Student, Session as CourseSession, Booking


# ---------- Hovn HTTP session ----------

def _build_cookie_jar_from_string(cookie_str: str) -> Dict[str, str]:
    """
    Turn a 'name=value; other=value2' string into a dict.
    """
    jar: Dict[str, str] = {}
    if not cookie_str:
        return jar
    parts = [p.strip() for p in cookie_str.split(";") if p.strip()]
    for part in parts:
        if "=" in part:
            name, value = part.split("=", 1)
            jar[name.strip()] = value.strip()
    return jar


def _create_hovn_session() -> requests.Session:
    if not HOVN_SESSION_COOKIE:
        raise RuntimeError(
            "HOVN_SESSION_COOKIE is not set. "
            "Set it in your .env to your admin cookie string."
        )

    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://www.hovn.app/admin/{HOVN_PROVIDER_SLUG}/bookings",
        }
    )

    cookies = _build_cookie_jar_from_string(HOVN_SESSION_COOKIE)
    s.cookies.update(cookies)
    return s


# ---------- Parsing helpers ----------

def _normalize_dates_in_json_like(s: str) -> str:
    """
    Hovn uses '$D2025-12-07T19:30:00.000Z' in the flight data JSON.
    Replace '"$D' with '"' so json.loads works.

    Example:  "$D2025-12-07T19:30:00.000Z" -> "2025-12-07T19:30:00.000Z"
    """
    return s.replace('"$D', '"')


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        # Hovn uses ...Z (UTC)
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _extract_booking_json_from_html(html: str, booking_ref: str) -> Dict[str, Any]:
    """
    Extract the 'booking' object for this reference from the admin booking page HTML.

    We rely on patterns we saw in booking.html, like:

      "booking":{"id":12104,...,"referenceNumber":"brn_YZWADB",...},"disabled":false
    """
    pattern = (
        '"booking":('
        r'\{.*?"referenceNumber":"' + re.escape(booking_ref) + r'".*?}}'
        '),"disabled"'
    )

    m = re.search(pattern, html, re.DOTALL)
    if not m:
        raise RuntimeError(
            f"Could not locate booking JSON for {booking_ref} in HTML."
        )

    booking_str = m.group(1)
    booking_str = _normalize_dates_in_json_like(booking_str)

    try:
        data = json.loads(booking_str)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to decode booking JSON: {e}") from e

    return data


# ---------- Upsert helpers ----------

def _upsert_student(db: Session, booking_data: Dict[str, Any]) -> Student:
    student_data = booking_data.get("student")
    if not student_data:
        raise RuntimeError("Booking data has no 'student' object.")

    hovn_student_id = student_data["id"]
    first_name = student_data.get("firstName") or ""
    last_name = student_data.get("lastName") or ""
    email = student_data.get("email") or ""
    phone = student_data.get("phoneNumber")

    student = (
        db.query(Student)
        .filter(Student.hovn_student_id == hovn_student_id)
        .one_or_none()
    )

    if student is None:
        student = Student(
            hovn_student_id=hovn_student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            account_id=student_data.get("accountId"),
            service_provider_id=student_data.get("serviceProviderId"),
            raw_json=student_data,
        )
        db.add(student)
    else:
        student.first_name = first_name
        student.last_name = last_name
        student.email = email
        student.phone = phone
        student.account_id = student_data.get("accountId")
        student.service_provider_id = student_data.get("serviceProviderId")
        student.raw_json = student_data

    return student


def _upsert_session(db: Session, booking_data: Dict[str, Any]) -> CourseSession:
    session_data = booking_data.get("courseSession")
    if not session_data:
        raise RuntimeError("Booking data has no 'courseSession' object.")

    hovn_session_id = session_data["id"]
    hovn_session_cuid = session_data.get("cuid")
    course_offering_id = session_data.get("courseOfferingId")
    course_id = session_data.get("courseId")

    course_name = None
    course_slug = None
    course_obj = session_data.get("course")
    # On some pages this is a full object, in others it's a pointer string.
    if isinstance(course_obj, dict):
        course_name = course_obj.get("name")
        course_slug = course_obj.get("slug")

    starts_at = _parse_iso(session_data.get("startsAt"))
    ends_at = _parse_iso(session_data.get("endsAt"))

    location = session_data.get("location") or {}
    location_id = location.get("id")
    location_label = location.get("label")
    address1 = location.get("address1")
    address2 = location.get("address2")
    city = location.get("city")
    state = location.get("state")
    postal_code = location.get("postalCode")

    sess = (
        db.query(CourseSession)
        .filter(CourseSession.hovn_session_id == hovn_session_id)
        .one_or_none()
    )

    if sess is None:
        sess = CourseSession(
            hovn_session_id=hovn_session_id,
            hovn_session_cuid=hovn_session_cuid,
            course_offering_id=course_offering_id,
            course_id=course_id,
            course_name=course_name,
            course_slug=course_slug,
            starts_at=starts_at,
            ends_at=ends_at,
            time_zone=session_data.get("timeZone"),
            is_private=session_data.get("isPrivate"),
            seats=session_data.get("seats"),
            location_id=location_id,
            location_label=location_label,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            postal_code=postal_code,
            instructor_user_id=session_data.get("instructorUserId"),
            client_id=session_data.get("clientId"),
            raw_json=session_data,
        )
        db.add(sess)
    else:
        sess.hovn_session_cuid = hovn_session_cuid
        sess.course_offering_id = course_offering_id
        sess.course_id = course_id
        if course_name:
            sess.course_name = course_name
        if course_slug:
            sess.course_slug = course_slug
        sess.starts_at = starts_at
        sess.ends_at = ends_at
        sess.time_zone = session_data.get("timeZone")
        sess.is_private = session_data.get("isPrivate")
        sess.seats = session_data.get("seats")
        sess.location_id = location_id
        sess.location_label = location_label
        sess.address1 = address1
        sess.address2 = address2
        sess.city = city
        sess.state = state
        sess.postal_code = postal_code
        sess.instructor_user_id = session_data.get("instructorUserId")
        sess.client_id = session_data.get("clientId")
        sess.raw_json = session_data

    return sess


def _upsert_booking(
    db: Session,
    booking_ref: str,
    booking_data: Dict[str, Any],
    student: Student,
    sess: CourseSession,
) -> Booking:
    hovn_booking_id = booking_data.get("id")
    hovn_booking_cuid = booking_data.get("cuid")

    booking = (
        db.query(Booking)
        .filter(Booking.hovn_booking_ref == booking_ref)
        .one_or_none()
    )

    created_at_hovn = _parse_iso(booking_data.get("createdAt"))
    updated_at_hovn = _parse_iso(booking_data.get("updatedAt"))
    canceled_at = _parse_iso(booking_data.get("canceledAt"))
    verified_at = _parse_iso(booking_data.get("verifiedAt"))

    if booking is None:
        booking = Booking(
            hovn_booking_id=hovn_booking_id,
            hovn_booking_cuid=hovn_booking_cuid,
            hovn_booking_ref=booking_ref,
            student=student,
            session=sess,
            course_order_item_id=booking_data.get("courseOrderItemId"),
            account_id=booking_data.get("accountId"),
            booked_by_account_id=booking_data.get("bookedByAccountId"),
            course_session_id=booking_data.get("courseSessionId"),
            is_ready_for_certificate=booking_data.get("isReadyForCertificate"),
            verified_at=verified_at,
            created_at_hovn=created_at_hovn,
            updated_at_hovn=updated_at_hovn,
            canceled_at=canceled_at,
            status="active" if not canceled_at else "canceled",
            raw_json=booking_data,
        )
        db.add(booking)
    else:
        booking.hovn_booking_id = hovn_booking_id
        booking.hovn_booking_cuid = hovn_booking_cuid
        booking.student = student
        booking.session = sess
        booking.course_order_item_id = booking_data.get("courseOrderItemId")
        booking.account_id = booking_data.get("accountId")
        booking.booked_by_account_id = booking_data.get("bookedByAccountId")
        booking.course_session_id = booking_data.get("courseSessionId")
        booking.is_ready_for_certificate = booking_data.get("isReadyForCertificate")
        booking.verified_at = verified_at
        booking.created_at_hovn = created_at_hovn
        booking.updated_at_hovn = updated_at_hovn
        booking.canceled_at = canceled_at
        booking.status = "active" if not canceled_at else "canceled"
        booking.raw_json = booking_data

    return booking


# ---------- Public entrypoint ----------

def sync_booking_via_api(booking_ref: str) -> None:
    """
    Fully sync one booking into the DB using the Hovn admin booking page.
    """
    print(f"[API] Syncing booking via admin page: {booking_ref}")

    # HTTP request to booking page
    s = _create_hovn_session()
    url = f"https://www.hovn.app/admin/{HOVN_PROVIDER_SLUG}/bookings/{booking_ref}"

    resp = s.get(url, timeout=20)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to fetch booking page ({resp.status_code}): {url}"
        )

    html = resp.text

    # Extract embedded booking JSON
    booking_data = _extract_booking_json_from_html(html, booking_ref)

    # Persist to DB
    db = get_session()
    try:
        student = _upsert_student(db, booking_data)
        sess = _upsert_session(db, booking_data)
        booking = _upsert_booking(db, booking_ref, booking_data, student, sess)

        db.commit()
        print(
            f"[API] Synced booking {booking_ref} -> "
            f"Booking id={booking.id}, Student id={student.id}, Session id={sess.id}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()