# n.e. thing training — Hovn Admin & ARC Certificate Sync System

A full-stack admin dashboard powering student management, Red Cross certificate syncing, Hovn pipeline ingestion, and automated email-driven verification.

This project is **Version 1.0** of the complete system.

---

## 📦 Tech Stack

### **Backend**
- FastAPI (Python 3.11+)
- SQLAlchemy ORM
- PostgreSQL
- Uvicorn ASGI server
- Zoho SMTP (email)
- Internal modules:
  - `redcross.py` — ARC certificate scraper  
  - `hovn_scraper.py` — booking/session scraping  
  - `normalize.py` — enterprise-grade normalization  
  - `db_pipeline.py` — persistence engine  

---

### **Frontend**
- React + Vite  
- TailwindCSS  
- React Router  
- Airtable-style grid-based admin UI  

---

## 🚀 Features

### 🎓 **Student Management**
- View / search all students  
- Full editable student profiles  
- Update email, name, phone, Hovn ID directly from GUI  
- Automatic ARC certificate lookup & DB caching  
- Defensive parsing for inconsistent ARC data  
- Real-time cert sync button per student  

---

### 🧾 **Certification System**
- ARC certificate scraping (real Red Cross backend)  
- DB-first caching:  
  - First lookup → scrape ARC → insert  
  - Future lookups → read from DB instantly  
- Smart expiry handling:  
  - If no expiry provided → assume 2 years  
  - If course contains “Eligible for Skills Session within 90 days” → expiry = 90 days  
- Cert color states:
  - > 90 days left → **green**  
  - < 90 days left → **yellow**  
  - < 90 days expired → **red**  
  - > 90 days expired → **blue**  
- Instructor + provider parsing  
- Issuer_org normalization for Foss, n.e. thing training, etc.  

---

### 💼 **Hovn Integration**
- Scrape booking + session  
- Normalize entire payload  
- Persist to DB  
- Automated migration tool for historical students  
- Ability to load 1 ref or hundreds from a `.txt` file  

---

### ✉️ **Email Automation**
- Internal new-student cert sync email  
- External certificate lookup workflow:
  - Send email → system parses email → auto replies with report  
- Safe mode (`store=false`) for external checks  
- Professional HTML formatting  
- Internal mode → short/no-frills plaintext  

---

## 🔌 API Documentation (Swagger-Style)

### **GET /api/health**
Returns server status.  
`{ "status": "ok" }`

---

### **GET /api/students**
List students (100 max).  

---

### **PATCH /api/students/{id}**
Update student fields.  
```json
{
  "first_name": "New",
  "last_name": "Last",
  "email": "updated@example.com"
}
```

---

### **POST /api/certs/lookup?email=...**
DB-first certificate lookup.  

---

### **POST /api/certs/check-email**
Safe certificate lookup (never stored).  

---

### **POST /api/email-webhook/cert-lookup**
Zoho inbound email → certificate report workflow.  

---

### **GET /api/certs/all**
Returns all stored certificates.  

---

### **POST /api/migrate/bookings**
Silent ARC-sync for existing Hovn bookings.  

---

## 🗄 Database Schema Overview

### **Student**
```
id  
first_name  
last_name  
email  
phone_e164  
hovn_student_id  
```

### **Certificate**
```
cert_id (ARC unique key)  
student_id  
course_name  
course_code  
format  
issue_date  
expiry_date  
issuer_org  
instructor_name  
added_at  
```

### **Booking / Session / Order**  
Normalized Hovn data.

---

## 🛠 Deployment Guide

### **1. Install environment**
- Python 3.11+
- PostgreSQL
- Node 20+

### **2. Backend setup**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### **3. Frontend build**
```bash
cd frontend
npm install
npm run build
```

### **4. Environment variables**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/hovn
SMTP_USER=notifications@nethingtraining.com
SMTP_PASS=yourpassword
SMTP_FROM=noreply@nethingtraining.com
INTERNAL_TO=eli.neirick@gmail.com
```

### **5. Zoho Inbound Email (Deluge)**
Example:
```
post = invokeurl
[
    url: "https://pipeline.nethingtraining.com/api/certs/check-email"
    type: POST
    parameters: {
        "email": target_email,
        "store": "false"
    }
];
```

---

## 🧪 Testing Suite

### **PowerShell tests**
```
# Health
curl http://127.0.0.1:8000/api/health

# Safe cert check
curl.exe -X POST -H "Content-Type: application/json" -d "{\\"email\\": \\"test@gmail.com\\"}" http://127.0.0.1:8000/api/certs/check-email
```

### **Postman Collection**
- Import endpoints manually or use:
  - GET students
  - PATCH students/{id}
  - POST certs/lookup
  - POST certs/check-email
  - POST email-webhook/cert-lookup
  - GET certs/all

---

# 🧭 What’s Next in Version 2 (Roadmap)

### ✔️ **1. Full multi-tenant instructor accounts**  
Instructors see only their students + certs.

### ✔️ **2. ARC PDF certificate generation**  
Ability to produce branded downloadable PDFs.

### ✔️ **3. Automated skill session reminders**  
Email/SMS reminders 30, 60, 90 days.

### ✔️ **4. Foss Swim School integration**  
Auto-ingest Foss rosters + unify with ARC.

### ✔️ **5. Bulk upload student tool**  
CSV/Excel import with validation.

### ✔️ **6. Dedicated /students/search API**  
Instant search index.

### ✔️ **7. Shift from scraper → official ARC API** *(if available)*
