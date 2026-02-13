import { useState} from "react";
import "./App.css";

const API_BASE = "http://127.0.0.1:5000";

function App() {
  const [userType, setUserType] = useState(null); // null, "student", "admin"
  const [studentId, setStudentId] = useState("");
  const [activeTab, setActiveTab] = useState("jobs");
  
  // Student state
  const [student, setStudent] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  
  // Admin state
  const [students, setStudents] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [allApplications, setAllApplications] = useState([]);
  const [stats, setStats] = useState([]);
  
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // ============================================
  // STUDENT LOGIN & WORKFLOWS
  // ============================================
  
  const handleStudentLogin = async (e) => {
    e.preventDefault();
    if (!studentId) return;
    
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/students/${studentId}`);
      if (!res.ok) throw new Error("Student not found");
      
      const data = await res.json();
      setStudent(data);
      setUserType("student");
      loadJobs();
      loadStudentApplications();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadJobs = async () => {
    try {
      const res = await fetch(`${API_BASE}/jobs`);
      const data = await res.json();
      setJobs(data);
    } catch (error) {
      setMessage(error.message);
    }
  };

  const loadStudentApplications = async () => {
    try {
      const res = await fetch(`${API_BASE}/applications/${studentId}`);
      const data = await res.json();
      setApplications(data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleApply = async (jobId) => {
    try {
      setMessage("");
      setLoading(true);
      
      // Check eligibility
      const eligRes = await fetch(`${API_BASE}/eligibility?student_id=${studentId}&job_id=${jobId}`);
      const eligData = await eligRes.json();
      
      if (eligData.status === "NOT ELIGIBLE") {
        setMessage("You are not eligible for this job (CGPA requirement not met)");
        return;
      }
      
      // Apply
      const applyRes = await fetch(`${API_BASE}/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: Number(studentId), job_id: jobId }),
      });
      
      const applyData = await applyRes.json();
      setMessage(` ${applyData.message || "Application successful"}`);
      loadStudentApplications();
    } catch (error) {
      setMessage(` ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // ADMIN WORKFLOWS
  // ============================================
  
  const handleAdminLogin = () => {
    setUserType("admin");
    setActiveTab("students");
    loadAdminData();
  };

  const loadAdminData = async () => {
    try {
      // Load all data for admin
      const [studentsRes, companiesRes, appsRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/admin/students`),
        fetch(`${API_BASE}/admin/companies`),
        fetch(`${API_BASE}/admin/applications`),
        fetch(`${API_BASE}/admin/stats/placement`),
      ]);
      
      setStudents(await studentsRes.json());
      setCompanies(await companiesRes.json());
      setAllApplications(await appsRes.json());
      setStats(await statsRes.json());
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleCreateStudent = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
      const res = await fetch(`${API_BASE}/admin/students`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      
      const result = await res.json();
      setMessage(result.message || "Student created successfully");
      loadAdminData();
      e.target.reset();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleDeleteStudent = async (id) => {
    if (!confirm("Delete this student?")) return;
    
    try {
      const res = await fetch(`${API_BASE}/admin/students/${id}`, { method: "DELETE" });
      const data = await res.json();
      setMessage(data.message);
      loadAdminData();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
      const res = await fetch(`${API_BASE}/admin/companies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      
      const result = await res.json();
      setMessage(result.message || "Company created successfully");
      loadAdminData();
      e.target.reset();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleCreateJob = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
      const res = await fetch(`${API_BASE}/admin/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      
      const result = await res.json();
      setMessage(result.message || "Job created successfully");
      e.target.reset();
    } catch (error) {
      setMessage(error.message);
    }
  };

  const handleCreateOffer = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData);
    
    try {
      const res = await fetch(`${API_BASE}/admin/offers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      
      const result = await res.json();
      setMessage(result.message || "Offer created successfully (Application status auto-updated)");
      loadAdminData();
      e.target.reset();
    } catch (error) {
      setMessage(error.message);
    }
  };

  // ============================================
  // RENDER: USER TYPE SELECTION
  // ============================================
  
  if (!userType) {
    return (
      <div className="container">
        <div className="login-box">
          <h1> Smart College Placement System</h1>
          <p style={{ marginBottom: "30px", color: "#aaa" }}>Select User Type</p>
          
          <button onClick={handleAdminLogin} style={{ marginBottom: "15px", width: "100%" }}>
             Login as Placement Officer (Admin)
          </button>
          
          <hr style={{ margin: "20px 0", border: "1px solid #444" }} />
          
          <form onSubmit={handleStudentLogin}>
            <input
              type="number"
              placeholder="Enter Student ID"
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? "Loading..." : " Login as Student"}
            </button>
          </form>
          
          {message && <div className="message error">{message}</div>}
        </div>
      </div>
    );
  }

  // ============================================
  // RENDER: STUDENT VIEW
  // ============================================
  
  if (userType === "student") {
    return (
      <div className="container">
        <header className="header">
          <h1>Smart College Placement System</h1>
          <div className="student-info">
            <strong>{student?.name}</strong> | CGPA: {student?.cgpa} | {student?.department}
            <button onClick={() => { setUserType(null); setStudent(null); }} style={{ marginLeft: "20px", fontSize: "0.9em" }}>
              Logout
            </button>
          </div>
        </header>

        <nav className="tabs">
          <button className={activeTab === "jobs" ? "active" : ""} onClick={() => setActiveTab("jobs")}>
             Job Listings
          </button>
          <button className={activeTab === "applications" ? "active" : ""} onClick={() => setActiveTab("applications")}>
             My Applications
          </button>
        </nav>

        {message && <div className="message">{message}</div>}

        {activeTab === "jobs" && (
          <div className="section">
            <h2>Available Jobs</h2>
            {jobs.length === 0 ? <p>No jobs available</p> : (
              <div className="job-grid">
                {jobs.map((job) => (
                  <div key={job.job_id} className="card">
                    <h3>{job.role_name}</h3>
                    <p><strong> Company:</strong> {job.company_name}</p>
                    <p><strong> Location:</strong> {job.location}</p>
                    <p><strong> Package:</strong> ₹{job.package_lpa} LPA</p>
                    <p><strong> Min CGPA:</strong> {job.min_cgpa}</p>
                    <p><strong> Eligible:</strong> {job.eligible_branches}</p>
                    <button
                      onClick={() => handleApply(job.job_id)}
                      disabled={loading || student?.cgpa < job.min_cgpa}
                      className={student?.cgpa < job.min_cgpa ? "disabled" : ""}
                    >
                      {student?.cgpa < job.min_cgpa ? "Not Eligible" : "Apply Now"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "applications" && (
          <div className="section">
            <h2>My Applications</h2>
            {applications.length === 0 ? <p>No applications yet</p> : (
              <div className="application-list">
                {applications.map((app) => (
                  <div key={app.application_id} className="card">
                    <h3>{app.role_name}</h3>
                    <p><strong> Company:</strong> {app.company_name}</p>
                    <p><strong> Package:</strong> ₹{app.package_lpa} LPA</p>
                    <p><strong> Applied:</strong> {new Date(app.applied_date).toLocaleDateString()}</p>
                    <p>
                      <strong>Status:</strong>{" "}
                      <span className={`status ${app.status.toLowerCase()}`}>{app.status}</span>
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // ============================================
  // RENDER: ADMIN VIEW
  // ============================================
  
  return (
    <div className="container">
      <header className="header">
        <h1> Placement Officer Dashboard</h1>
        <button onClick={() => setUserType(null)} style={{ float: "right" }}>Logout</button>
      </header>

      <nav className="tabs">
        <button className={activeTab === "students" ? "active" : ""} onClick={() => setActiveTab("students")}>
           Students
        </button>
        <button className={activeTab === "companies" ? "active" : ""} onClick={() => setActiveTab("companies")}>
           Companies
        </button>
        <button className={activeTab === "jobs" ? "active" : ""} onClick={() => setActiveTab("jobs")}>
           Add Jobs
        </button>
        <button className={activeTab === "offers" ? "active" : ""} onClick={() => setActiveTab("offers")}>
           Create Offers
        </button>
        <button className={activeTab === "applications" ? "active" : ""} onClick={() => setActiveTab("applications")}>
           All Applications
        </button>
        <button className={activeTab === "stats" ? "active" : ""} onClick={() => setActiveTab("stats")}>
           Stats
        </button>
      </nav>

      {message && <div className="message">{message}</div>}

      {/* STUDENTS TAB */}
      {activeTab === "students" && (
        <div className="section">
          <h2>Add Student</h2>
          <form onSubmit={handleCreateStudent} className="admin-form">
            <input name="roll_no" placeholder="Roll No" required />
            <input name="name" placeholder="Name" required />
            <input name="email" type="email" placeholder="Email" required />
            <input name="department" placeholder="Department" required />
            <input name="cgpa" type="number" step="0.01" placeholder="CGPA" required />
            <input name="graduation_year" type="number" placeholder="Graduation Year" required />
            <button type="submit">Add Student</button>
          </form>

          <h2>All Students</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Roll No</th>
                <th>Name</th>
                <th>Email</th>
                <th>Dept</th>
                <th>CGPA</th>
                <th>Year</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {students.map((s) => (
                <tr key={s.student_id}>
                  <td>{s.student_id}</td>
                  <td>{s.roll_no}</td>
                  <td>{s.name}</td>
                  <td>{s.email}</td>
                  <td>{s.department}</td>
                  <td>{s.cgpa}</td>
                  <td>{s.graduation_year}</td>
                  <td>
                    <button onClick={() => handleDeleteStudent(s.student_id)} className="delete-btn">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* COMPANIES TAB */}
      {activeTab === "companies" && (
        <div className="section">
          <h2>Add Company</h2>
          <form onSubmit={handleCreateCompany} className="admin-form">
            <input name="company_name" placeholder="Company Name" required />
            <input name="location" placeholder="Location" required />
            <input name="package_lpa" type="number" step="0.01" placeholder="Package (LPA)" required />
            <button type="submit">Add Company</button>
          </form>

          <h2>All Companies</h2>
          <div className="job-grid">
            {companies.map((c) => (
              <div key={c.company_id} className="card">
                <h3>{c.company_name}</h3>
                <p> Location: {c.location}</p>
                <p> Package: ₹{c.package_lpa} LPA</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ADD JOBS TAB */}
      {activeTab === "jobs" && (
        <div className="section">
          <h2>Add Job Role</h2>
          <form onSubmit={handleCreateJob} className="admin-form">
            <select name="company_id" required>
              <option value="">Select Company</option>
              {companies.map((c) => (
                <option key={c.company_id} value={c.company_id}>{c.company_name}</option>
              ))}
            </select>
            <input name="role_name" placeholder="Role Name" required />
            <input name="min_cgpa" type="number" step="0.01" placeholder="Min CGPA" required />
            <input name="eligible_branches" placeholder="Eligible Branches (e.g., CSE, IT)" required />
            <button type="submit">Add Job</button>
          </form>
        </div>
      )}

      {/* CREATE OFFERS TAB */}
      {activeTab === "offers" && (
        <div className="section">
          <h2>Create Offer</h2>
          <form onSubmit={handleCreateOffer} className="admin-form">
            <input name="student_id" type="number" placeholder="Student ID" required />
            <input name="job_id" type="number" placeholder="Job ID" required />
            <select name="offer_status" required>
              <option value="">Select Status</option>
              <option value="ACCEPTED">ACCEPTED</option>
              <option value="PENDING">PENDING</option>
              <option value="REJECTED">REJECTED</option>
            </select>
            <button type="submit">Create Offer (Auto-updates Application Status)</button>
          </form>
        </div>
      )}

      {/* ALL APPLICATIONS TAB */}
      {activeTab === "applications" && (
        <div className="section">
          <h2>All Applications</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Student</th>
                <th>Company</th>
                <th>Role</th>
                <th>Applied Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {allApplications.map((app) => (
                <tr key={app.application_id}>
                  <td>{app.student_name}</td>
                  <td>{app.company_name}</td>
                  <td>{app.role_name}</td>
                  <td>{new Date(app.applied_date).toLocaleDateString()}</td>
                  <td><span className={`status ${app.status.toLowerCase()}`}>{app.status}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* STATS TAB */}
      {activeTab === "stats" && (
        <div className="section">
          <h2>Company-wise Placement Statistics</h2>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Company</th>
                <th>Total Offers</th>
              </tr>
            </thead>
            <tbody>
              {stats.map((stat, idx) => (
                <tr key={idx}>
                  <td>{stat.company_name}</td>
                  <td>{stat.total_offers}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default App;
