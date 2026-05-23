from flask import Flask, request, jsonify, send_from_directory
import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

app = Flask(__name__, static_folder=".")

# ── DATABASE ──────────────────────────────────────────────────
DATABASE_URL = "postgresql://postgres.hnnmtgclwufluuzcypgg:Wellexpo2026@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require&connect_timeout=10"

# Single persistent connection
_conn = None

def get_db():
    global _conn
    try:
        if _conn is None or _conn.closed:
            _conn = psycopg2.connect(DATABASE_URL)
        _conn.isolation_level  # ping to check if alive
    except Exception:
        _conn = psycopg2.connect(DATABASE_URL)
    return _conn

def fetch_all(conn, sql, params=()):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]

def exec_one(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    cur.execute("SELECT lastval()")
    last_id = cur.fetchone()[0]
    cur.close()
    return last_id

def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def safe_int(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

# ── FILE UPLOADS ──────────────────────────────────────────────
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_file(files, field):
    f = files.get(field)
    if f and f.filename:
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{ts}_{f.filename}"
        path = os.path.join(UPLOAD_FOLDER, filename)
        f.save(path)
        size = os.path.getsize(path)
        return filename, f.filename, size, f.content_type
    return "", "", None, None

# ── HELPERS ───────────────────────────────────────────────────

def get_or_create_industry(conn, raw_value):
    if not raw_value:
        return None, None
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id FROM industry_sectors WHERE name = %s", (raw_value,))
    row = cur.fetchone()
    cur.close()
    if row:
        return row["id"], raw_value
    return None, raw_value

def get_or_create_booth_type(conn, raw_value):
    if not raw_value:
        return None, None
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT id FROM booth_types WHERE name = %s", (raw_value,))
    row = cur.fetchone()
    cur.close()
    if row:
        return row["id"], raw_value
    return None, raw_value

def get_exhibition_id(conn):
    rows = fetch_all(conn, "SELECT id FROM exhibitions WHERE is_active = 1 LIMIT 1")
    return rows[0]["id"] if rows else 1

# ── ROUTES ────────────────────────────────────────────────────

# Serve website files (images, videos, css, js) WITHOUT touching the database
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/register.html")
def register():
    return send_from_directory(".", "register.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(".", filename)

# ── DATABASE ROUTES ───────────────────────────────────────────

@app.route("/submit", methods=["POST"])
def submit():
    try:
        data = request.form.to_dict()
        files = request.files
        ts = now_iso()

        conn = get_db()

        industry_id, industry_raw = get_or_create_industry(conn, data.get("industry_sector", ""))
        company_id = exec_one(conn, """
            INSERT INTO companies
              (company_name, brand_name, company_website,
               industry_sector_id, industry_sector_raw,
               year_established, company_description,
               created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            data.get("company_name", ""),
            data.get("brand_name", ""),
            data.get("company_website", ""),
            industry_id, industry_raw,
            data.get("year_established", ""),
            data.get("company_description", ""),
            ts, ts,
        ))

        contact_id = exec_one(conn, """
            INSERT INTO contacts
              (company_id, contact_person_name, email_address,
               phone_number, whatsapp_number, country, city,
               is_primary, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            company_id,
            data.get("contact_person_name", ""),
            data.get("email_address", ""),
            data.get("phone_number", ""),
            data.get("whatsapp_number", ""),
            data.get("country", ""),
            data.get("city", ""),
            1, ts,
        ))

        exhibition_id = get_exhibition_id(conn)
        booth_type_id, booth_type_raw = get_or_create_booth_type(conn, data.get("booth_type", ""))

        reg_id = exec_one(conn, """
            INSERT INTO registrations
              (exhibition_id, company_id, contact_id,
               product_service_category, target_market,
               previous_exhibition_experience,
               booth_type_id, booth_type_raw, booth_size,
               number_of_booth_staff,
               power_requirement, internet_requirement,
               interested_sponsorship, interested_speaking,
               interested_product_launch, special_requirements,
               terms_conditions, consent_marketing,
               status, created_at, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            exhibition_id, company_id, contact_id,
            data.get("product_service_category", ""),
            data.get("target_market", ""),
            data.get("previous_exhibition_experience", ""),
            booth_type_id, booth_type_raw,
            data.get("booth_size", ""),
            safe_int(data.get("number_of_booth_staff")),
            data.get("power_requirement", ""),
            data.get("internet_requirement", ""),
            data.get("interested_sponsorship", ""),
            data.get("interested_speaking", ""),
            data.get("interested_product_launch", ""),
            data.get("special_requirements", ""),
            data.get("terms_conditions", ""),
            data.get("consent_marketing", ""),
            "pending", ts, ts,
        ))

        doc_fields = ["company_logo", "product_images", "company_profile", "business_registration"]
        for field in doc_fields:
            file_path, orig_name, size, mime = save_file(files, field)
            if file_path:
                exec_one(conn, """
                    INSERT INTO documents
                      (registration_id, document_type, file_path,
                       original_name, file_size_bytes, mime_type, uploaded_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (reg_id, field, file_path, orig_name, size, mime, ts))

        exec_one(conn, """
            INSERT INTO audit_log
              (table_name, record_id, action, changed_by, new_values)
            VALUES (%s,%s,%s,%s,%s)
        """, ("registrations", reg_id, "INSERT", "form_submit",
              json.dumps({"company_name": data.get("company_name")})))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Registration submitted successfully!",
            "registration_id": reg_id,
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/registrations")
def list_registrations():
    conn = get_db()
    rows = fetch_all(conn, """
        SELECT
            r.id, r.status, r.created_at,
            c.company_name, c.brand_name, c.company_website,
            c.industry_sector_raw, c.year_established,
            ct.contact_person_name, ct.email_address,
            ct.phone_number, ct.country, ct.city,
            r.product_service_category, r.target_market,
            r.booth_type_raw, r.booth_size,
            r.number_of_booth_staff,
            r.power_requirement, r.internet_requirement,
            r.interested_sponsorship, r.interested_speaking,
            r.interested_product_launch,
            r.special_requirements,
            r.terms_conditions, r.consent_marketing
        FROM registrations r
        JOIN companies c  ON c.id = r.company_id
        JOIN contacts  ct ON ct.id = r.contact_id
        ORDER BY r.created_at DESC
    """)
    return jsonify(rows)


@app.route("/registrations/<int:reg_id>")
def get_registration(reg_id):
    conn = get_db()
    rows = fetch_all(conn, """
        SELECT r.*, c.company_name, c.brand_name, ct.email_address, ct.phone_number
        FROM registrations r
        JOIN companies c  ON c.id = r.company_id
        JOIN contacts  ct ON ct.id = r.contact_id
        WHERE r.id = %s
    """, (reg_id,))

    if not rows:
        return jsonify({"error": "Not found"}), 404

    reg = rows[0]
    docs = fetch_all(conn, "SELECT * FROM documents WHERE registration_id = %s", (reg_id,))
    reg["documents"] = docs
    return jsonify(reg)


@app.route("/registrations/<int:reg_id>/status", methods=["POST"])
def update_status(reg_id):
    try:
        data = request.get_json()
        status = data.get("status")
        if status not in ("pending", "approved", "rejected"):
            return jsonify({"success": False, "message": "Invalid status"}), 400
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "UPDATE registrations SET status = %s WHERE id = %s",
            (status, reg_id)
        )
        conn.commit()
        cur.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    print("WellExpo 2026 server running at http://localhost:5000")
    print("Connecting to Supabase...")
    get_db()
    print("Database connected!")
    app.run(debug=False, port=5000)