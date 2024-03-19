import mysql.connector
from mysql.connector import Error
import atexit
import sqlvalidator

import os
from dotenv import load_dotenv
import logging 
from common import *

logger = logging.getLogger(__name__)
load_dotenv()

DEBUG = os.getenv('DEBUG')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')


# class SQL_QUERY(Exception):
#     pass

def create_connection():
  global conn
  global cursor
  """ create a database connection to the SQLite database
      specified by the db_file
  :param db_file: database file
  :return: Connection object or None
  """
  logger.info("Create DB connection")
  try:
    conn = mysql.connector.connect( host=DB_HOST,
                                    database=DB_NAME,
                                    user=DB_USER,
                                    password=DB_PASSWORD )

    if conn.is_connected():
        db_info = conn.get_server_info()
        logger.info("Connected to MySQL Server version %s", db_info)
        cursor = conn.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        logger.info("You're connected to database: %s", record)

  except Error as e:
    logger.error(e)
    raise LoggedException(logger, "Error while connecting to MySQL")
  return conn

def get_all_rows(table=None, limit="" , order=""):
  global conn
  global cursor
  _order = ""
  _limit = ""

  if table is None: raise LoggedException("table cannot be empty in query")
  
  conn.reconnect()
  if order != "":
   _order = " ORDER BY " + order

  if limit != "":
    _limit = " LIMIT " + limit  
  
  logger.info("read db")
  query = "SELECT * FROM "+ table + _order + _limit + ";"
  cursor.execute(query)
  result = cursor.fetchall()
  return result

def insert_data_from_pump(time, pump_data=[]):
  global conn
  global cursor
  conn.reconnect()
  # conn = create_connection();
  cursor.execute( "INSERT INTO PUMPS(time, pump_id, method) VALUES (%s, %s, %s)", (time, pump_data[0], pump_data[1]))
  conn.commit();

def queryBuidler(query=None, table=None, selector="*", where=None, limit=None, order=None):
  if query is None:
    logger.info('bulding query from ', table, selector, limit, order)
    if table is None: raise LoggedException("table cannot be empty in query")
    query = "SELECT " + selector + " FROM " + table

    if where != None:
      query += " WHERE " + str(where) 

    if order != None:
      query += " ORDER BY " + str(order)

    if limit != None:
      query += " LIMIT " + str(limit) 

    query += ";"
  
  formatted_sql = sqlvalidator.format_sql(query)
  test = sqlvalidator.parse(formatted_sql)
  if not test.is_valid():
    logger.error('invalid SQL was generated, did not pass test.', query)
    raise LoggedException(test.errors)
 
  return formatted_sql;

def query(query=None, table=None, selector="*", limit=None, order=None):
  global conn
  global cursor
  if query is None:
    _query = queryBuidler(table, selector, limit, order)
  else:
    _query = queryBuidler(query)
  conn.reconnect()
  cursor.execute(_query)
  result = cursor.fetchall()

  return result
  
def insert_data(temp, humidity, pressure, gas_resistance=None, aq_calculated=None, eCO2=0, tvoc=0, sensor1=None, sensor2=None, sensor3=None, sensor4=None, time=None):
  global conn
  global cursor
  conn.reconnect()
  logger.info('insert @ ', time)
  if time is None: return;
  cursor.execute( "INSERT INTO SENSOR_READINGS(time, temp, humidity, pressure, gas_resistance, aq_calculated, soil_1, soil_2, soil_3, soil_4, eCO2, TVOC) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (time, temp,  pressure, humidity, gas_resistance, aq_calculated, sensor1, sensor2, sensor3, sensor4, eCO2, tvoc))
  conn.commit();

def getRows(rows, table, where=None, modifier=None):
  conn.reconnect()
  timespace = {
     "latest": " ORDER BY time DESC LIMIT " + str(rows) + " ",
     "newest": "",
     None: ""
  }
  
  if where != None:
    where = " WHERE "+ where
  else: 
    where = ""

  modifier = timespace[modifier]

  logger.info("SELECT * FROM " + table + where + modifier)
  
  query = "SELECT * FROM " + table + where + modifier
  cursor.execute(query)

  result = cursor.fetchall()

  return result

def cleanup():
  global conn
  global cursor
  try:
    cursor.close()
    conn.close()
    logger.info('Closed DB connections')
  except:
    pass
  
def exit_handler():
    cleanup();


# conn = create_connection();


atexit.register(exit_handler);

