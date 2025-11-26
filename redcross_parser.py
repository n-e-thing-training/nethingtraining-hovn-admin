# redcross_parser.py
from bs4 import BeautifulSoup
import re
from datetime import datetime

def parse_date(date_str: str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str.strip(), "%b %d, %Y").date()
    except:
        return None

def extract_cert_blocks(html: str):
    soup = BeautifulSoup(html, "html.parser")

    # Each full certificate row is inside:
    # <div class="certificate-heading-list result-certificate-dt align-layout">
    return soup.select("div.certificate-heading-list.result-certificate-dt.align-layout")

def parse_cert_block(block):
    """
    Given one certificate block (one cert),
    extract: id, course_name, issue_date, expire_date
    """
    # CERT ID
    hidden = block.select_one("input.certid")
    cert_id = hidden["value"].replace("id-", "") if hidden else None

    # COURSE NAME (text in <div class="section-header col-class">)
    course_div = block.select_one("div.col-class")
    course_name = course_div.text.strip() if course_div else None

    # ISSUE + EXPIRE DATES
    date_div = block.select_one("div.col-date")
    issue_date = None
    if date_div:
        issue_date = parse_date(date_div.text.strip())

    # In the hidden field for PDF info
    expiration = None
    pdf_data = block.select_one("input.certpdfdownload")
    if pdf_data:
        parts = pdf_data["value"].split("|")
        # Expire date is always position -2 in the value chunk
        try:
            exp_raw = parts[-2]
            expiration = parse_date(exp_raw)
        except:
            expiration = None

    return {
        "cert_id": cert_id,
        "course_name": course_name,
        "issue_date": issue_date,
        "expire_date": expiration,
    }

def parse_all_certs(html: str):
    blocks = extract_cert_blocks(html)
    certs = []

    for block in blocks:
        item = parse_cert_block(block)
        if item["cert_id"]:
            certs.append(item)

    return certs