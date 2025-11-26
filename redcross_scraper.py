import requests
from bs4 import BeautifulSoup
from datetime import datetime


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_redcross_certificates(email: str):
    """
    Scrapes the Red Cross certificate lookup page.
    Returns list of dicts containing:
        - cert_id
        - course_name
        - issue_date
        - expire_date
    """

    url = (
        "https://www.redcross.org/on/demandware.store/"
        "Sites-RedCross-Site/default/Certificates-SearchCertificates"
        f"?email={email}&format=ajax"
    )

    r = requests.get(url, headers=HEADERS, timeout=15)

    if r.status_code != 200:
        raise Exception(f"Red Cross HTML fetch failed ({r.status_code})")

    soup = BeautifulSoup(r.text, "html.parser")
    results = []

    # Each cert row is a .certificate-heading-list.result-certificate-dt
    cert_blocks = soup.select(".certificate-heading-list.result-certificate-dt")

    for block in cert_blocks:
        certpdf_input = block.select_one("input.certpdfdownload")

        if not certpdf_input:
            continue

        raw_value = certpdf_input.get("value")
        parts = raw_value.split("|")

        # Parse values
        cert_id = parts[0].replace("id-", "").strip()
        course_name = parts[5].strip()
        issue_date_raw = parts[13].strip()
        expire_date_raw = parts[14].strip()

        # Convert dates
        def try_parse(d):
            try:
                return datetime.strptime(d, "%m/%d/%Y").date()
            except:
                try:
                    return datetime.strptime(d, "%b %d, %Y").date()
                except:
                    return None

        issue_date = try_parse(issue_date_raw)
        expire_date = try_parse(expire_date_raw)

        results.append({
            "cert_id": cert_id,
            "course_name": course_name,
            "issue_date": issue_date,
            "expire_date": expire_date
        })

    return results