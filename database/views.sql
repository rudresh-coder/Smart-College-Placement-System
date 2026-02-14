-- View: student placement status (only those with offers)
CREATE OR REPLACE VIEW student_placement_status AS
SELECT 
    s.student_id,
    s.name,
    c.company_name,
    j.role_name,
    o.offer_status
FROM students s
JOIN offers o ON s.student_id = o.student_id
JOIN job_roles j ON o.job_id = j.job_id
JOIN companies c ON j.company_id = c.company_id;

-- Company-wise placements: count ONLY accepted offers
CREATE OR REPLACE VIEW company_placement_stats AS
SELECT
    c.company_name,
    COUNT(o.offer_id) AS total_placements
FROM companies c
JOIN job_roles j ON c.company_id = j.company_id
JOIN offers o ON j.job_id = o.job_id
WHERE o.offer_status = 'ACCEPTED'
GROUP BY c.company_name;
