CREATE INDEX idx_student_id ON students(student_id);
CREATE INDEX idx_job_id ON job_roles(job_id);
CREATE INDEX idx_application_student_job ON applications(student_id, job_id);