from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from mysql.connector import pooling

app = Flask(__name__)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

CORS(
    app,
    resources={r"/*": {"origins": ALLOWED_ORIGINS}},
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key"],
)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "")
ALLOWED_OFFER_STATUS = {"PENDING", "ACCEPTED", "REJECTED"}

@app.before_request
def protect_admin_routes():
    if not request.path.startswith("/admin"):
        return None

    # allow CORS preflight
    if request.method == "OPTIONS":
        return None

    if not ADMIN_API_KEY:
        return jsonify({"error": "Server misconfigured: ADMIN_API_KEY is not set"}), 500

    provided_key = request.headers.get("X-Admin-Key", "")
    if provided_key != ADMIN_API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    return None

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "placement_user"),
    "password": os.getenv("DB_PASSWORD", "placement_pass"),
    "database": os.getenv("DB_NAME", "placement_db"),
    "port": int(os.getenv("DB_PORT", "3307"))
}

connection_pool = pooling.MySQLConnectionPool(
    pool_name="placement_pool",
    pool_size=5,
    **db_config
)

def get_conn():
    return connection_pool.get_connection()

def _fetch_student_job_cgpa(cursor, student_id, job_id):
    cursor.execute(
        """
        SELECT s.cgpa AS student_cgpa, j.min_cgpa AS required_cgpa
        FROM students s
        JOIN job_roles j ON j.job_id = %s
        WHERE s.student_id = %s
        """,
        (job_id, student_id),
    )
    return cursor.fetchone()

def _application_status_from_offer(offer_status):
    if offer_status == "ACCEPTED":
        return "OFFERED"
    if offer_status == "REJECTED":
        return "REJECTED"
    return "PENDING"

# ============================================
# STUDENT WORKFLOWS
# ============================================

@app.route("/eligibility", methods=["GET"])
def check_eligibility():
    student_id = request.args.get("student_id")
    job_id = request.args.get("job_id")

    if student_id is None or job_id is None:
        return jsonify({"error": "student_id and job_id are required"}), 400

    try:
        student_id = int(student_id)
        job_id = int(job_id)
    except (TypeError, ValueError):
        return jsonify({"error": "student_id and job_id must be integers"}), 400

    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        row = _fetch_student_job_cgpa(cursor, student_id, job_id)

        if row is None:
            return jsonify({"status": "NOT ELIGIBLE"})

        status = "ELIGIBLE" if row["student_cgpa"] >= row["required_cgpa"] else "NOT ELIGIBLE"
        return jsonify({"status": status})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/apply", methods=["POST"])
