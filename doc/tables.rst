Database Format
===============

PostgreSQL database dump:

.. code-block:: sql

    CREATE TABLE contexts (
        entity_id integer NOT NULL,
        connected_id integer NOT NULL,
        connection_type character varying(500)
    );

    CREATE TABLE data (
        id integer NOT NULL,
        entity_id integer NOT NULL,
        key character varying(40),
        mimetype character varying(40)
    );

    CREATE TABLE data_chunks (
        id integer NOT NULL,
        data_id integer NOT NULL,
        index integer,
        data bytea NOT NULL,
        length integer
    );

    CREATE TABLE entities (
        id integer NOT NULL,
        type character varying(60),
        uuid uuid,
        parent_id integer
    );

    CREATE TABLE parameter_declarations (
        entity_name character varying(60) NOT NULL,
        parameter_name character varying(40) NOT NULL,
        parameter_type character varying(40)
    );

    CREATE TABLE parameters (
        id integer NOT NULL,
        entity_id integer NOT NULL,
        name character varying(40),
        type character varying(20) NOT NULL
    );

    CREATE TABLE parameters_boolean (
        id integer NOT NULL,
        value boolean
    );

    CREATE TABLE parameters_date (
        id integer NOT NULL,
        value date
    );

    CREATE TABLE parameters_datetime (
        id integer NOT NULL,
        value timestamp without time zone
    );

    CREATE TABLE parameters_float (
        id integer NOT NULL,
        value double precision
    );

    CREATE TABLE parameters_integer (
        id integer NOT NULL,
        value integer
    );

    CREATE TABLE parameters_string (
        id integer NOT NULL,
        value character varying(40)
    );

    CREATE TABLE parameters_time (
        id integer NOT NULL,
        value time without time zone
    );


