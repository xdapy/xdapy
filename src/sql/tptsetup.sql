DROP database if exists optionDB;

CREATE database optionDB;

use optionDB;

CREATE TABLE options_entity
    (
    name    VARCHAR(40) NOT NULL,
    level   INT,
    PRIMARY KEY (name) 
    )
    ENGINE=InnoDB;
    
CREATE TABLE options_parameter
    (
    name    VARCHAR(40) NOT NULL,
    type    VARCHAR(10) NOT NULL,
    defined VARCHAR(100),
    PRIMARY KEY (name) 
    )
    ENGINE=InnoDB;
    
    CREATE TABLE options_data
    (
    name    VARCHAR(40) NOT NULL,
    PRIMARY KEY (name) 
    )
    ENGINE=InnoDB;
    
CREATE TABLE options_datalist
    (
    entity_name    VARCHAR(40) NOT NULL,
    data_name    VARCHAR(40) NOT NULL,
    PRIMARY KEY (entity_name, data_name),
    CONSTRAINT FOREIGN KEY (entity_name) REFERENCES options_entity(name) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FOREIGN KEY (data_name) REFERENCES options_data(name) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
    
CREATE TABLE options_parameterlist
    (
    entity_name    VARCHAR(40) NOT NULL,
    parameter_name    VARCHAR(40) NOT NULL,
    mandatory    BOOL,
    PRIMARY KEY (entity_name, parameter_name),
    CONSTRAINT FOREIGN KEY (entity_name) REFERENCES options_entity(name) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FOREIGN KEY (parameter_name) REFERENCES options_parameter(name) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
    
CREATE TABLE options_connections
    (
    parent    VARCHAR(40) NOT NULL,
    child    VARCHAR(40) NOT NULL,
    PRIMARY KEY (parent, child), 
    CONSTRAINT FOREIGN KEY (parent) REFERENCES options_entity(name) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FOREIGN KEY (child) REFERENCES options_entity(name) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
   
INSERT INTO options_parameter(name, type, defined)
    VALUES ('name', 'STRING', ''), 
        ('comment', 'STRING', ''),
        ('valid', 'STRING', false),
        ('initials', 'STRING', ''), 
        ('glasses', 'BOOL', false),
        ('date of birth', 'DATE', NULL),
        ('handedness', 'STRING', ''),
        ('project','STRING', ''), 
        ('reference', 'STRING', '') ,
        ('project name','STRING',''),
        ('source directory', 'STRING',''),
        ('source file', 'STRING',''),
        ('keywords', 'STRING','') ,
        ('experimenter', 'STRING',''),
        ('date', 'DATE',NULL) ,
        ('viewing distance','DOUBLE',1), 
        ('start', 'DATETIME', NULL),
        ('end', 'DATETIME', NULL),
        ('software', 'STRING',''),
        ('hardware', 'STRING',''), 
        ('serial number', 'STRING',''),
        ('calibration file', 'STRING',''), 
        ('frame rate', 'DOUBLE',100),
        ('count', 'INT', NULL),
        ('file directory','STRING',''),
        ('slope', 'DOUBLE',NULL),
        ('threshold', 'DOUBLE',NULL),
        ('est','DOUBLE',NULL);

INSERT INTO options_data(name)
    VALUES ('calibration file');
    
INSERT INTO options_entity(name)
    VALUES ('observer'),
        ('experiment'),
        ('trial'),
        ('session');

INSERT INTO options_parameterlist(entity_name,parameter_name,mandatory)
    VALUES ('observer', 'name', true),
        ('observer', 'initials', true),
        ('observer', 'glasses', true),
        ('observer', 'handedness', true),
        ('experiment', 'reference', true),
        ('experiment', 'project name', true),
        ('experiment', 'keywords', true),
        ('experiment', 'experimenter', true),
        ('experiment', 'viewing distance', true),
        ('experiment', 'software', true),
        ('experiment', 'hardware', true),
        ('session', 'date', true),
        ('trial','comment', false),
        ('trial', 'valid', true),
        ('trial', 'count', true);

INSERT INTO options_datalist(entity_name,data_name)
    VALUES ('experiment', 'calibration file');

INSERT INTO options_connections(parent,child)
    VALUES ('experiment', 'observer'),
        ('observer', 'session'),
        ('session', 'trial');


DROP database if exists dataDB;

CREATE database dataDB;

use dataDB;

CREATE TABLE entities
    (
    id      INT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE, 
    name    VARCHAR(40),
    created    DATETIME,
    modified   DATETIME,
    PRIMARY KEY (id)
    )
    ENGINE=InnoDB;
    
CREATE TABLE data
    (
    id      INT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE,
    name    VARCHAR(40),
    value   Blob,
    time    TIMESTAMP,
    microseconds INT,
    PRIMARY KEY (id)
    )
    ENGINE=InnoDB;

CREATE TABLE parameters
    (
    id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name    VARCHAR(40) UNIQUE NOT NULL,
    PRIMARY KEY (id)
    )
    ENGINE=InnoDB;
    
CREATE TABLE string_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   VARCHAR(100) NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE table int_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   INT(20) NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE table double_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   DOUBLE NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE table bool_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   BOOL NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
        
CREATE table datetime_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   DATETIME NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE table date_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   DATE NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
    
CREATE table time_parameters
    (
    id    INT UNSIGNED NOT NULL,
    value   TIME NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

       
CREATE TABLE connections
    (
    name        VARCHAR(40),
    from_entity INT UNSIGNED NOT NULL,
    to_entity   INT UNSIGNED NOT NULL,
    PRIMARY KEY (name, from_entity, to_entity), 
    CONSTRAINT FOREIGN KEY (from_entity) REFERENCES entities(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FOREIGN KEY (to_entity) REFERENCES entities(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
   
CREATE TABLE parameterlist
    (
    entity_id   INT UNSIGNED NOT NULL,
    parameter_id    INT UNSIGNED NOT NULL, 
    PRIMARY KEY (entity_id, parameter_id),
    CONSTRAINT FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FOREIGN KEY (parameter_id) REFERENCES parameters(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;
    
CREATE TABLE datalist
    (
    entity_id   INT UNSIGNED NOT NULL,
    data_id    INT UNSIGNED NOT NULL UNIQUE,
    PRIMARY KEY (data_id),
    CONSTRAINT FOREIGN KEY (entity_id) REFERENCES entities(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FOREIGN KEY (data_id) REFERENCES data(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB; 

CREATE OR REPLACE VIEW parameter_view AS 
        SELECT name, id, value 
        FROM parameters join string_parameters using (id) 
    UNION 
        SELECT name, id, value
        FROM parameters join int_parameters using (id) 
    UNION 
        SELECT name, id, value  
        FROM parameters join double_parameters using (id) 
    UNION 
        SELECT name, id, value  
        FROM parameters join bool_parameters using (id) 
    UNION 
        SELECT name, id, value  
        FROM parameters join datetime_parameters using (id) 
    UNION 
        SELECT name, id, value  
        FROM parameters join date_parameters using (id)
    UNION 
        SELECT name, id, value  
        FROM parameters join time_parameters using (id) 
    order by id;
    
DELIMITER $$

CREATE PROCEDURE get_ancestors(IN nid INT)
    BEGIN
        DECLARE n INT;
        
        
        CREATE TEMPORARY TABLE __ancestors (
            id INT NOT NULL PRIMARY KEY
        );

        SELECT COUNT(*)
            FROM connections
            WHERE to_entity = nid INTO n;

        IF n <> 0 THEN
            CALL get_ancestors_routine(nid);
        END IF;
        
        SELECT entities.*
            FROM entities 
            JOIN __ancestors 
            on entities.id = __ancestors.id;
    END$$
    
CREATE PROCEDURE get_ancestors_routine(IN nid INT)
    BEGIN
        DECLARE n INT DEFAULT 0;
        DECLARE done INT DEFAULT 0;
        DECLARE cur CURSOR FOR SELECT from_entity FROM connections WHERE to_entity = nid;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
        
        OPEN cur;
        
        looping: LOOP
            FETCH cur INTO n;
            
            IF done = 1 THEN
                LEAVE looping;
            END IF;
            
            INSERT INTO __ancestors VALUES ( n );
            CALL get_ancestors_routine(n);
        END LOOP looping;
        CLOSE cur;
    END$$
    
CREATE PROCEDURE get_ancestor(IN nid INT, OUT n INT)
    BEGIN
        DECLARE r INT DEFAULT 0;
        DECLARE done INT DEFAULT 0;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
        
        SELECT from_entity
            FROM connections
            WHERE to_entity = nid INTO r;
        
        IF done = 0 THEN
            SET n = r;
        END IF;
    END$$
    
CREATE PROCEDURE get_children(IN nid INT)
    BEGIN
        DECLARE n INT;
        
        CREATE TEMPORARY TABLE __children(
            id INT NOT NULL PRIMARY KEY
        );

        SELECT COUNT(*)
            FROM connections
            WHERE from_entity = nid INTO n;

        IF n <> 0 THEN
            CALL get_children_routine(nid);
        END IF;
        
        SELECT entities.*
            FROM entities 
            JOIN __children 
            on entities.id = __children.id;
    END$$
   
CREATE PROCEDURE get_children_routine(IN nid INT)
    BEGIN
        DECLARE n INT DEFAULT 0;
        DECLARE done INT DEFAULT 0;
        DECLARE cur CURSOR FOR SELECT to_entity FROM connections WHERE from_entity = nid;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
        
        OPEN cur;
        
        looping: LOOP
            FETCH cur INTO n;
            
            IF done = 1 THEN
                LEAVE looping;
            END IF;
            
            INSERT INTO __children VALUES ( n );
            CALL get_children_routine(n);
        END LOOP looping;
        CLOSE cur;
    END$$
/*    
CREATE PROCEDURE get_data(IN parameter_name VARCHAR(64), IN parameter_value VARCHAR(64))
    BEGIN
        DECLARE start INT DEFAULT 1;
        DECLARE end_name INT DEFAULT 1;
        DECLARE end_value INT DEFAULT 1;
        DECLARE name VARCHAR(26) DEFAULT parameter_name;
        DECLARE value VARCHAR(26) DEFAULT parameter_value;
        
        SELECT INSTR(parameter_name,';') into end_name;
        SELECT INSTR(parameter_value,';') into end_value;
        
        SELECT SUBSTRING(name,1,end_name-1) into name;
        SELECT SUBSTRING(value,1,end_value-1)into value;
        
        SELECT LEFT('roseindia', 4);
        
        SET @stmt := 
            'SELECT * 
            FROM parameters p 
            WHERE ';
        
        SET @stmt := CONCAT(@stmt,'p.name = "', name, '" AND p.value = "', value, '" ');
        
        PREPARE select_param FROM @stmt;
        EXECUTE select_param;
        DEALLOCATE PREPARE select_param;
    END$$
*/   

CREATE PROCEDURE insert_param( IN namefield VARCHAR(40), IN valuefield VARBINARY(200))
BEGIN
    DECLARE l INT;
    DECLARE tabletype VARCHAR(10);
    DECLARE tablename VARCHAR(20);
    
    INSERT IGNORE INTO parameters(name) VALUES ( namefield );
    
    SELECT type 
    FROM optionDB.options_parameter 
    WHERE name = BINARY namefield
    INTO tabletype;
    
    IF LAST_INSERT_ID() = 0 THEN
        SELECT id FROM parameters WHERE name = namefield INTO l;
    ELSE
        SELECT LAST_INSERT_ID() INTO l;
    END IF;
    
    IF strcmp(tabletype, 'STRING') = 0 THEN 
        SET tablename = 'string_parameters';
    ELSEIF strcmp(tabletype, 'INT') = 0 THEN 
        SET tablename = 'int_parameters';
    ELSEIF strcmp(tabletype, 'DOUBLE') = 0 THEN 
        SET tablename = 'double_parameters';        
    ELSEIF strcmp(tabletype, 'BOOL') = 0 THEN 
        SET tablename = 'bool_parameters';        
    ELSEIF strcmp(tabletype, 'DATETIME') = 0 THEN 
        SET tablename = 'datetime_parameters';        
    ELSEIF strcmp(tabletype, 'DATE') = 0 THEN 
        SET tablename = 'date_parameters';        
    ELSEIF strcmp(tabletype, 'TIME') = 0 THEN 
        SET tablename = 'time_parameters'; 
    END IF;
    
    SET @sql = CONCAT('INSERT IGNORE INTO ', tablename, ' (id,value)',
        'VALUES(', l, ',''', valuefield, ''')');  # use ID in second table
    PREPARE stmt FROM @sql;
    EXECUTE stmt;
    DROP PREPARE stmt;


END$$

CREATE PROCEDURE fail(IN message VARCHAR(128))
    BEGIN
        
        DECLARE a INT;
           
        SELECT message
        FROM entities
        WHERE entities.id= 0
        INTO a ;
            
    END$$
    
CREATE TRIGGER update_modified_with_parameter
        AFTER INSERT ON parameterlist FOR EACH ROW
    BEGIN
        DECLARE b INT DEFAULT 0;
        DECLARE a DATETIME;
        DECLARE done INT DEFAULT 0;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;
        
        SET a = CURRENT_TIMESTAMP;
            
        UPDATE entities
            SET  modified = a
            WHERE id = NEW.entity_id;
            
        CALL get_ancestor(NEW.entity_id,b);
        
        UPDATE entities
            SET  modified = a
            WHERE id = b;
    END$$
    
CREATE TRIGGER update_modified_with_connections
        AFTER INSERT ON connections FOR EACH ROW
    BEGIN
    
        DECLARE a DATETIME;
        DECLARE b INT;
        
        SELECT modified
            FROM entities e
            WHERE id = NEW.to_entity
            INTO a;
        
        CALL get_ancestor(NEW.to_entity,b);
            
        UPDATE entities
            SET  modified = a
            WHERE id = b;
    END$$
  
CREATE TRIGGER insert_parameter
        BEFORE INSERT ON parameters FOR EACH ROW
    BEGIN
        
        IF (SELECT COUNT(*) FROM optionDB.options_parameter o
        WHERE  NEW.name = BINARY o.name) = 0 THEN
            
            CALL fail(CAN_NOT_INSERT_PARAMETER);
             
        END IF;
    END$$
    
   
    
DELIMITER ;
    