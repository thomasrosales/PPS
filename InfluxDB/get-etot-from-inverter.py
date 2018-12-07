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
import datetime
import time
import sys
import os

def get_total_energy_data_influx():
    '''
    Get the total value of the last energy in influxdb.

    It is connected to influxdb and the query 
    is executed to obtain the last value of 
    the total energy of the previous day.

    Returns
    -------
    int
        Returns 0 if the query fails 
        Returns etot if the query is successful
    '''
    try:

        user = 'mfv'
        password = 'mfv18!'
        dbname = 'mfv'
        host = 'influxdb.linti.unlp.edu.ar'
        port = 443
        ssl = True

        etot_aux = 0

        client = InfluxDBClient(host, port, user, password, dbname, ssl)

        yesterday = datetime.datetime.now().replace(microsecond=0, second=59, minute=59, hour=23) - datetime.timedelta(1)
        
        print yesterday

        yesterday = int(time.mktime(time.strptime(str(yesterday),'%Y-%m-%d %H:%M:%S')))*1000000000

        print yesterday

        result = client.query('''select etot from Inverter where "id" = '4' and time <= '''  
            + str(yesterday) 
            + ''' order by time desc limit 1;''')

        results = list(result.get_points(measurement='Inverter'))

        for item in results:
            etot_aux = float(item['etot'])
	    
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print 'Error:', e
    

    return etot_aux

# MAIN
if __name__ == "__main__":
    print ('El valor de etot es: ', get_total_energy_data_influx())
