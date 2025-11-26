# redcross.py
import requests
from bs4 import BeautifulSoup

BASE_URL = (
    "https://www.redcross.org/on/demandware.store/"
    "Sites-RedCross-Site/default/Certificates-SearchCertificates"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.redcross.org/take-a-class/digital-certificate",
    "Origin": "https://www.redcross.org",
    "X-Requested-With": "XMLHttpRequest",
}

def determine_format(course_code: str):
    code = (course_code or "").upper()
    if "BL" in code:
        return "Blended"
    if "OL" in code or code.startswith("ROC"):
        return "Online"
    return "Instructor-Led"


def scrape_certs_for_email(email: str):
    params = {
        "email": email,
        "format": "ajax"
    }

    resp = requests.get(BASE_URL, params=params, headers=HEADERS)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    inputs = soup.select("input.certpdfdownload")

    certs = []

    for tag in inputs:
        raw = tag.get("value", "")
        parts = raw.split("|")

        # Red Cross format indexes:
        # 0  id-XXXXXX
        # 1  TS/walletpdftemplate
        # 2  cert PDF URL
        # 3  Org / Provider
        # 4  AAS number
        # 5  Course name
        # 6  Course code
        # 7  ?
        # 8  Format (text)
        # 9  Active/Expired
        # 10 "Certifications"
        # 11 Student name
        # 12 Provider / Org
        # 13 Issue date
        # 14 Expiry date
        # 15 Validity length
        # 16 Instructor name
        # 17 Cert number duplicated

        course_code = parts[6] if len(parts) > 6 else ""
        format_label = determine_format(course_code)

        certs.append({
            "cert_id": parts[0].replace("id-", "") if len(parts) > 0 else "",
            "course_name": parts[5] if len(parts) > 5 else "",
            "course_code": course_code,
            "format": format_label,
            "issue_date": parts[13] if len(parts) > 13 else "",
            "expiry_date": parts[14] if len(parts) > 14 else "",
            "agency_org_name": parts[3] if len(parts) > 3 else "",
            "instructor_name": parts[16] if len(parts) > 16 else "",
        })

    return certs