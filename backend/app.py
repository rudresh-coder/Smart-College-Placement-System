from flask import Flask, request, jsonify
import os
import mysql.connector

app = Flask(__name__)

db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "placement_user"),
    password=os.getenv("DB_PASSWORD", "placement_pass"),
    database=os.getenv("DB_NAME", "placement_db")
)

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

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.callproc("apply_for_job", [student_id, job_id])
        db.commit()
        return jsonify({"message": "Application successful"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()

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

    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        cursor.callproc("check_student_eligibility", [student_id, job_id])
        for result in cursor.stored_results():
            row = result.fetchone()
            if row is None:
                return jsonify({"error": "No eligibility result found"}), 404
            return jsonify(row)
        return jsonify({"error": "No eligibility result found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        if cursor is not None:
            cursor.close()

if __name__ == "__main__":
    app.run(debug=True)
