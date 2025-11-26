# emailer.py
import os
import smtplib
from email.message import EmailMessage
from email.mime.text import MIMEText
from typing import List, Dict, Any

# ---------------------------------------------------------
# SMTP CONFIG (Zoho Mail)
# ---------------------------------------------------------
SMTP_HOST = "smtppro.zoho.com"
SMTP_PORT = 465  # SSL PORT
SMTP_USER = os.getenv("SMTP_USERNAME")          # notifications@nethingtraining.com
SMTP_PASS = os.getenv("SMTP_PASSWORD")          # App password

FROM_ADDR = os.getenv("MAIL_FROM", "noreply@nethingtraining.com")
INTERNAL_TO = os.getenv("INTERNAL_TO", "eli.neirick@gmail.com")


# ---------------------------------------------------------
# Base email sender — ALWAYS SSL (Zoho standard)
# ---------------------------------------------------------
def _send_email(to_addr: str, subject: str, html_body: str, text_body: str = None):
    msg = EmailMessage()
    msg["From"] = FROM_ADDR
    msg["To"] = to_addr
    msg["Subject"] = subject

    msg.set_content(text_body or "See HTML version.")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


# ---------------------------------------------------------
# Utility: Convert cert list → HTML table
# ---------------------------------------------------------
def _cert_table_html(certs: List[Dict[str, Any]]) -> str:
    if not certs:
        return "<p>No certifications found.</p>"

    rows = ""
    for c in certs:
        rows += f"""
        <tr>
            <td>{c.get("course_name", "—")}</td>
            <td>{c.get("issuer_org", "—")}</td>
            <td>{c.get("format", "—")}</td>
            <td>{c.get("issue_date", "—")}</td>
            <td>{c.get("expiry_date", "—")}</td>
        </tr>
        """

    return f"""
    <table border="1" cellpadding="6" cellspacing="0"
           style="border-collapse: collapse; font-size: 13px;">
        <thead style="background: #f0f0f0;">
            <tr>
                <th>Course</th>
                <th>Provider</th>
                <th>Format</th>
                <th>Issued</th>
                <th>Expires</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    """


# =========================================================
#  A) INTERNAL — Cert sync after student creation
# =========================================================
def send_cert_report(student, certs: List[Dict[str, Any]]):
    subject = f"[HOVN] Cert sync for {student.first_name} {student.last_name}"

    html = f"""
    <h2>New Student Created</h2>

    <p>
        <strong>Name:</strong> {student.first_name} {student.last_name}<br>
        <strong>Email:</strong> {student.email}
    </p>

    <h3>Certifications imported:</h3>
    {_cert_table_html(certs)}
    """

    _send_email(INTERNAL_TO, subject, html)


# =========================================================
#  B) ONE-OFF CERT LOOKUP (external, store=false)
# =========================================================
def send_one_off_lookup(to_email: str, certs: List[Dict[str, Any]]):
    subject = "Your American Red Cross Certification Report"

    html = f"""
    <p>Hello,</p>

    <p>You recently requested a verification of your American Red Cross certifications.
       Below is a complete list associated with your email.</p>

    {_cert_table_html(certs)}

    <p>If anything is incorrect, reply to this email and our team will assist.</p>

    <p>Best regards,<br>
       <strong>n.e. thing training</strong><br>
       Certification Support</p>
    """

    _send_email(to_email, subject, html)


# =========================================================
#  C) INTERNAL — Migration log email (no student emails)
# =========================================================
def send_migration_notice(ref: str, student, certs: List[Dict[str, Any]]):
    subject = f"[HOVN Migration] Imported student from {ref}"

    html = f"""
    <h2>Imported Student (Migration)</h2>

    <p><strong>Booking Ref:</strong> {ref}</p>
    <p>
        <strong>Name:</strong> {student.first_name} {student.last_name}<br>
        <strong>Email:</strong> {student.email}
    </p>

    <h3>Certifications scraped:</h3>
    {_cert_table_html(certs)}

    <p>This was an automated import. No customer email was sent.</p>
    """

    _send_email(INTERNAL_TO, subject, html)


# =========================================================
#  D) CERT LOOKUP REPLY (INBOUND-WEBHOOK HANDLER)
#     - Internal: short/no-frills
#     - External: formatted & professional
# =========================================================
def send_cert_lookup_reply(to_email: str, subject: str, body: str):
    """
    Sends a plaintext email (used by webhook handler)
    """
    msg = MIMEText(body)
    msg["From"] = FROM_ADDR
    msg["To"] = to_email
    msg["Subject"] = subject

    with smtplib.SMTP_SSL(SMTP_HOST, 465) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(FROM_ADDR, [to_email], msg.as_string())