import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

from models import (
    Student,
    Order,
    Session,
    Booking,
    Agency,
    Course,
    Location,
    Instructor,
)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# --------------------------------------------------
# Helper: get or create a record
# --------------------------------------------------
def get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance, False

    params = {**filters}
    if defaults:
        params.update(defaults)

    instance = model(**params)
    db.add(instance)
    return instance, True


# --------------------------------------------------
# Main persistence function
# --------------------------------------------------
def persist_full_normalized_bundle(data: dict):
    db = SessionLocal()

    try:
        # ===============================================================
        # STUDENT
        # ===============================================================
        stu = data["student"]
        hovn_student_id = stu["student_id"]

        student, created_student = get_or_create(
            db,
            Student,
            hovn_student_id=hovn_student_id
        )

        student.first_name = stu.get("first_name")
        student.last_name = stu.get("last_name")
        student.email = stu.get("email")
        student.phone_e164 = stu.get("phone_e164")
        student.phone_raw = stu.get("phone_raw")

        # ===============================================================
        # AGENCY
        # ===============================================================
        session_data = data["session"]

        agency_name = session_data["agency"]
        agency, _ = get_or_create(
            db,
            Agency,
            name=agency_name
        )

        # ===============================================================
        # COURSE
        # ===============================================================
        course_name = session_data["course_name"]
        course_format = session_data["format"]

        course, _ = get_or_create(
            db,
            Course,
            name=course_name,
            format=course_format,
            agency_id=agency.id
        )

        # ===============================================================
        # LOCATION
        # ===============================================================
        loc = session_data

        location, _ = get_or_create(
            db,
            Location,
            name=loc["location_name"],
            address_line1=loc.get("location_street"),
            city=loc.get("location_city"),
            state=loc.get("location_state"),
            postal_code=loc.get("location_zip"),
            country_code="US",
        )

        # ===============================================================
        # INSTRUCTOR
        # ===============================================================
        instr_name = session_data["instructor_name"]

        if instr_name:
            first, *rest = instr_name.split(" ")
            last = " ".join(rest) if rest else None
        else:
            first = last = None

        instructor, _ = get_or_create(
            db,
            Instructor,
            full_name=instr_name,
            first_name=first,
            last_name=last,
        )

        # ===============================================================
        # SESSION
        # ===============================================================
        hovn_session_id = session_data["session_id"]

        session_obj, created_sess = get_or_create(
            db,
            Session,
            hovn_session_id=hovn_session_id
        )

        session_obj.course_id = course.id
        session_obj.agency_id = agency.id
        session_obj.location_id = location.id
        session_obj.instructor_id = instructor.id

        session_obj.start_utc = session_data.get("start_utc")
        session_obj.start_local = session_data.get("start_central")
        session_obj.format = session_data.get("format")
        session_obj.hovn_session_url = session_data.get("session_url")

        # ===============================================================
        # ORDER
        # ===============================================================
        order_data = data["order"]
        hovn_order_id = order_data["order_id"]

        order_obj, created_order = get_or_create(
            db,
            Order,
            hovn_order_id=hovn_order_id
        )

        order_obj.hovn_order_number = order_data.get("order_number")
        order_obj.stripe_order_number = order_data.get("stripe_order_number")
        order_obj.student_id = student.id
        order_obj.amount_cents = order_data.get("total_cents")
        order_obj.currency_code = "USD"
        order_obj.status = order_data.get("status")
        order_obj.ordered_at_utc = order_data.get("order_datetime_utc")
        order_obj.ordered_at_local = order_data.get("order_datetime_central")

        # ===============================================================
        # BOOKING
        # ===============================================================
        booking_ref = data["booking_ref"]

        booking_obj, created_booking = get_or_create(
            db,
            Booking,
            hovn_booking_ref=booking_ref
        )

        booking_obj.student_id = student.id
        booking_obj.session_id = session_obj.id
        booking_obj.order_id = order_obj.id
        booking_obj.status = "active"

        # ===============================================================
        # COMMIT
        # ===============================================================
        db.commit()

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()