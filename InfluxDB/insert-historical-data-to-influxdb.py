#!/usr/bin/python3.7

#######################################################
## Inverters monitorings of the Facultad de Informatica
#######################################################
## Author: Rosales, Tomas
## Copyright: Copyright 2018, MFV
## Version: 1.0 Release
## Mmaintainer: Facultad de Informatica
## Email: trosales@linti.unlp.edu.ar
## Status: production
#######################################################

import os
import calendar
import influxdb
import time
import datetime
import csv
import sys

def migrationToInfluxDB(rootDir):
    for dirName, subdirList, fileList in os.walk(rootDir):
        print('Directorio encontrado: %s' % dirName)
        for fname in fileList:
            print(fname)
            extend = fname.split(".")
            inversor = extend[0].split(' ')
            
            id_inverter = int(inversor[1])

            if extend[1] == 'csv':
                file = dirName + '/' + fname
                
                with open(file, mode='r', buffering=-1) as csvfile:
                    reader = csv.DictReader(csvfile)

                    #for row in file.readlines():
                    for row in reader:
                        print(row)

                        date_hour = row['Time'].strip()
                        
                        old_time = int(time.mktime(time.strptime(date_hour,'%Y/%m/%d %H:%M:%S')))*1000000000

                        print(old_time)
        
                        temp = float(row['Temp'])
                        vdc = float(0.0)
                        iac = float(row['Iac(A)'])
                        vac = float(row['Vac(V)'])
                        freq = float(row['Fac(Hz)'])
                        pinst = float(0.0)
                        etot = float(row['E-Total(kWh)'])
                        wtime = float(row['E-Today(kWh)'])
                        modo = float(0.0)
                        vdc_1 = float(row['Vpv1(V)'])
                        vdc_2 = float(row['Vpv2(V)'])
                        vdc_3 = float(row['Vpv3(V)'])
                        pinst = float(0.0)


                        user = 'user'
                        password = 'password'
                        dbname = 'dbname'
                        host = 'ip-host-server'
                        port = 443
                        ssl = True

                        try:
                            client = influxdb.InfluxDBClient(host, port, user, password, dbname, ssl)

                            json_body = [
                            {
                                "measurement": "Inverter",
                                "tags": {
                                    "id": id_inverter,
                                },
                                #The maximum timestamp is 9223372036854775806 or 2262-04-11T23:47:16.854775806Z. 
                                #The minimum timestamp is -9223372036854775806 or 1677-09-21T00:12:43.145224194Z.
                                #"time": "2009-11-10T23:00:00Z"

                                "time": old_time,
                                "fields":  {
                                    "temp": temp,
                                    "vdc": vdc,
                                    "vdc_1":vdc_1,
                                    "vdc_2":vdc_2,
                                    "vdc_3":vdc_3,
                                    "iac": iac,
                                    "vac": vac,
                                    "freq": freq,
                                    "pinst": pinst,
                                    "etot": etot,
                                    "wtime": wtime,
                                    "modo" : modo,
                                    "pinst": pinst
                                }
                            }
                            ]
                            client.write_points(json_body)
                            print ('Ok: connection sucessful to database')
                        except Exception as e:
                            print ('Error: Failed to connect to database: ', e)
    return 0

if __name__ == "__main__":
    #direccion de la carpeta con los archivos historicos
    rootDir = '/home/linti/Escritorio/historical_datas_inverter'
    print (rootDir)
    migrationToInfluxDB(rootDir)
