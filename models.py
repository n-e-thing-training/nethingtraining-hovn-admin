from __future__ import annotations
# models.py
from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from db import Base


# --------------------------- STUDENT ----------------------------
class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hovn_student_id: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    phone_e164: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="student")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="student")
    certificates: Mapped[list["Certificate"]] = relationship("Certificate", back_populates="student")


# --------------------------- AGENCY ----------------------------
class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    courses: Mapped[list["Course"]] = relationship("Course", back_populates="agency")
    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="agency")


# --------------------------- COURSE ----------------------------
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    format: Mapped[str | None] = mapped_column(String(50), nullable=True)

    agency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("agencies.id"), nullable=True)
    agency: Mapped[Agency | None] = relationship("Agency", back_populates="courses")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("name", "format", "agency_id", name="uq_course_name_format_agency"),
    )

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="course")


# --------------------------- LOCATION ----------------------------
class Location(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)

    raw_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("name", "address_line1", "city", "state", "postal_code", name="uq_location"),
    )

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="location")


# --------------------------- INSTRUCTOR ----------------------------
class Instructor(Base):
    __tablename__ = "instructors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    title: Mapped[str | None] = mapped_column(String(100), nullable=True)

    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_e164: Mapped[str | None] = mapped_column(String(32), nullable=True)
    phone_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="instructor")


# --------------------------- SESSION ----------------------------
class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    hovn_session_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    course_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("courses.id"))
    course: Mapped[Course | None] = relationship("Course", back_populates="sessions")

    agency_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("agencies.id"))
    agency: Mapped[Agency | None] = relationship("Agency", back_populates="sessions")

    location_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("locations.id"))
    location: Mapped[Location | None] = relationship("Location", back_populates="sessions")

    instructor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("instructors.id"))
    instructor: Mapped[Instructor | None] = relationship("Instructor", back_populates="sessions")

    start_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_local: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    format: Mapped[str | None] = mapped_column(String(50))

    hovn_session_url: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="session")


# --------------------------- ORDER ----------------------------
class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    hovn_order_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    hovn_order_number: Mapped[str | None] = mapped_column(String(64))

    stripe_order_number: Mapped[str | None] = mapped_column(String(128), index=True)

    student_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id"))
    student: Mapped[Student | None] = relationship("Student", back_populates="orders")

    amount_cents: Mapped[int | None] = mapped_column(Integer)
    currency_code: Mapped[str | None] = mapped_column(String(3))

    status: Mapped[str | None] = mapped_column(String(50))

    ordered_at_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ordered_at_local: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="order")


# --------------------------- BOOKING ----------------------------
class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    hovn_booking_ref: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    student_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("students.id"))
    student: Mapped[Student | None] = relationship("Student", back_populates="bookings")

    session_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sessions.id"))
    session: Mapped[Session | None] = relationship("Session", back_populates="bookings")

    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id"))
    order: Mapped[Order | None] = relationship("Order", back_populates="bookings")

    status: Mapped[str | None] = mapped_column(String(50), default="active")

    is_online_component_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


# --------------------------- CERTIFICATE ----------------------------
class Certificate(Base):
    __tablename__ = "certificates"

    # Use Red Cross cert_id as unique identifier
    cert_id: Mapped[str] = mapped_column(String(32), primary_key=True)

    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    student: Mapped[Student] = relationship("Student", back_populates="certificates")

    course_name: Mapped[str | None] = mapped_column(String(255))
    course_code: Mapped[str | None] = mapped_column(String(64))
    format: Mapped[str | None] = mapped_column(String(32))

    issuer_org: Mapped[str | None] = mapped_column(String(255))
    instructor_name: Mapped[str | None] = mapped_column(String(255))

    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)

    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)