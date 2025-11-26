import os
import sys
import json
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

EDGE_CDP_URL = os.getenv("EDGE_CDP_URL", "http://127.0.0.1:9222")

BOOKING_BASE_URL = "https://www.hovn.app/admin/ne-thing-training/bookings/"
SESSION_BASE_URL = "https://www.hovn.app"

# ---------- XPATHS FROM YOU ----------

BOOKING_XPATHS = {
    "bookingRef": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[1]/div[1]/div[1]/span[2]",
    "name": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[1]/div[1]/div[1]/span[2]",
    "email": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/span[2]/a[1]",
    "phone": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[3]/div[1]/div[1]/a[1]",
    "studentID": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[1]/div[1]/div[1]/div[2]/div[1]/div[3]/a[1]",
    "orderNum": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/div[1]/div[1]/span[2]",
    "orderStatus": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/div[1]/div[4]/div[1]/div[1]",
    "orderDate": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/div[1]/div[3]/time[1]",
    "orderTotal": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/div[3]/div[1]/div[1]/span[2]",
    "sessionAddress": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[3]/div[1]/div[1]/div[1]/div[1]/div[3]/address[1]/div[1]/div[1]/p[1]",
    "orderID": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[4]/div[2]/div[1]/div[2]/a[1]",
}

# Session link on booking page (that you gave)
SESSION_LINK_XPATH = r"/html/body/div[2]/main/div/div/div/div/div/div/div[4]/div[3]/div[1]/div[1]/div/div/a"

SESSION_XPATHS = {
    "courseName": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/span[1]",
    "format": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/span[2]",
    "agency": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/span[1]",
    "date": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/p[1]/time[1]",
    "time": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/p[2]/span[1]/time[1]",
    "locationName": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/p[3]/span[1]",
    "instructor": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[1]/div[2]/div[1]/div[1]/span[1]",
    "sessionID": r"/html[1]/body[1]/div[2]/main[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[2]/div[1]/div[2]/span[1]/span[1]",
}


def _get_text(page, xpath: str) -> str | None:
    try:
        el = page.locator(f"xpath={xpath}")
        el.wait_for(timeout=15000)
        return el.inner_text().strip()
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None


def _get_attr(page, xpath: str, attr: str) -> str | None:
    try:
        el = page.locator(f"xpath={xpath}")
        el.wait_for(timeout=15000)
        val = el.get_attribute(attr)
        if val is None:
            return None
        return val.strip()
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None


def _last_path_segment(href: str | None) -> str | None:
    if not href:
        return None
    # works for both absolute and relative URLs
    return href.rstrip("/").split("/")[-1]


def _normalize_address(raw: str | None) -> str | None:
    if raw is None:
        return None
    # collapse newlines / multiple spaces to a single space
    return " ".join(raw.split())


def _clean_instructor_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    # strip things like "\nLead" etc. by taking the first line
    return raw.split("\n", 1)[0].strip()


def _extract_booking(page) -> dict:
    data: dict[str, str | None] = {}

    data["booking_ref"] = _get_text(page, BOOKING_XPATHS["bookingRef"])
    data["student_name"] = _get_text(page, BOOKING_XPATHS["name"])

    # email from href or visible text
    email_href = _get_attr(page, BOOKING_XPATHS["email"], "href")
    if email_href and email_href.lower().startswith("mailto:"):
        data["student_email"] = email_href.split(":", 1)[1]
    else:
        data["student_email"] = _get_text(page, BOOKING_XPATHS["email"])

    # phone from tel: href or text
    phone_href = _get_attr(page, BOOKING_XPATHS["phone"], "href")
    if phone_href and phone_href.lower().startswith("tel:"):
        data["student_phone"] = phone_href.split(":", 1)[1]
    else:
        data["student_phone"] = _get_text(page, BOOKING_XPATHS["phone"])

    # student id: only last segment, no text key
    student_href = _get_attr(page, BOOKING_XPATHS["studentID"], "href")
    data["student_id"] = _last_path_segment(student_href)

    data["order_number"] = _get_text(page, BOOKING_XPATHS["orderNum"])
    data["order_status"] = _get_text(page, BOOKING_XPATHS["orderStatus"])

    # use datetime attribute for full ISO timestamp
    data["order_datetime"] = _get_attr(page, BOOKING_XPATHS["orderDate"], "datetime")

    data["order_total"] = _get_text(page, BOOKING_XPATHS["orderTotal"])

    # normalize address to single line
    session_address_raw = _get_text(page, BOOKING_XPATHS["sessionAddress"])
    data["session_address"] = _normalize_address(session_address_raw)

    # order_id: only last segment, no *_text key
    order_id_href = _get_attr(page, BOOKING_XPATHS["orderID"], "href")
    data["order_id"] = _last_path_segment(order_id_href)

    # session page link
    session_link = _get_attr(page, SESSION_LINK_XPATH, "href")
    if session_link:
        if session_link.startswith("http"):
            data["session_url"] = session_link
        else:
            data["session_url"] = urljoin(SESSION_BASE_URL, session_link)
    else:
        data["session_url"] = None

    return data


