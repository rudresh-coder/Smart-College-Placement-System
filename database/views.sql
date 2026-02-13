CREATE VIEW student_placement_status AS
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

CREATE VIEW company_placement_stats AS
SELECT
    c.company_name,
    COUNT(o.offer_id) AS total_offers
FROM companies c 
JOIN job_roles j ON c.company_id = j.company_id
JOIN offers o ON j.job_id = o.job_id
GROUP BY c.company_name;