def apply_job():
    data = request.get_json(silent=True) or {}
    if "student_id" not in data or "job_id" not in data:
        return jsonify({"error": "student_id and job_id are required"}), 400

    try:
        student_id = int(data["student_id"])
        job_id = int(data["job_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "student_id and job_id must be integers"}), 400

    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)

        row = _fetch_student_job_cgpa(cursor, student_id, job_id)
        if row is None:
            return jsonify({"error": "Student or job not found"}), 404
        if row["student_cgpa"] < row["required_cgpa"]:
            return jsonify({"error": "Student not eligible for this job"}), 400

        cursor.execute(
            "SELECT application_id FROM applications WHERE student_id = %s AND job_id = %s",
            (student_id, job_id),
        )
        if cursor.fetchone():
            return jsonify({"message": "Application already exists"}), 200

        cursor.execute(
            """
            INSERT INTO applications (student_id, job_id, applied_date, status)
            VALUES (%s, %s, CURDATE(), 'APPLIED')
            """,
            (student_id, job_id),
        )
        db.commit()
        return jsonify({"message": "Application successful"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    """Get student profile"""
    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if student is None:
            return jsonify({"error": "Student not found"}), 404
        return jsonify(student)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/applications/<int:student_id>", methods=["GET"])
def get_student_applications(student_id):
    """Student views their application history"""
    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, j.role_name, c.company_name, c.package_lpa
            FROM applications a
            JOIN job_roles j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            WHERE a.student_id = %s
            ORDER BY a.applied_date DESC
        """, (student_id,))
        applications = cursor.fetchall()
        return jsonify(applications)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/jobs", methods=["GET"])
def get_jobs():
    """Get all available jobs"""
    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT j.*, c.company_name, c.location, c.package_lpa
            FROM job_roles j
            JOIN companies c ON j.company_id = c.company_id
        """)
        jobs = cursor.fetchall()
        return jsonify(jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

# ============================================
# ADMIN/PLACEMENT OFFICER WORKFLOWS (CRUD)
# ============================================

# --- Student Management ---

@app.route("/admin/students", methods=["GET"])
def admin_get_all_students():
    """Admin views all students"""
    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students ORDER BY student_id DESC")
        students = cursor.fetchall()
        return jsonify(students)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/students", methods=["POST"])
def admin_create_student():
    """Admin adds a new student"""
    data = request.get_json(silent=True) or {}
    required_fields = ["roll_no", "name", "email", "department", "cgpa", "graduation_year"]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO students (roll_no, name, email, department, cgpa, graduation_year)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (data["roll_no"], data["name"], data["email"], 
              data["department"], data["cgpa"], data["graduation_year"]))
        db.commit()
        return jsonify({"message": "Student created successfully", "student_id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/students/<int:student_id>", methods=["PUT"])
def admin_update_student(student_id):
    """Admin updates student details"""
    data = request.get_json(silent=True) or {}
    
    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        
        # Build dynamic update query
        update_fields = []
        values = []
        
        allowed_fields = ["roll_no", "name", "email", "department", "cgpa", "graduation_year"]
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            return jsonify({"error": "No fields to update"}), 400
        
        values.append(student_id)
        query = f"UPDATE students SET {', '.join(update_fields)} WHERE student_id = %s"
        
        cursor.execute(query, values)
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify({"message": "Student updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/students/<int:student_id>", methods=["DELETE"])
def admin_delete_student(student_id):
    """Admin deletes a student"""
    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        
        # Delete related offers first
        cursor.execute("DELETE FROM offers WHERE student_id = %s", (student_id,))
        
        # Delete related applications
        cursor.execute("DELETE FROM applications WHERE student_id = %s", (student_id,))
        
        # Now delete the student
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Student not found"}), 404
            
        return jsonify({"message": "Student deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

# --- Company Management ---

@app.route("/admin/companies", methods=["GET"])
def admin_get_companies():
    """Admin views all companies"""
    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM companies ORDER BY company_id DESC")
        companies = cursor.fetchall()
        return jsonify(companies)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/companies", methods=["POST"])
def admin_create_company():
    """Admin adds a new company"""
    data = request.get_json(silent=True) or {}
    required_fields = ["company_name", "location", "package_lpa"]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO companies (company_name, location, package_lpa)
            VALUES (%s, %s, %s)
        """, (data["company_name"], data["location"], data["package_lpa"]))
        db.commit()
        return jsonify({"message": "Company created successfully", "company_id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/companies/<int:company_id>", methods=["DELETE"])
def admin_delete_company(company_id):
    """Admin deletes a company"""
    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Company not found"}), 404
            
        return jsonify({"message": "Company deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

# --- Job Role Management ---

@app.route("/admin/jobs", methods=["POST"])
def admin_create_job():
    """Admin adds a new job role"""
    data = request.get_json(silent=True) or {}
    required_fields = ["company_id", "role_name", "min_cgpa", "eligible_branches"]
    
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO job_roles (company_id, role_name, min_cgpa, eligible_branches)
            VALUES (%s, %s, %s, %s)
        """, (data["company_id"], data["role_name"], data["min_cgpa"], data["eligible_branches"]))
        db.commit()
        return jsonify({"message": "Job role created successfully", "job_id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/jobs/<int:job_id>", methods=["DELETE"])
def admin_delete_job(job_id):
    """Admin deletes a job role"""
    db = connection_pool.get_connection()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("DELETE FROM job_roles WHERE job_id = %s", (job_id,))
        db.commit()
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Job not found"}), 404
            
        return jsonify({"message": "Job deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

# --- Offer Management ---

@app.route("/admin/offers", methods=["POST"])
def admin_create_offer():
    data = request.get_json(silent=True) or {}
    required_fields = ["student_id", "job_id", "offer_status"]

    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    try:
        student_id = int(data["student_id"])
        job_id = int(data["job_id"])
    except (TypeError, ValueError):
        return jsonify({"error": "student_id and job_id must be integers"}), 400

    offer_status = str(data["offer_status"]).upper()
    if offer_status not in ALLOWED_OFFER_STATUS:
        return jsonify({"error": "offer_status must be one of PENDING, ACCEPTED, REJECTED"}), 400

    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT s.student_id, j.job_id
            FROM students s
            JOIN job_roles j ON j.job_id = %s
            WHERE s.student_id = %s
            """,
            (job_id, student_id),
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "Student or job not found"}), 404

        application_status = _application_status_from_offer(offer_status)

        cursor.execute(
            "SELECT application_id FROM applications WHERE student_id = %s AND job_id = %s",
            (student_id, job_id),
        )
        existing_app = cursor.fetchone()

        if existing_app:
            cursor.execute(
                """
                UPDATE applications
                SET status = %s
                WHERE student_id = %s AND job_id = %s
                """,
                (application_status, student_id, job_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO applications (student_id, job_id, applied_date, status)
                VALUES (%s, %s, CURDATE(), %s)
                """,
                (student_id, job_id, application_status),
            )

        cursor.execute(
            """
            INSERT INTO offers (student_id, job_id, offer_date, offer_status)
            VALUES (%s, %s, CURDATE(), %s)
            """,
            (student_id, job_id, offer_status),
        )
        db.commit()

        return jsonify({"message": "Offer created successfully", "offer_id": cursor.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/offers/<int:offer_id>", methods=["PUT"])
def admin_update_offer_status(offer_id):
    data = request.get_json(silent=True) or {}
    offer_status = str(data.get("offer_status", "")).upper()
    if offer_status not in ALLOWED_OFFER_STATUS:
        return jsonify({"error": "offer_status must be one of PENDING, ACCEPTED, REJECTED"}), 400

    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT offer_id, student_id, job_id FROM offers WHERE offer_id = %s",
            (offer_id,),
        )
        offer = cursor.fetchone()
        if offer is None:
            return jsonify({"error": "Offer not found"}), 404

        cursor.execute(
            "UPDATE offers SET offer_status = %s WHERE offer_id = %s",
            (offer_status, offer_id),
        )

        cursor.execute(
            """
            UPDATE applications
            SET status = %s
            WHERE student_id = %s AND job_id = %s
            """,
            (_application_status_from_offer(offer_status), offer["student_id"], offer["job_id"]),
        )

        db.commit()
        return jsonify({"message": "Offer status updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

# ============================================
# ANALYTICAL WORKFLOWS (Reports & Stats)
# ============================================

@app.route("/admin/stats/placement", methods=["GET"])
def get_placement_stats():
    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                c.company_name,
                COUNT(o.offer_id) AS total_placements
            FROM companies c
            JOIN job_roles j ON c.company_id = j.company_id
            JOIN offers o ON j.job_id = o.job_id
            WHERE o.offer_status = 'ACCEPTED'
            GROUP BY c.company_name
            """
        )
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/stats/student-placements", methods=["GET"])
def get_student_placements():
    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                s.student_id,
                s.name,
                c.company_name,
                j.role_name,
                o.offer_status
            FROM students s
            JOIN offers o ON s.student_id = o.student_id
            JOIN job_roles j ON o.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            """
        )
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

@app.route("/admin/applications", methods=["GET"])
def admin_get_all_applications():
    """Admin views all applications"""
    db = get_conn()
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.*, s.name as student_name, j.role_name, c.company_name
            FROM applications a
            JOIN students s ON a.student_id = s.student_id
            JOIN job_roles j ON a.job_id = j.job_id
            JOIN companies c ON j.company_id = c.company_id
            ORDER BY a.applied_date DESC
        """)
        applications = cursor.fetchall()
        return jsonify(applications)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()
        if db.is_connected():
            db.close()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