def _extract_session(page) -> dict:
    data: dict[str, str | None] = {}

    data["course_name"] = _get_text(page, SESSION_XPATHS["courseName"])
    data["format"] = _get_text(page, SESSION_XPATHS["format"])
    data["agency"] = _get_text(page, SESSION_XPATHS["agency"])

    # only keep one ISO field (using the date <time> element's datetime)
    data["session_date_iso"] = _get_attr(page, SESSION_XPATHS["date"], "datetime")

    data["location_name"] = _get_text(page, SESSION_XPATHS["locationName"])
    data["instructor_name"] = _clean_instructor_name(
        _get_text(page, SESSION_XPATHS["instructor"])
    )
    data["session_id_text"] = _get_text(page, SESSION_XPATHS["sessionID"])

    return data


def attach_to_edge(playwright):
    """
    Attach ONLY to an already-running Edge with --remote-debugging-port=9222.
    Does NOT launch Edge.
    """
    print("[SCRAPER] Attaching to existing Edge with CDP...")
    try:
        browser = playwright.chromium.connect_over_cdp(EDGE_CDP_URL)
    except Exception as e:
        print("[SCRAPER] ERROR: Could not connect to Edge via CDP.")
        print(f"[SCRAPER]  • URL tried: {EDGE_CDP_URL}")
        print("[SCRAPER]  • Make sure Edge is running with:")
        print('    msedge.exe --remote-debugging-port=9222 --profile-directory="Profile 1"')
        raise e

    contexts = browser.contexts
    if not contexts:
        context = browser.new_context()
    else:
        context = contexts[0]

    page = context.new_page()
    return browser, context, page


def scrape_booking_and_session(booking_ref: str) -> dict:
    with sync_playwright() as p:
        browser, context, page = attach_to_edge(p)

        try:
            booking_url = BOOKING_BASE_URL + booking_ref
            print(f"[SCRAPER] Opening booking page: {booking_url}")
            page.goto(booking_url, wait_until="networkidle", timeout=60000)

            booking_data = _extract_booking(page)

            session_url = booking_data.get("session_url")
            session_data = None
            if session_url:
                print(f"[SCRAPER] Opening session page: {session_url}")
                page.goto(session_url, wait_until="networkidle", timeout=60000)
                session_data = _extract_session(page)
            else:
                print("[SCRAPER] WARNING: No session_url found on booking page.")

            result = {
                "booking_ref": booking_ref,
                "booking_url": booking_url,
                "booking": booking_data,
                "session": session_data,
            }

            print(json.dumps(result, indent=2))
            return result
        finally:
            # Do NOT close browser; it's your real profile window
            try:
                context.close()
            except Exception:
                pass
            try:
                browser.close()
            except Exception:
                pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python hovn_scraper.py <BOOKING_REF>")
        sys.exit(1)

    booking_ref = sys.argv[1].strip()
    print(f"[SCRAPER] Processing booking ref: {booking_ref}")
    scrape_booking_and_session(booking_ref)


if __name__ == "__main__":
    main()