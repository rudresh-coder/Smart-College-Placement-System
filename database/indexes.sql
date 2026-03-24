DROP INDEX idx_student_id ON students;
DROP INDEX idx_job_id ON job_roles;
DROP INDEX idx_application_student_job ON applications;

CREATE INDEX idx_applications_job_id ON applications(job_id);
CREATE INDEX idx_offers_student_job ON offers(student_id, job_id);
CREATE INDEX idx_job_roles_company_id ON job_roles(company_id);
