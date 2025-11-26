# normalized_pipeline.py
from __future__ import annotations

import sys
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db import SessionLocal, engine, Base
from models import (
    Student,
    Agency,
    Course,
    Location,
    Instructor,
    Session,
    Order,
    Booking,
)
from normalize import (
    normalize_phone_e164,
    parse_currency_to_cents,
    parse_iso_utc_and_local,
    parse_address_block,
    parse_instructor_name_and_title,
    extract_hovn_id_from_path,
)
from hovn_scraper import scrape_booking_and_session


# Ensure tables exist
def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_or_create_agency(db, name: Optional[str]) -> Optional[Agency]:
    if not name:
        return None
    stmt = select(Agency).where(Agency.name == name)
    agency = db.execute(stmt).scalar_one_or_none()
    if agency:
        return agency
    agency = Agency(name=name)
    db.add(agency)
    db.flush()
    return agency


def get_or_create_course(db, name: Optional[str], fmt: Optional[str], agency: Optional[Agency]) -> Optional[Course]:
    if not name:
        return None
    agency_id = agency.id if agency else None
    stmt = select(Course).where(
        Course.name == name,
        Course.format == fmt,
        Course.agency_id == agency_id,
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course:
        return course

    course = Course(
        name=name,
        format=fmt,
        agency_id=agency_id,
    )
    db.add(course)
    db.flush()
    return course


def get_or_create_location(db, name: Optional[str], address_raw: Optional[str]) -> Optional[Location]:
    if not name:
        return None

    parsed = parse_address_block(address_raw)

    stmt = select(Location).where(
        Location.name == name,
        Location.address_line1 == parsed["address_line1"],
        Location.city == parsed["city"],
        Location.state == parsed["state"],
        Location.postal_code == parsed["postal_code"],
    )
    loc = db.execute(stmt).scalar_one_or_none()
    if loc:
        return loc

    loc = Location(
        name=name,
        address_line1=parsed["address_line1"],
        city=parsed["city"],
        state=parsed["state"],
        postal_code=parsed["postal_code"],
        country_code=parsed["country_code"],
        raw_address=parsed["raw_address"],
    )
    db.add(loc)
    db.flush()
    return loc


def get_or_create_instructor(db, raw_name: Optional[str]) -> Optional[Instructor]:
    if not raw_name:
        return None

    parsed = parse_instructor_name_and_title(raw_name)
    full_name = parsed["full_name"]

    stmt = select(Instructor).where(Instructor.full_name == full_name)
    inst = db.execute(stmt).scalar_one_or_none()
    if inst:
        # Update title if changed
        if parsed["title"] and inst.title != parsed["title"]:
            inst.title = parsed["title"]
        return inst

    inst = Instructor(
        full_name=full_name,
        first_name=parsed["first_name"],
        last_name=parsed["last_name"],
        title=parsed["title"],
    )
    db.add(inst)
    db.flush()
    return inst


def get_or_create_student(
    db,
    hovn_student_id: Optional[str],
    full_name: Optional[str],
    email: Optional[str],
    phone_raw: Optional[str],
) -> Student:
    # Try by hovn_student_id first
    if hovn_student_id:
        stmt = select(Student).where(Student.hovn_student_id == hovn_student_id)
        student = db.execute(stmt).scalar_one_or_none()
        if student:
            # Update fields
            if full_name:
                first, last = full_name.split(" ", 1) if " " in full_name.strip() else (full_name.strip(), None)
                student.first_name = first or student.first_name
                student.last_name = last or student.last_name
            if email and student.email != email:
                student.email = email
            if phone_raw:
                student.phone_raw = phone_raw
                student.phone_e164 = normalize_phone_e164(phone_raw)
            return student

    # Next, try by email if present
    if email:
        stmt = select(Student).where(Student.email == email)
        student = db.execute(stmt).scalar_one_or_none()
        if student:
            if hovn_student_id and not student.hovn_student_id:
                student.hovn_student_id = hovn_student_id
            if phone_raw:
                student.phone_raw = phone_raw
                student.phone_e164 = normalize_phone_e164(phone_raw)
            if full_name:
                first, last = full_name.split(" ", 1) if " " in full_name.strip() else (full_name.strip(), None)
                if first:
                    student.first_name = first
                if last:
                    student.last_name = last
            return student

    # Create new
    first_name = None
    last_name = None
    if full_name:
        parts = full_name.strip().split()
        if len(parts) == 1:
            first_name = parts[0]
        else:
            first_name = parts[0]
            last_name = " ".join(parts[1:])

    student = Student(
        hovn_student_id=hovn_student_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone_raw=phone_raw,
        phone_e164=normalize_phone_e164(phone_raw) if phone_raw else None,
    )
    db.add(student)
    db.flush()
    return student


def get_or_create_session(
    db,
    hovn_session_id: str,
    course: Optional[Course],
    agency: Optional[Agency],
    location: Optional[Location],
    instructor: Optional[Instructor],
    session_start_iso: Optional[str],
    session_url: Optional[str],
) -> Session:
    stmt = select(Session).where(Session.hovn_session_id == hovn_session_id)
    session = db.execute(stmt).scalar_one_or_none()

    start_utc, start_local = parse_iso_utc_and_local(session_start_iso)

    if session:
        # Update fields
        if course:
            session.course = course
        if agency:
            session.agency = agency
        if location:
            session.location = location
        if instructor:
            session.instructor = instructor
        if start_utc:
            session.start_utc = start_utc
            session.start_local = start_local
        if session_url:
            session.hovn_session_url = session_url
        return session

    session = Session(
        hovn_session_id=hovn_session_id,
        course=course,
        agency=agency,
        location=location,
        instructor=instructor,
        start_utc=start_utc,
        start_local=start_local,
        format=course.format if course else None,
        hovn_session_url=session_url,
    )
    db.add(session)
    db.flush()
    return session


def get_or_create_order(
    db,
    hovn_order_id: str,
    hovn_order_number: Optional[str],
    student: Optional[Student],
    order_datetime_iso: Optional[str],
    amount_str: Optional[str],
    status: Optional[str],
) -> Order:
    stmt = select(Order).where(Order.hovn_order_id == hovn_order_id)
    order = db.execute(stmt).scalar_one_or_none()

    ordered_at_utc, ordered_at_local = parse_iso_utc_and_local(order_datetime_iso)
    amount_cents = parse_currency_to_cents(amount_str)
    currency_code = "USD" if amount_cents is not None else None

    if order:
        if hovn_order_number and order.hovn_order_number != hovn_order_number:
            order.hovn_order_number = hovn_order_number
        if student and order.student_id != student.id:
            order.student = student
        if ordered_at_utc:
            order.ordered_at_utc = ordered_at_utc
            order.ordered_at_local = ordered_at_local
        if amount_cents is not None:
            order.amount_cents = amount_cents
            order.currency_code = currency_code
        if status:
            order.status = status
        return order

    order = Order(
        hovn_order_id=hovn_order_id,
        hovn_order_number=hovn_order_number,
        student=student,
        ordered_at_utc=ordered_at_utc,
        ordered_at_local=ordered_at_local,
        amount_cents=amount_cents,
        currency_code=currency_code,
        status=status,
    )
    db.add(order)
    db.flush()
    return order


def get_or_create_booking(
    db,
    hovn_booking_ref: str,
    student: Optional[Student],
    session: Optional[Session],
    order: Optional[Order],
    status: Optional[str] = "active",
) -> Booking:
    stmt = select(Booking).where(Booking.hovn_booking_ref == hovn_booking_ref)
    booking = db.execute(stmt).scalar_one_or_none()
    if booking:
        if student and booking.student_id != student.id:
            booking.student = student
        if session and booking.session_id != session.id:
            booking.session = session
        if order and booking.order_id != order.id:
            booking.order = order
        if status:
            booking.status = status
        return booking

    booking = Booking(
        hovn_booking_ref=hovn_booking_ref,
        student=student,
        session=session,
        order=order,
        status=status,
    )
    db.add(booking)
    db.flush()
    return booking


def process_booking_ref(booking_ref: str) -> None:
    """
    1. Scrape booking+session via hovn_scraper.
    2. Normalize.
    3. Upsert into Postgres.
    """
    init_db()

    raw = scrape_booking_and_session(booking_ref)

    booking_data = raw.get("booking") or {}
    session_data = raw.get("session") or {}

    hovn_booking_ref = booking_data.get("booking_ref") or booking_ref

    # --- Student ---
    hovn_student_id = extract_hovn_id_from_path(booking_data.get("student_id"))
    student_full_name = booking_data.get("student_name")
    student_email = booking_data.get("student_email")
    student_phone_raw = booking_data.get("student_phone")

    # --- Order ---
    hovn_order_id = extract_hovn_id_from_path(booking_data.get("order_id"))
    hovn_order_number = booking_data.get("order_number")
    order_status = booking_data.get("order_status")
    order_datetime_iso = booking_data.get("order_datetime")
    order_total_str = booking_data.get("order_total")

    # --- Session & related ---
    session_url = booking_data.get("session_url")
    hovn_session_id = session_data.get("session_id_text")
    course_name = session_data.get("course_name")
    fmt = session_data.get("format")
    agency_name = session_data.get("agency")
    session_start_iso = session_data.get("session_date_iso") or session_data.get("session_time_iso")
    location_name = session_data.get("location_name")
    address_raw = booking_data.get("session_address")
    instructor_raw = session_data.get("instructor_name")

    db = SessionLocal()
    try:
        # Agency
        agency = get_or_create_agency(db, agency_name)

        # Course
        course = get_or_create_course(db, course_name, fmt, agency)

        # Location
        location = get_or_create_location(db, location_name, address_raw)

        # Instructor
        instructor = get_or_create_instructor(db, instructor_raw)

        # Student
        student = get_or_create_student(
            db=db,
            hovn_student_id=hovn_student_id,
            full_name=student_full_name,
            email=student_email,
            phone_raw=student_phone_raw,
        )

        # Session
        if not hovn_session_id:
            raise RuntimeError("Session ID is missing from session_data['session_id_text'].")

        session = get_or_create_session(
            db=db,
            hovn_session_id=hovn_session_id,
            course=course,
            agency=agency,
            location=location,
            instructor=instructor,
            session_start_iso=session_start_iso,
            session_url=session_url,
        )

        # Order
        if not hovn_order_id:
            raise RuntimeError("Order ID is missing from booking_data['order_id'].")

        order = get_or_create_order(
            db=db,
            hovn_order_id=hovn_order_id,
            hovn_order_number=hovn_order_number,
            student=student,
            order_datetime_iso=order_datetime_iso,
            amount_str=order_total_str,
            status=order_status,
        )

        # Booking
        get_or_create_booking(
            db=db,
            hovn_booking_ref=hovn_booking_ref,
            student=student,
            session=session,
            order=order,
            status="active",
        )

        db.commit()
        print(f"[PIPELINE] Successfully upserted booking {hovn_booking_ref} into DB.")
    except SQLAlchemyError as e:
        db.rollback()
        print("[PIPELINE] Database error:", e)
        raise
    except Exception as e:
        db.rollback()
        print("[PIPELINE] Error:", e)
        raise
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python normalized_pipeline.py <BOOKING_REF>")
        sys.exit(1)

    booking_ref = sys.argv[1].strip()
    print(f"[PIPELINE] Processing booking ref: {booking_ref}")
    process_booking_ref(booking_ref)


if __name__ == "__main__":
    main()