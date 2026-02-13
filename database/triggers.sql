DELIMITER $$

CREATE TRIGGER after_offer_insert
AFTER INSERT ON offers
FOR EACH ROW
BEGIN
    UPDATE applications
    SET status = 'OFFERED'
    WHERE student_id = NEW.student_id
    AND job_id = NEW.job_id;
END $$

DELIMITER ;