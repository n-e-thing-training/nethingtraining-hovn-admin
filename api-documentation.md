# Hovn Admin & ARC Certificate Sync System — Full API Reference

## Overview
This document contains the complete API reference for the n.e. thing training admin backend (Version 1.0).  
All endpoints are served under the FastAPI application and use JSON for request and response bodies unless otherwise stated.

---

# 🔧 Base URL

For local development:
```
http://127.0.0.1:8000
```

---

# 📘 Authentication
**None required** (internal-only system).  
Reverse proxy authentication can be added later (see roadmap).

---

# 📂 Endpoints

---

# 🏥 Health Check

### **GET /api/health**
Returns API availability.

**Response**
```json
{ "status": "ok" }
```

---

# 🎓 Students

---

## **GET /api/students**
Returns a list of all students.

**Query Params**
- `limit` — default 100

**Response**
```json
[
  {
    "id": 1,
    "hovn_student_id": "stu_ABC123",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+12223334444"
  }
]
```

---

## **PATCH /api/students/{id}**
Updates a student's information.

**Request Body**
```json
{
  "first_name": "Updated",
  "last_name": "Name",
  "email": "new@example.com",
  "phone": "+15556667777",
  "hovn_student_id": "stu_99999"
}
```

**Response**
```json
{ "status": "ok", "student_id": 3 }
```

---

## **POST /api/students/create**
Creates a new student, performs ARC scrape, stores certs, and sends internal summary email.

**Request Body**
```json
{
  "hovn_student_id": "stu_ABC123",
  "first_name": "John",
  "last_name": "Doe",
  "email": "student@example.com",
  "phone": "+12223334444"
}
```

**Response**
```json
{ "status": "ok", "student_id": 7 }
```

---

## **POST /api/students/migrate**
Used when bulk-importing students from historical bookings.  
Runs ARC scrape but **sends no emails**.

**Request Body**
```json
{
  "booking_refs": ["brn_ABC123", "brn_XYZ789"]
}
```

**Response**
```json
{
  "status": "ok",
  "results": [
    { "student_id": 17, "email": "x@example.com" }
  ]
}
```

---

# 🧾 Bookings

## **GET /api/bookings**
List all bookings in DB.

**Response**
```json
[
  {
    "id": 1,
    "hovn_booking_ref": "brn_ABC123",
    "student_id": 3,
    "order_id": 2,
    "session_id": 5
  }
]
```

---

# 🛒 Orders

## **GET /api/orders**
List all orders in DB.

---

# 🗓 Sessions

## **GET /api/sessions**
List all session records.

---

# 🪪 Certificates

---

## **POST /api/certs/lookup?email=EMAIL**
DB-first search:
- If student exists + certs exist → return cached DB certs  
- If student exists + no certs → scrape & store  
- If no student → scrape but **do NOT store**

**Response**
```json
[
  {
    "cert_id": "01XYZ",
    "course_name": "CPR/AED",
    "format": "Blended",
    "issuer_org": "n.e. thing training",
    "issue_date": "01/01/2023",
    "expiry_date": "01/01/2025",
    "student_id": 3,
    "student_name": "John Doe"
  }
]
```

---

## **GET /api/certs/all**
Return all stored certificates, joined with student.

---

## **POST /api/certs/email-check**
Always scrape ARC → never store.  
Used for external API requests (e.g., Zoho / Deluge).

**Request**
```json
{ "email": "test@example.com" }
```

**Response**
```json
{
  "email": "test@example.com",
  "count": 2,
  "certs": [...]
}
```

---

## **POST /api/certs/check-email**
Same as above, but normalized for emailer.

---

# 📬 Email Webhooks

---

## **POST /api/email-webhook/cert-lookup**
Used by inbound email system.

### Behavior:
- Extract email from subject/body  
- Scrape ARC (store=false)  
- Internal sender → all certs  
- External sender → only n.e. thing training certs  
- Auto-email results back to requester  

**Request Example**
```json
{
  "from": "boss@nethingtraining.com",
  "subject": "Check john@example.com",
  "text": "Please lookup"
}
```

---

# 🧰 Hovn Pipeline

---

## **POST /api/migrate/bookings**
Backfills all students + certs from a batch of Hovn booking refs.

---

# 🕸 Static File Serving

```
GET /             → React index.html
GET /dashboard    → React index.html
GET /assets/*     → Vite build assets
/* (fallback)     → React index.html
```

---

# 🔐 CORS

Enabled for all origins during V1 development.

---

# 🧪 Suggested Test Suite

### Health
```
curl http://127.0.0.1:8000/api/health
```

### Cert Lookup (DB-first)
```
curl -X POST "http://127.0.0.1:8000/api/certs/lookup?email=test@example.com"
```

### External Safe Lookup
```
curl -X POST -H "Content-Type: application/json" \
  -d '{ "email": "test@example.com" }' \
  http://127.0.0.1:8000/api/certs/check-email
```

### Webhook Simulation
```
curl -X POST -H "Content-Type: application/json" \
  -d '{ "from": "eli@nethingtraining.com", "subject": "Check test@example.com" }' \
  http://127.0.0.1:8000/api/email-webhook/cert-lookup
```

---

# 📌 Notes

- ARC cert IDs are globally unique → used as primary business key.
- Expiry date is defensively parsed and, if missing, assumed 2 years after issue.
- "Eligible for Skills Session within 90 days" → 90‑day expiry override.
- UI computes color-coded badges using days-to-expiry.

---

# 🛣 Roadmap (Version 2)
- OAuth or internal login system
- Role-based permissions (Guard / Instructor / Admin)
- Direct Hovn API (if they release one)
- Multi-instructor session attendance/LMS
- Full cert PDF auto-parsing + extraction
- Reconciliation dashboard (ARC vs DB vs Hovn)
- Public cert verification portal
- Offline-capable instructor check-in app
- Dedicated "Audit Log" database table
