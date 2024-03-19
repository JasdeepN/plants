from db import create_connection
import logging

logger = logging.getLogger(__name__)

def drop_table(conn):
  logger.warning("TABLES ARE ABOUT TO BE DROPPED LAST CHANCE TO BACK OUT")
  print("TABLES ARE ABOUT TO BE DROPPED LAST CHANCE TO BACK OUT")
  if input("are you sure? (y/n)") != "y":
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    cursor.execute("DROP TABLE IF EXISTS SENSOR_READINGS")
    cursor.execute("DROP TABLE IF EXISTS PUMPS")
    conn.commit();
    print("Tables dropped.")
    logger.warning('Y - TABLES DROPPED')
  else:
    print("That was close.")
    logger.warning("N - ABORTED TABLE DROP.")


def create_table(conn):
  logger.info("CREATING TABLES")
  cursor = conn.cursor()
  #Creating table
  logger.info("CREATING NEW TABLES")
  logger.info("Attempting create table SENSOR_READINGS")

  table = '''CREATE TABLE SENSOR_READINGS (
            id INT NOT NULL AUTO_INCREMENT,
            time DATETIME NOT NULL,
            temp DOUBLE NULL,
            humidity DOUBLE NULL,
            pressure DOUBLE NULL,
            gas_resistance DOUBLE NULL,
            aq_calculated DOUBLE NULL,
            soil_1 ENUM('disconnected', 'error 1', 'error 2', 'dry', 'watered', 'wet') DEFAULT 'disconnected',
            soil_2 ENUM('disconnected', 'error 1', 'error 2', 'dry', 'watered', 'wet') DEFAULT 'disconnected',
            soil_3 ENUM('disconnected', 'error 1', 'error 2', 'dry', 'watered', 'wet') DEFAULT 'disconnected',
            soil_4 ENUM('disconnected', 'error 1', 'error 2', 'dry', 'watered', 'wet') DEFAULT 'disconnected',
            eCO2 DOUBLE NULL,
            TVOC DOUBLE NULL,
            PRIMARY KEY (id)  
          ); ''' 
  cursor.execute(table)

  logger.info("SENSOR_READINGS table created successfully")

  logger.info("Attempting create table PUMPS")
  table_pump = ''' CREATE TABLE PUMPS (
            id INTEGER NOT NULL AUTO_INCREMENT,
            pump_id INT NOT NULL, 
            time DATETIME NOT NULL,
            method BOOLEAN NOT NULL,
            PRIMARY KEY (id)
            ); ''' 

  cursor.execute(table_pump)
  conn.commit();
  logger.info("PUMPS table created successfully")

  print("Tables are Ready")

def run():   
  conn = create_connection()

  drop_table(conn)
  create_table(conn)

  conn.close()

print("WARNING THIS WILL DROP ALL TABLES AND RECREATE BASED ON SCHEMA")
if input("are you sure? (y/n)") != "y":
    
    exit()
# run();
print("Your Tables are gone.")