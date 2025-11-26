"""
hovn_next_parser.py

Parser for Hovn admin Next.js Flight HTML snapshots.
Given a booking reference (e.g. "brn_YZWADB") and the HTML of a session
or order page (which includes a "bookings" array inside the
self.__next_f.push payload), this extracts:

- booking
- student
- session (basic info)
- invoice (order)

and returns a single normalized dict.
"""

import json
import re
import sys
from typing import Any, Dict, List, Optional


# ------------------------------
# Low-level helpers
# ------------------------------

def _clean_hovn_json(raw: str) -> str:
    """
    Make the Hovn Next Flight JSON parsable by the stdlib json module.

    Things we fix:
    - $D2025-11-07T...   ->  2025-11-07T...
    - $undefined         ->  null
    - Escaped ampersands (\u0026) remain fine for json
    """
    s = raw

    # Replace $D-prefixed ISO timestamps like "$D2025-11-07T15:41:44.284Z"
    # with just "2025-11-07T15:41:44.284Z"
    s = re.sub(r'"(\w+)":"\$D([^"]+)"', r'"\1":"\2"', s)

    # Replace "$D" if it appears without a field-name pattern,
    # just in case (e.g. inside nested structures)
    s = s.replace('"$D', '"')

    # Replace explicit "$undefined" tokens with null
    # Cases:
    #   "foo":"$undefined"
    #   "foo":$undefined
    s = s.replace('"$undefined"', 'null')
    s = s.replace('$undefined', 'null')

    return s


