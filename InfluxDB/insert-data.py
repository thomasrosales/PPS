#!/usr/bin/python

#######################################################
## InfluxDB Test of the Facultad de Informatica
#######################################################
## Author: Rosales, Tomas
## Copyright: Copyright 2018, MFV
## Version: 1.0 Release
## Mmaintainer: Facultad de Informatica
## Email: trosales@linti.unlp.edu.ar
## Status: production
#######################################################

from influxdb import InfluxDBClient
from random import randint
import logging
import time

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')



def setupLogger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create a file handler
    handler = logging.FileHandler(log_file)
    handler.setLevel(level)

    # create a logging format
    handler.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(handler)

    logger.info('Finish configuration login.')

    return logger


def insertIntoInfluxDB(id,vdc,iac,vac,freq,pinst,etot):
    
    logger_influxdb = setupLogger("influxdb_logger","influxdb_login.log")


    #if the db is not found, then to create it
    try:
        error = "no hay error"
        user = 'user'
    	password = 'password'
    	dbname = 'dbname'
    	host = 'ip-host-server'
    	port = 8086

        client = InfluxDBClient(host, port, user, password, dbname)

        #client.switch_database('MFV')
        logger_influxdb.info('Start connect to database')

        json_body = [
        {
            "measurement": "Inverter",
            "tags": {
                "id": id,
                
            },
            "fields":  {
                "vdc": vdc,
                "iac": iac,
                "vac": vac,
                "freq": freq,
                "pinst": pinst,
                "etot": etot
            }
        }
        ]

        logger_influxdb.debug('Insert data', json_body)
        client.write_points(json_body)
        logger_influxdb.info('Finish inserting data')
    
    except Exception as e:
        error = "hay error"
        logger_influxdb.error('Failed to connect to database: %s', e, exc_info=False)

    return error

while True:
    num1 = randint(0,50)
    num2 = randint(0,50)
    num3 = randint(0,50)
    num4 = randint(0,50)
    num5 = randint(0,50)
    num6 = randint(0,50)
    
    
    print "insertIntoInfluxDb"
    error = insertIntoInfluxDB(1,num1,num2,num3,num4,num5,num6)
    print error
    time.sleep(10)
    