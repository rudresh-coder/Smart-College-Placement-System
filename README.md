# Smart College Placement Management System

A full-stack, database-driven web application that models a real-world college placement workflow using **Advanced DBMS concepts**.  
The system enables students to check eligibility and apply for jobs, while placement admins manage students, companies, job roles, and offers — with **business rules enforced at the database level**.

---

## Tech Stack
- **Frontend:** React (Vite), CSS
- **Backend:** Python, Flask, Flask-CORS
- **Database:** MySQL / MariaDB
- **Database Concepts:** Stored Procedures, Triggers, Views, Indexes, Constraints

---

## Project Structure
- **Backend:** [`backend/app.py`](backend/app.py)
- **Database Scripts:**
  - Schema: [`database/schema.sql`](database/schema.sql)
  - Procedures: [`database/procedures.sql`](database/procedures.sql)
  - Triggers: [`database/triggers.sql`](database/triggers.sql)
  - Views: [`database/views.sql`](database/views.sql)
  - Indexes: [`database/indexes.sql`](database/indexes.sql)
- **Frontend:** [`frontend/src/App.jsx`](frontend/src/App.jsx), [`frontend/src/App.css`](frontend/src/App.css)

---

## Core Workflows

### Student
- Login using Student ID (simulated identity)
- Browse available job roles
- Check eligibility using a stored procedure
- Apply for eligible jobs
- View application history and status

### Admin (Placement Officer)
- Manage students, companies, and job roles
- Create and update placement offers
- View placement reports and statistics

---

## Business Rules (Database-Driven)

- Eligibility logic is enforced using stored procedure `check_student_eligibility`
- Job applications are created using stored procedure `apply_for_job`
- Duplicate applications are prevented using a composite `UNIQUE(student_id, job_id)` constraint
- Offer creation and updates automatically synchronize application status using triggers
- Placement statistics are computed dynamically using SQL views

### Status Mapping
| Offer Status | Application Status |
|-------------|-------------------|
| PENDING     | APPLIED           |
| ACCEPTED    | OFFERED           |
| REJECTED    | REJECTED          |

---

## Reports
- **Company-wise placement statistics** via view `company_placement_stats`
- **Student placement status** via view `student_placement_status`

---

## Run Backend
```sh
cd backend
python app.py
```
---

## Run frontend
```sh
cd frontend
npm install
npm run dev
```
---

## Environment variables
- `DB_HOST` (default: `localhost`)
- `DB_USER` (default: `placement_user`)
- `DB_PASSWORD` (default: `placement_pass`)
- `DB_NAME` (default: `placement_db`)
- `DB_PORT` (default: `3307`)