def _extract_array_block(html: str, key: str) -> str:
    """
    Extract the JSON array assigned to the given key, e.g. '"bookings":[' ... ']'.

    - key is the JSON key name WITHOUT quotes, like 'bookings'
    - Returns the raw array string including [ and ] (still in Hovn format).
    """
    marker = f'"{key}":['
    start_key = html.find(marker)
    if start_key == -1:
        raise RuntimeError(f'Could not find "{marker}" in HTML.')

    # First '[' after the key
    start_idx = html.index('[', start_key)

    depth = 0
    in_string = False
    escaped = False
    end_idx: Optional[int] = None

    for i in range(start_idx, len(html)):
        ch = html[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '[':
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

    if end_idx is None:
        raise RuntimeError(f'Could not find matching ] for "{key}" array.')

    return html[start_idx:end_idx + 1]


def _load_html_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ------------------------------
# Core parsing logic
# ------------------------------

def _parse_bookings_array(html: str) -> List[Dict[str, Any]]:
    """
    Extract and parse the "bookings" array from a Hovn admin HTML page.
    Returns a list of booking dicts.
    """
    raw_block = _extract_array_block(html, "bookings")
    cleaned = _clean_hovn_json(raw_block)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to decode bookings JSON: {e}\nSnippet: {cleaned[:500]}") from e

    if not isinstance(data, list):
        raise RuntimeError(f'Expected "bookings" to parse as list, got {type(data)}')

    return data


def _parse_classes_array(html: str) -> List[Dict[str, Any]]:
    """
    Try to extract and parse a "classes" array (used for segments & locations)
    from the same HTML. If not found, returns [].
    """
    try:
        raw_block = _extract_array_block(html, "classes")
    except RuntimeError:
        return []

    cleaned = _clean_hovn_json(raw_block)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Not critical for basic booking parsing
        return []

    if isinstance(data, list):
        return data
    return []


def _find_session_segment_for_booking(
    classes: List[Dict[str, Any]],
    course_session_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Given the 'classes' array and the booking's courseSessionId,
    pick the most relevant in-person class segment (if any).

    We prefer the segment where:
      - class["courseSessionId"] == course_session_id
      - modality == "INSTRUCTOR_LED" if present
    """
    # First, matching ID
    candidates = [c for c in classes if c.get("courseSessionId") == course_session_id]
    if not candidates:
        return None

    # Prefer instructor-led if present
    for c in candidates:
        if c.get("modality") == "INSTRUCTOR_LED":
            return c

    # Otherwise just return the first
    return candidates[0]


def _normalize_booking_bundle(
    booking: Dict[str, Any],
    class_segment: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a single normalized dict from a raw Hovn booking dict and
    an optional class / segment dict.
    """

    student = booking.get("student") or {}
    course_order_item = booking.get("courseOrderItem") or {}
    order = course_order_item.get("order") or {}

    # Basic booking fields
    booking_norm = {
        "hovn_booking_id": booking.get("id"),
        "hovn_booking_cuid": booking.get("cuid"),
        "booking_ref": booking.get("referenceNumber"),
        "course_order_item_id": booking.get("courseOrderItemId"),
        "account_id": booking.get("accountId"),
        "booked_by_account_id": booking.get("bookedByAccountId"),
        "course_session_id": booking.get("courseSessionId"),
        "is_ready_for_certificate": booking.get("isReadyForCertificate"),
        "verified_at": booking.get("verifiedAt"),
        "created_at": booking.get("createdAt"),
        "updated_at": booking.get("updatedAt"),
        "canceled_at": booking.get("canceledAt"),
        "status": "canceled" if booking.get("canceledAt") else "active",
    }

    # Student
    student_norm = {
        "hovn_student_id": student.get("id"),
        "account_id": student.get("accountId"),
        "first_name": student.get("firstName"),
        "last_name": student.get("lastName"),
        "email": student.get("email"),
        "phone": student.get("phoneNumber"),
        "service_provider_id": student.get("serviceProviderId"),
        "created_at": student.get("createdAt"),
        "updated_at": student.get("updatedAt"),
    }

    # Session (from class_segment if available)
    session_norm: Dict[str, Any] = {
        "course_session_id": booking.get("courseSessionId"),
        "class_segment_id": None,
        "name": None,
        "starts_at": None,
        "ends_at": None,
        "modality": None,
        "location": None,          # full nested location dict if available
        "location_label": None,
        "address": None,
        "city": None,
        "state": None,
        "postal_code": None,
        "time_zone": None,
    }

    if class_segment:
        session_norm["class_segment_id"] = class_segment.get("id")
        session_norm["name"] = class_segment.get("name")
        session_norm["starts_at"] = class_segment.get("startsAt")
        session_norm["ends_at"] = class_segment.get("endsAt")
        session_norm["modality"] = class_segment.get("modality")

        location = class_segment.get("location") or {}
        session_norm["location"] = location or None
        session_norm["location_label"] = location.get("label")
        session_norm["address"] = location.get("formattedAddress") or location.get("address1")
        session_norm["city"] = location.get("city")
        session_norm["state"] = location.get("state")
        session_norm["postal_code"] = location.get("postalCode")
        session_norm["time_zone"] = location.get("timeZone")

    # Invoice / order
    invoice_norm = {
        "hovn_order_id": course_order_item.get("orderId"),
        "order_reference": order.get("referenceNumber"),
        "status": order.get("status"),
        "order_cuid": order.get("cuid"),
        "service_provider_id": order.get("serviceProviderId"),
        "total_price": order.get("totalPrice", course_order_item.get("price")),
        "paid_at": order.get("paidAt"),
        "created_at": order.get("createdAt"),
        "updated_at": order.get("updatedAt"),
    }

    return {
        "booking": booking_norm,
        "student": student_norm,
        "session": session_norm,
        "invoice": invoice_norm,
        # Keep the full raw Hovn booking JSON in case we need details later
        "raw": booking,
    }


# ------------------------------
# Public API
# ------------------------------

def parse_session_html_for_booking(
    html: str,
    booking_ref: str,
) -> Dict[str, Any]:
    """
    Parse a Hovn session/order HTML string, locate the booking
    with the given booking_ref, and return a normalized bundle:

        {
          "booking": {...},
          "student": {...},
          "session": {...},
          "invoice": {...},
          "raw": {...original Hovn booking dict...}
        }

    Raises RuntimeError if the booking cannot be found.
    """
    bookings = _parse_bookings_array(html)
    classes = _parse_classes_array(html)

    target: Optional[Dict[str, Any]] = None
    for b in bookings:
        if b.get("referenceNumber") == booking_ref:
            target = b
            break

    if target is None:
        raise RuntimeError(f'No booking with referenceNumber="{booking_ref}" found in bookings array.')

    course_session_id = target.get("courseSessionId")
    class_segment = None
    if course_session_id is not None:
        class_segment = _find_session_segment_for_booking(classes, course_session_id)

    bundle = _normalize_booking_bundle(target, class_segment)
    return bundle


# ------------------------------
# CLI usage (for debugging)
# ------------------------------

def main_cli() -> None:
    if len(sys.argv) < 3:
        print("Usage: python hovn_next_parser.py <BOOKING_REF> <HTML_FILE_PATH>")
        print("Example: python hovn_next_parser.py brn_YZWADB session.html")
        sys.exit(1)

    booking_ref = sys.argv[1]
    html_path = sys.argv[2]

    html = _load_html_from_file(html_path)
    bundle = parse_session_html_for_booking(html, booking_ref)

    # Pretty-print the normalized bundle as JSON
    print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    main_cli()