DROP database test;

CREATE database test;

use test;


CREATE TABLE params
    (
    id    INT NOT NULL AUTO_INCREMENT,
    name   VARCHAR(20) UNIQUE NOT NULL,
    PRIMARY KEY (id) 
    )
    ENGINE=InnoDB;
    
CREATE table str_params
    (
    id    INT NOT NULL,
    value   VARCHAR(20) NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES params(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE table int_params
    (
    id    INT NOT NULL,
    value   INT(20) NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES params(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE table datetime_params
    (
    id    INT NOT NULL,
    value   DATETIME NOT NULL,
    PRIMARY KEY (id, value),
    CONSTRAINT FOREIGN KEY (id) REFERENCES params(id) ON DELETE CASCADE ON UPDATE CASCADE
    )
    ENGINE=InnoDB;

CREATE OR REPLACE VIEW v AS 
        SELECT name, id, value 
        FROM params join int_params using (id) 
    UNION 
        SELECT name, id, value
        FROM params join str_params using (id) 
    UNION 
        SELECT name, id, value  
        FROM params join datetime_params using (id) 
    order by id;
    
DELIMITER $$
CREATE PROCEDURE insert_param(IN tablename VARCHAR(23), IN namefield VARCHAR(23), IN valuefield VARBINARY(23))
BEGIN
    DECLARE l INT;
    
    INSERT IGNORE INTO params(name) VALUES ( namefield );
    IF LAST_INSERT_ID() > 0 THEN
        SET @sql = CONCAT('INSERT IGNORE INTO ', tablename ,'(id, value) ',
            'VALUES (LAST_INSERT_ID(), ''', valuefield, ''')');  # use ID in second table
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DROP PREPARE stmt;
    ELSE 
        SELECT id FROM params WHERE name = namefield INTO l;
        
        SET @sql = CONCAT('INSERT IGNORE INTO ', tablename, ' (id,value)',
            'VALUES(', l, ',''', valuefield, ''')');  # use ID in second table
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DROP PREPARE stmt;
    END IF;

END$$

DELIMITER ;
   
    

CALL  insert_param('str_params', 'prename', 'Mya');
CALL  insert_param('str_params','lastname', 'Luls');
CALL  insert_param('str_params','address', 'Here');
CALL  insert_param('datetime_params','married', current_timestamp);
CALL  insert_param('int_params','children', 2);


SELECT * from v;

 /*
INSERT INTO params(name)
    VALUES('intname');         # generate ID by inserting NULL
INSERT INTO int_params (id,value)
    VALUES(LAST_INSERT_ID(),1);  # use ID in second table
 
INSERT INTO params(name)
    VALUES('intname');         # generate ID by inserting NULL
INSERT INTO int_params (id,value)
    VALUES(LAST_INSERT_ID(),2);  # use ID in second table

INSERT INTO params(name)
    VALUES('datetime2name');         # generate ID by inserting NULL
INSERT INTO datetime_params (id,value)
    VALUES(LAST_INSERT_ID(),CURRENT_TIMESTAMP);  # use ID in second table

CREATE OR REPLACE VIEW w AS    
    SELECT params.name, params.id, cast(int_params.value as unsigned) as value          
    FROM params join int_params using (id)
    order by id;

CREATE OR REPLACE VIEW w2 AS    
    SELECT params.name, params.id, cast(str_params.value as char) as value          
    FROM params join str_params using (id)
    order by id;
  
Select * from v;


INSERT INTO params(name)
    VALUES('strname2');         # generate ID by inserting NULL
INSERT INTO str_params (id,value)
    VALUES(LAST_INSERT_ID(),(SELECT value from v where id=1));  # use ID in second table
 


CREATE OR REPLACE VIEW w AS 
    Select * from params as p left join int_params as i using (id)
    left join str_params as s using (id);
order by id;

print self._execute_query("Select * from params as p left join int_params as i using (id) "
                                    "left join str_params as s using (id)"
                                    "left join datetime_params as d using (id);")
        print self._execute_query("""    SELECT * 
                                        FROM params join str_params using (id) 
                                    UNION 
                                        SELECT * 
                                        FROM params join int_params using (id) 
                                    """)
        print self._execute_query("Select * from int_params;")
((6L, '1', None, None, None), (9L, 'intnaame', None, None, None), (7L, 'intname', None, None, None), (8L, 'intnamee', None, None, None), (10L, 'intnamme', 1L, 'tst', None), (10L, 'intnamme', 1L, 'tsts', None), (10L, 'intnamme', 10L, 'tst', None), (10L, 'intnamme', 10L, 'tsts', None), (12L, 'intnammee', None, None, None), (11L, 'intnammme', None, 'tsts', None), (13L, 'intneamme', None, 'tsst', None), (1L, 'strname', None, 'tex2t', None), (1L, 'strname', None, 'text', None), (2L, 'strname2', None, 'tex2t', None), (3L, 'strname3', None, None, None), (4L, 'strname4', None, None, None), (5L, 'strname5', None, None, None))
((1L, 'strname', 'tex2t'), (1L, 'strname', 'text'), (2L, 'strname2', 'tex2t'), (10L, 'intnamme', 'tst'), (10L, 'intnamme', 'tsts'), (11L, 'intnammme', 'tsts'), (13L, 'intneamme', 'tsst'), (10L, 'intnamme', '1'), (10L, 'intnamme', '10'))
((10L, 1L), (10L, 10L))

*/