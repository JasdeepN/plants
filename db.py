import mysql.connector
from mysql.connector import Error
import atexit

# filename to form database 
# file = "/home/admin/plants/db/sensor.db"

def create_connection():
  """ create a database connection to the SQLite database
      specified by the db_file
  :param db_file: database file
  :return: Connection object or None
  """
  conn = None
  try:
    conn = mysql.connector.connect(host='localhost',
                                         database='sensor',
                                         user='env-monitor',
                                         password='password')
    if conn.is_connected():
        db_Info = conn.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = conn.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)

  except Error as e:
    print("Error while connecting to MySQL", e)


  return conn


def select_all_tables(conn):
    """
    Query all rows in the tasks table
    :param conn: the Connection object
    :return:
    """
    conn.reconnect()
    cursor.execute("SELECT * FROM sqlite_schema WHERE type='table'")

    rows = cursor.fetchall()

    for row in rows:
        print(row, "\n")
 
def drop_table(conn):
  cursor.execute("SET FOREIGN_KEY_CHECKS=0")
  cursor.execute("DROP TABLE IF EXISTS SENSOR_READINGS")
  cursor.execute("DROP TABLE IF EXISTS PUMPS")


def create_table(conn):
  conn.reconnect()
  #Creating table
  table = ''' CREATE TABLE SENSOR_READINGS (
            id INT NOT NULL AUTO_INCREMENT,
            time DATETIME NOT NULL,
            temp DOUBLE NULL,
            humidity DOUBLE NULL,
            pressure DOUBLE NULL,
            gas_resistance DOUBLE NULL,
            aq_calculated DOUBLE NULL,
            soil_1 ENUM('error', 'dry', 'watered', 'wet') DEFAULT 'error',
            soil_2 ENUM('error', 'dry', 'watered', 'wet') DEFAULT 'error',
            soil_3 ENUM('error', 'dry', 'watered', 'wet') DEFAULT 'error',
            soil_4 ENUM('error', 'dry', 'watered', 'wet') DEFAULT 'error',
            eCO2 INT NULL,
            TVOC INT NULL,
            PRIMARY KEY (id)
          ); ''' 
  cursor.execute(table)

 

  table_pump = ''' CREATE TABLE PUMPS (
            id INTEGER NOT NULL AUTO_INCREMENT,
            pump_id INT NOT NULL, 
            time DATETIME NOT NULL,
            method BOOLEAN NOT NULL,
            PRIMARY KEY (id)
            ); ''' 

  cursor.execute(table_pump)

  print("Tables are Ready")


def get_all_rows(table=None, limit="" , order=""):
  _order = ""
  _limit = ""

  conn.reconnect()
  if table is None: return;
  if order is not "":
   _order = " ORDER BY " + order

  if limit is not "":
    _limit = " LIMIT " + limit  
  print("read db")
  query = "SELECT * FROM "+table+ _order + _limit + ";"
  cursor.execute(query)
  result = cursor.fetchall()
  return result

def insert_data_from_pump(time, pump_data=[]):
  conn.reconnect()
  # conn = create_connection();
 
  cursor.execute( "INSERT INTO PUMPS(time, pump_id, method) VALUES (%s, %s, %s)", (time, pump_data[0], pump_data[1]))

  conn.commit();

  # insert_data(sensor_data[0], sensor_data[1], sensor_data[2], sensor_data[3], sensor_data[4], sensor_data[5], sensor_data[6], sensor_data[7], sensor_data[8]);

  
def insert_data(temp, humidity, pressure, gas_resistance=None, aq_calculated=None, eCO2=0, tvoc=0, sensor1=None, sensor2=None, sensor3=None, sensor4=None, time=None):
  conn.reconnect()
  print('insert @ ', time)
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


  print(">>>>>SELECT * FROM " + table + where + modifier)
  
  query = "SELECT * FROM " + table + where + modifier
  cursor.execute(query)


  result = cursor.fetchall()

  return result

def cleanup():
  cursor.close()
  conn.close()
  print('closed connections')


def run():   
  conn = create_connection()
  # cursor object
  drop_table(conn)
  create_table(conn)
  # select_all_tables(conn)
  # data = get_all_rows(conn)
  # print(data)
  # Close the connection
  conn.close()

def exit_handler():
    cleanup();

conn = create_connection();
cursor = conn.cursor(buffered=True);
atexit.register(exit_handler)

# run();
