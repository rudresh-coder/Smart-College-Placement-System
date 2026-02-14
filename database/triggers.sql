DELIMITER $$

DROP TRIGGER IF EXISTS after_offer_insert$$
DROP TRIGGER IF EXISTS after_offer_update$$

CREATE TRIGGER after_offer_insert
AFTER INSERT ON offers
FOR EACH ROW
BEGIN
    IF NEW.offer_status = 'ACCEPTED' THEN
        UPDATE applications
        SET status = 'OFFERED'
        WHERE student_id = NEW.student_id
          AND job_id = NEW.job_id;
    ELSEIF NEW.offer_status = 'REJECTED' THEN
        UPDATE applications
        SET status = 'REJECTED'
        WHERE student_id = NEW.student_id
          AND job_id = NEW.job_id;
    ELSE
        -- PENDING
        UPDATE applications
        SET status = 'PENDING'
        WHERE student_id = NEW.student_id
          AND job_id = NEW.job_id;
    END IF;
END $$

CREATE TRIGGER after_offer_update
AFTER UPDATE ON offers
FOR EACH ROW
BEGIN
    IF NEW.offer_status <> OLD.offer_status THEN
        IF NEW.offer_status = 'ACCEPTED' THEN
            UPDATE applications
            SET status = 'OFFERED'
            WHERE student_id = NEW.student_id
              AND job_id = NEW.job_id;
        ELSEIF NEW.offer_status = 'REJECTED' THEN
            UPDATE applications
            SET status = 'REJECTED'
            WHERE student_id = NEW.student_id
              AND job_id = NEW.job_id;
        ELSE
            UPDATE applications
            SET status = 'PENDING'
            WHERE student_id = NEW.student_id
              AND job_id = NEW.job_id;
        END IF;
    END IF;
END $$

DELIMITER ;
