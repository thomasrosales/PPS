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

import argparse

from influxdb import InfluxDBClient


def main():
    """Instantiate a connection to the InfluxDB."""
    user = 'user'
    password = 'password'
    dbname = 'dbname'
    ssl = True
    host='ip-host-server'
    port = 443
    #dbuser_password = 'my_secret_password'
   

    client = InfluxDBClient(host, port, user, password, dbname,ssl)

    dbs = client.get_list_database()

    measurements = client.get_list_measurements()

    users = client.get_list_users()

    print("La base de datos es: ", dbs)

    print("Todas las medidas son:", measurements)

    print("Los usuarios son: ", user)


if __name__ == '__main__':
    main()
