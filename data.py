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


def insert_bottle_table():
    bottle_table_sql = """
                CREATE TABLE bottles (
                    bottle_id SERIAL PRIMARY KEY,
                    homie_fb_id BIGINT,
                    bottle_name VARCHAR(255) NOT NULL,
                    bottle_size INT,
                    num_drinks INT,
                    UNIQUE (homie_fb_id, bottle_name)
                    )"""
    execute_statement(bottle_table_sql)

def insert_homie_table():
    homie_table_sql = """
            CREATE TABLE homies (
            homie_fb_id BIGINT PRIMARY KEY,
            homie_name VARCHAR(255) NOT NULL,
            curr_bottle_id INT
            )"""
    execute_statement(homie_table_sql)
        

def insert_drink_table():
    drink_table_sql = """
            CREATE TABLE drinks (
                index SERIAL PRIMARY KEY,
                homie_fb_id BIGINT,
                drink_time TIMESTAMP DEFAULT NOW(),
                bottle_id INT
            )"""
    
    execute_statement(drink_table_sql)

def delete_last_drink(homie_fb_id):
    drink_entry = execute_statement("SELECT * FROM drinks WHERE index=(SELECT MAX(index) FROM drinks WHERE homie_fb_id = %s);", args=(homie_fb_id,), ret=True)
    bottle_id = drink_entry[0][3]
    delete_drink_sql = """DELETE FROM drinks
    WHERE index=(SELECT MAX(index) FROM drinks WHERE homie_fb_id = %s)"""
    execute_statement(delete_drink_sql, (homie_fb_id,))
    execute_statement("UPDATE bottles set num_drinks = num_drinks-1 WHERE homie_fb_id = %s AND bottle_id = %s;", args=(homie_fb_id, bottle_id))




def insert_drink(homie_fb_id, bottle_name=None):
    if bottle_name is None:
        # Fetches current bottle selected by user
        homie_entry = execute_statement("SELECT * FROM homies WHERE homie_fb_id = %s;", args=(homie_fb_id,), ret=True)
        bottle_id = homie_entry[0][2]
    else:
        bottle_entry = execute_statement("SELECT * FROM bottles WHERE homie_fb_id = %s AND bottle_name = %s;", args=(homie_fb_id, bottle_name), ret=True)
        bottle_id = bottle_entry[0][0]

    # Adds a drink event with the currently selected bottle id
    add_drink_sql = """INSERT INTO drinks (homie_fb_id, bottle_id) VALUES(%s, %s);"""
    execute_statement(add_drink_sql, (homie_fb_id, bottle_id))
    # Updates the total number of drink events logged by that bottle
    execute_statement("UPDATE bottles set num_drinks = num_drinks+1 WHERE homie_fb_id = %s AND bottle_id = %s;", args=(homie_fb_id, bottle_id))

def insert_homie(homie_fb_id, homie_name):
    insert_bottle("NULL", "0", homie_fb_id)
    bottle_entry = execute_statement("SELECT * FROM bottles WHERE homie_fb_id = %s AND bottle_name = %s;", args=(homie_fb_id, "NULL"), ret=True)
    bottle_id = bottle_entry[0][0]
    new_homie_sql = """INSERT INTO homies (homie_fb_id, homie_name, curr_bottle_id) VALUES(%s, %s, %s);"""
    execute_statement(new_homie_sql, args=(homie_fb_id, homie_name, bottle_id))

def get_drinks():
    try:
        all_drinks = execute_statement("SELECT * FROM drinks;", ret=True)
    except:
        raise
    return(all_drinks)

def switch_bottle(name, homie_fb_id):
    try:
        bottle_entry = execute_statement("SELECT * FROM bottles WHERE homie_fb_id = %s AND bottle_name = %s;", args=(homie_fb_id, name), ret=True)
        bottle_id = bottle_entry[0][0]
        execute_statement("UPDATE homies set curr_bottle_id = %s WHERE homie_fb_id = %s;", args=(bottle_id, homie_fb_id))
    except:
        raise

def get_bottle(homie_fb_id):
    try:
        bottle_entry = execute_statement("SELECT curr_bottle_id from homies where homie_fb_id = %s;", args=(homie_fb_id), ret=True)
        return bottle_entry[0][0]
    except:
        raise

def insert_bottle(name, size, homie_fb_id):
    new_bottle_sql = """INSERT INTO bottles (homie_fb_id, bottle_name, bottle_size, num_drinks) VALUES(%s, %s, %s, %s);"""
    return execute_statement(new_bottle_sql, [homie_fb_id, name, size, 0])
    
def delete_bottle(name, homie_fb_id):
    bottle_entry = execute_statement("SELECT * FROM bottles WHERE homie_fb_id = %s AND bottle_name = %s;", args=(homie_fb_id, name), ret=True)
    bottle_id = bottle_entry[0][0]
    execute_statement("DELETE FROM drinks WHERE bottle_id = %s;", args=(bottle_id,))
    
    homie_entry = execute_statement("SELECT * FROM homies WHERE homie_fb_id = %s;", args=(homie_fb_id,), ret=True)
    if homie_entry[0][2] == bottle_id:
        switch_bottle("NULL", homie_fb_id)
    delete_bottle_sql = """DELETE FROM bottles WHERE bottle_name = %s AND homie_fb_id = %s;"""
    return execute_statement(delete_bottle_sql, [name, homie_fb_id])

def get_bottle_stats(homie_fb_id):
    try:
        results = execute_statement("SELECT bottle_name, bottle_size, num_drinks FROM bottles WHERE homie_fb_id = %s", args=(homie_fb_id,), ret=True)
    except:
        raise
    return(results)

def get_bottle_ids(homie_fb_id):
    results = execute_statement("SELECT bottle_id, bottle_size FROM bottles WHERE homie_fb_id = %s", args=(homie_fb_id,), ret=True)
    return results

def get_homie_events_over_time(homie_fb_id, time_string):
    results = execute_statement("SELECT bottle_id FROM drinks WHERE homie_fb_id = %s AND drink_time > now() - interval %s;", args=(homie_fb_id, time_string), ret=True)
    return results

def get_homie_list():
    results = execute_statement("SELECT homie_fb_id, homie_name FROM homies;", ret=True)
    return results

def execute_statement(sql, args=False, ret=False):
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
        if ret:
            results = cur.fetchall()
        else:
            results = None
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        raise
    finally:
        if conn is not None:
            conn.close()
    return results


#insert_bottle_table()
#insert_homie_table()
#insert_drink_table()
