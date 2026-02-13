DELIMITER $$

CREATE PROCEDURE check_student_eligibility (
    IN p_student_id INT,
    IN p_job_id INT
)
BEGIN
    DECLARE student_cgpa DECIMAL(3,2);
    DECLARE required_cgpa DECIMAL(3,2);

    SELECT cgpa INTO student_cgpa
    FROM students
    WHERE student_id = p_student_id;

    SELECT min_cgpa INTO required_cgpa
    FROM job_roles
    WHERE job_id = p_job_id;

    IF student_cgpa >= required_cgpa THEN
        SELECT 'ELIGIBLE' AS status;
    ELSE
        SELECT 'NOT ELIGIBLE' AS status;
    END IF;
END $$

DELIMITER ;

DELIMITER $$

CREATE PROCEDURE apply_for_job (
    IN p_student_id INT,
    IN p_job_id INT
)
BEGIN
    DECLARE student_cgpa DECIMAL(3,2);
    DECLARE required_cgpa DECIMAL(3,2);

    SELECT cgpa INTO student_cgpa
    FROM students
    WHERE student_id = p_student_id;

    SELECT min_cgpa INTO required_cgpa
    FROM job_roles
    WHERE job_id = p_job_id;

    IF student_cgpa >= required_cgpa THEN
        INSERT INTO applications (student_id, job_id, applied_date, status)
        VALUES (p_student_id, p_job_id, CURDATE(), 'APPLIED');
    ELSE
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Student not eligible for this job';
    END IF;
END $$

DELIMITER ;
