from urllib import parse
from configparser import ConfigParser
import psycopg2
import os
import sys

def config(filename=sys.path[0]+'/config.ini', section='postgresql'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)
 
    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    elif os.environ['POST_USER']:
        db['host'] = os.environ['POST_HOST']
        db['database'] = os.environ['POST_DATABASE']
        db['user'] = os.environ['POST_USER']
        db['password'] = os.environ['POST_PASSWORD']
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    return db

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()
 
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
 
        # create a cursor
        cur = conn.cursor()
        
 # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')
 
        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)
       
     # close the communication with the PostgreSQL
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')

# (For reference and if I blow up prod db :yikes:)
def insert_tables():
    command1 = """
            CREATE TABLE drink_stats (
                index SERIAL PRIMARY KEY,
                homie_fb_id BIGINT,
                drink_time TIMESTAMP DEFAULT NOW()
            )"""
    command2 = """
            CREATE TABLE homie_stats (
                homie_fb_id BIGINT PRIMARY KEY,
                homie_name VARCHAR(255) NOT NULL,
                homie_drink_size INT,
                num_drinks INT
            )"""
    execute_statement(command1)
    execute_statement(command2)


def delete_last_drink(homie_fb_id):
    delete_drink_sql = """DELETE FROM drink_stats 
    WHERE index=(SELECT MAX(index) FROM drink_stats WHERE homie_fb_id = %s)"""
    execute_statement(delete_drink_sql, (homie_fb_id,))

def execute_statement(sql, args=False):
    conn = None
    try:
        # read database configuration
        params = config() # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute insert statement
        if args:
            cur.execute(sql, args)
        else:
            cur.execute(sql)
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def insert_drink(homie_fb_id):
    add_drink_sql = """INSERT INTO drink_stats (homie_fb_id) VALUES(%s);"""
    execute_statement(add_drink_sql, (homie_fb_id,))

def zero_homie():
    new_homie_sql = "UPDATE homie_stats SET num_drinks = 0;"
    execute_statement(new_homie_sql)

def decrement_homie(homie_id):
    new_homie_sql = "UPDATE homie_stats SET num_drinks = num_drinks-1 WHERE homie_fb_id = %s;"
    execute_statement(new_homie_sql, (homie_id,))

def increment_homie(homie_id):
    new_homie_sql = "UPDATE homie_stats SET num_drinks = num_drinks+1 WHERE homie_fb_id = %s;"
    execute_statement(new_homie_sql, (homie_id,))

def update_homie(homie):
    new_homie_sql = """UPDATE homie_stats
                        SET homie_drink_size = %s
                        WHERE homie_fb_id = %s"""
    execute_statement(new_homie_sql, (homie[2], homie[0]))

def insert_homie(homie):
    new_homie_sql = """INSERT INTO homie_stats (homie_fb_id, homie_name, homie_drink_size, num_drinks) VALUES(%s, %s, %s, %s);"""
    execute_statement(new_homie_sql, homie)

def get_drinks():
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT * FROM drink_stats;")
        all_drinks = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        return False
    finally:
        if conn is not None:
            conn.close()
    return(all_drinks)


def get_homies():
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        cur.execute("SELECT homie_fb_id, homie_name, homie_drink_size, num_drinks FROM homie_stats;")
        homie_table = cur.fetchall()

        print(homie_table)
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error in getting homie table, 90 percent chance its monday(?) and no one... drank(?): {}".format(error))
        return False
    finally:
        if conn is not None:
            conn.close()

    return(homie_table)


