import re
import json
from datetime import datetime
import phonenumbers
from zoneinfo import ZoneInfo

CENTRAL_TZ = "America/Chicago"


def _clean_money(value: str | None) -> int | None:
    if not value:
        return None
    v = value.replace("$", "").replace(",", "").strip()
    try:
        return int(float(v) * 100)
    except:
        return None


def _parse_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    try:
        num = phonenumbers.parse(phone, "US")
        return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    except:
        return phone


def _split_name(full_name: str | None):
    if not full_name:
        return None, None
    parts = full_name.split()
    if len(parts) == 1:
        return parts[0], None
    return parts[0], " ".join(parts[1:])


def _normalize_timestamp(iso_str: str | None):
    """
    Return (utc_iso, central_iso)
    """
    if not iso_str:
        return None, None

    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    utc = dt.astimezone(ZoneInfo("UTC")).isoformat()
    central = dt.astimezone(ZoneInfo(CENTRAL_TZ)).isoformat()
    return utc, central


def _parse_address(raw: str | None):
    """
    Expected:
        "2331 Willow Rd Glenview, IL 60025"
    Newlines already removed in scraper.
    """
    if not raw:
        return None, None, None, None

    # Example: "2331 Willow Rd Glenview, IL 60025"
    # Try splitting before city:
    m = re.match(r"(.+?)\s+([A-Za-z ]+),\s*([A-Z]{2})\s+(\d{5})", raw)
    if not m:
        return raw, None, None, None

    street = m.group(1).strip()
    city = m.group(2).strip()
    state = m.group(3).strip()
    zipcode = m.group(4).strip()
    return street, city, state, zipcode


def extract_last_path(url_or_path: str | None):
    if not url_or_path:
        return None
    return url_or_path.rstrip("/").split("/")[-1]


def normalize_full_bundle(bundle: dict):
    bk = bundle["booking"]
    ss = bundle["session"]

    # -------- Student --------
    fn, ln = _split_name(bk["student_name"])
    phone = _parse_phone(bk["student_phone"])

    # -------- Order --------
    order_utc, order_central = _normalize_timestamp(bk["order_datetime"])
    total_cents = _clean_money(bk["order_total"])

    # -------- Address --------
    street, city, state, zipcode = _parse_address(bk["session_address"])

    # -------- Session --------
    sess_id = extract_last_path(ss["session_id_text"])
    sess_utc, sess_central = _normalize_timestamp(ss["session_date_iso"])

    normalized = {
        "booking_ref": bundle["booking_ref"],
        "booking_url": bundle["booking_url"],

        "student": {
            "student_id": extract_last_path(bk["student_id"]),
            "first_name": fn,
            "last_name": ln,
            "email": bk["student_email"],
            "phone_e164": phone,
        },

        "order": {
            "order_id": extract_last_path(bk["order_id"]),
            "order_number": bk["order_number"],
            "status": bk["order_status"],
            "order_datetime_utc": order_utc,
            "order_datetime_central": order_central,
            "total_cents": total_cents,
            "stripe_order_number": None,
        },

        "session": {
            "session_id": sess_id,
            "course_name": ss["course_name"],
            "format": ss["format"],
            "agency": ss["agency"],
            "start_utc": sess_utc,
            "start_central": sess_central,
            "location_name": ss["location_name"],
            "location_street": street,
            "location_city": city,
            "location_state": state,
            "location_zip": zipcode,
            "instructor_name": ss["instructor_name"],
        },
    }

    return normalized