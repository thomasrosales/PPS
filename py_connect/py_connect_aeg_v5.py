#!/usr/bin/python

#######################################################
## Inverters monitorings of the Facultad de Informatica
#######################################################
## Author: Rosales, Tomas
## Copyright: Copyright 2018, MFV
## Version: 5.0 Release
## Mmaintainer: Facultad de Informatica
## Email: trosales@linti.unlp.edu.ar
## Status: production
#######################################################

import sys
import serial
import time
import struct
import array
import datetime
from time import strftime
import random
import memcache
import os
import threading
import commands
from numpy import array
from influxdb import InfluxDBClient
from random import randint
import logging
import ConfigParser
from Queue import *

#Format of how the data is stored.
#%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s')

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

        logger_influxdb = setup_logger("influxdb_logger","influxdb_login.log")

        etot_aux = 0

        client = InfluxDBClient(host, port, user, password, dbname, ssl)

        logger_influxdb.info('Start Connect To DataBase')

        result = client.query('''select etot from Inverter where "id" = '4' order by time desc limit 1;''')

        results = list(result.get_points(measurement='Inverter'))

        for item in results:
            etot_aux = float(item['etot'])

        logger_influxdb.info('Finish geting etot data')
	    
    except Exception as e:
        logger_influxdb.error('Error: Failed to connect to database: %s', e)

    return etot_aux

def config_section_map(section, logger):
    '''
    Get configuration variable.

    The information requested by parameters 
    is obtained from the configuration file.

    Parameters
    ----------
    section : str
        Section in logger file
    logger : str
        file logger

    Returns
    -------
    Tuple
        Return array of sections

    '''
    result = {}
    options = Config.options(section)
    for option in options:
        try:
            result[option] = Config.get(section, option)
            if result[option] == -1:
            	logger.debug('config_section_map: %s', option)
        except Exception as e:
        	logger.error("config_section_map Exception on %s ", e)
        	result[option] = None
    return result

def setup_logger(name, log_file, level=logging.INFO):
    """
    Return a logger file.

    Return a logger with the specified name 
    If specified,     the name is typically 
    a dot-separated hierarchical name like 
    a, a.b or a.b.c.d.

    Parameters
    ----------
    name : str
        name for the log file
    log_file : str
        path to the log file
    level : logging.INFO
    	Logs a message with level INFO on the root logger. 
    	The arguments are interpreted as for debug().

    Returns
    -------
    logger
        Return instance logger
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    current_dir = '../../../../var/log/inverters/'
    directory_logger = current_dir
    
    if not os.path.exists(directory_logger):
		os.makedirs(directory_logger)

    handler = logging.FileHandler(directory_logger + log_file)
    handler.setLevel(level)

    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def insert_influxdb(
	host, port, dbname, user, 
	password, id, temp, vdc1,
    vdc2, vdc3, iac, vac, 
    freq, pinst, etot, wtime, 
    modo, ssl):
    '''
    Insert data in influxdb.

    It connects to influxdb with server data, 
    provided by the university. 
    A JSON is created with the structure 
    corresponding to that of the database in 
    influxdb. The insert function is executed 
    and registered in the logeo file.

    Parameters
    ----------
    host : str
        Host name
    port : int
        Number port
    dbname: str
        Database name
    user : str:
        User name
    password : str
        User password
    id : int
        Inverter identifier
    temp : float
        Inverter temperature
    vdc(1,2,3) : float
        Voltage of continuos current
    iac : float
        Alternating current
    vac : float
        Voltios of altern courrent 
    freq : float
        Inverter frequency
    pinst : str

    etot : float
        Total energy
    wtime : float
        Total Energy today
    modo : str
        Inverter operation mod
    ssl : bool
        ssl mode enabled / not enabled

    '''

    logger_influxdb = setup_logger("influxdb_logger","influxdb_login.log")

    try:
				
		client = InfluxDBClient(host, port, user, password, dbname, ssl)

		logger_influxdb.info('Start Connect To DataBase')

		#JSON configuration
		json_body = [
	    {
	        "measurement": "InverterDev",
	        "tags": {
	            "id": id,
	        },
	        "fields":  {
	            "temp": temp,
                "vdc1": vdc1,
                "vdc2": vdc2,
                "vdc3": vdc3,
                "iac": iac,
                "vac": vac,
                "freq": freq,
                "pinst": pinst,
                "etot": etot,
                "wtime": wtime,
                "modo" : modo
	        }
	    }
	    ]

   		client.write_points(json_body)

		logger_influxdb.info('Finish inserting data')
	    
    except Exception as e:
    	logger_influxdb.error('Error: Failed to connect to database: %s', e, exc_info=False)

def hand_shake(idports, logger):
    '''
    Connects to the inverter.

    Connects to the inverter using the PySerial library. 
    Read the user manual to identify the frames of this 
    communication.

    Parameters
    ----------
    idports : int
        Number port
    logger : logger
        Logger file

    Returns
    -------
    int
        Inverter identifier.

    '''

    #logger.info('Init Hand Shake For Thread: %s' % str(idports))

    '''
    port  Device name or None.
    baudrate (int) Baud rate such as 9600 or 115200 etc.
    bytesize Number of data bits. Possible values: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
    parity Enable parity checking. Possible values: PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE
    stopbits Number of stop bits. Possible values: STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
    timeout (float) Set a read timeout value.
    xonxoff (bool) Enable software flow control.
    rtscts (bool) Enable hardware (RTS/CTS) flow control.
    dsrdtr (bool) Enable hardware (DSR/DTR) flow control.
    write_timeout (float) Set a write timeout value.

    '''
    ser = serial.Serial()
    ser.port = "/dev/ttyUSB" + str(ports[idports])
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 1
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 2

    #Time for retry the hand_shake
    t_reconexion = 10

    try:
		if ser.isOpen() == 0:
			ser.open()
			logger.info('Hand Shake. Serial Port Open Correct.')
    except Exception as e:
		logger.error('Hand Shake. Fail Open Serial Port. Error %s', e)
		t = datetime.datetime.now()
		s1 = ' Error al abrir el puerto serie'
		print t,s1
		f = open(archivo_log, 'a')
		f.write(str(t)+s1+'\n')
		f.close()
		time.sleep(t_reconexion)

    
    i = 0

    while i < 3:
        while i == 0:

            logger.info('Hand Shake. Start Reading Serial Address.')

            tt = datetime.datetime.now()
            fecha = tt.strftime("%Y-%m-%d")
            tiempo = tt.strftime("%H:%M:%S")
            year = tt.strftime("%Y")
            mes = tt.strftime("%B")

            current_dir = '/home/pi/inverter_data'
            directorio = current_dir+'/'+year+'/'+mes
			
            archivo_log = directorio+'/'+fecha+'_'+'log.txt'
            archivo_parametros = directorio+'/'+fecha+'_'+'parametros.txt'

            if not os.path.exists(directorio):
				os.makedirs(directorio)

            t = datetime.datetime.now()
            print t, ' Empieza la inicializacion'	
			
            #Write Initiate	
            init_data ='AAAA010000000004000159'
            ser.write(init_data.decode("hex"))

            #Write Query
            query = 'AAAA010000000000000155'
            ser.write(query.decode("hex"))

            #Read Serial address
            serial_address = ser.read(8)
            serial_address = serial_address.encode("hex")

            if len(serial_address) == 0:
            	logger.warning('Hand Shake. Failed To Read Serial Address.')
            	t = datetime.datetime.now()
            	print t, ' Error al leer el serial address'
            	f = open(archivo_log, 'a')
            	f.write(str(t)+' Error al leer el serial address'+'\n')
            	f.close()
            	time.sleep(t_reconexion)
            else:
                try:
                	#Read Serial data.
                	data_length1 = ord(ser.read(1))
                	serial_data = ser.read(data_length1)

                	### INVERTER IDENTIFICATION ###
                	id_inversor = serial_data[0:1]
                	id_inversor = int(id_inversor,16)
                    logger.info('Identification Inverter: %s', str(id_inversor))
                	print 'El inversor es el: ', id_inversor
                	### END INVERTER IDENTIFICATION ###

                	serial_data = serial_data.encode("hex")
                	checksum1 = ser.read(2)
                	checksum1 = checksum1.encode("hex")
                	checksum1 = int(checksum1,16)
                	
                	#Verify checksum.
                	answer1 = serial_address+format(data_length1,'02x')+serial_data
                	check1_verify = sum(bytearray(answer1.decode("hex")))
                	if check1_verify == checksum1:
                		i = 1
                		t = datetime.datetime.now()
                		print t ,' Read Serial address and data OK'
                		f = open(archivo_log, 'a')
                		f.write(str(t)+' Read Serial address and data OK'+'\n')
                		f.close()
                	else:
                		t = datetime.datetime.now()
                		print t ,' Checksum error in Read Serial address and data'
                		f = open(archivo_log, 'a')
                		f.write(str(t)+' Checksum error in Read Serial address and data'+'\n')
                		f.close()
                except Exception as detail:
                	print 'Handling chacksum error:', detail
                	t = datetime.datetime.now()
                	print t ,' Error in Read Serial address and data'
			
        while i == 1:	
        	#Write Serial.
        	send_register ='AAAA0100000000010B'
        	write_serial = send_register + serial_data + '01'
        	checksum2 = sum(bytearray(write_serial.decode("hex")))
        	write_serial = write_serial + format(checksum2, '04x')
        	write_serial = write_serial.decode("hex")
        	ser.write(write_serial)
        	t = datetime.datetime.now()
        	print t, ' Write Serial OK'
        	f = open(archivo_log, 'a')
        	f.write(str(t)+' Write Serial OK'+'\n')
        	f.close()
        	
        	try:
        		#Read Acknowledge address and data.
        		ack_address = ser.read(8)
        		ack_address = ack_address.encode("hex")
        		print ack_address
        		ack_data_length = ord(ser.read(1))
        		ack_data = ser.read(ack_data_length)
        		ack_data = ack_data.encode("hex")
        		checksum3 = ser.read(2)
        		checksum3 = checksum3.encode("hex")
        		checksum3 = int(checksum3,16)
        	except:
        		i = 0
        		t = datetime.datetime.now()
        		print t, ' Error al leer el acknowledge address'
        		f = open(archivo_log, 'a')
        		f.write(str(t)+' Error al leer el acknowledge address'+'\n')
        		f.close()
        	else:					
        		#Verify checksum.
        		answer3 = ack_address + format(ack_data_length,'02x') + ack_data
        		check3_verify = sum(bytearray(answer3.decode("hex")))
        		if check3_verify == checksum3:						
        			if ack_data == serial_data:
        				i = 1
        				t = datetime.datetime.now()
        				print t, ' ack_data == serial_data'
        				f = open(archivo_log, 'a')
        				f.write(str(t)+' ack_data == serial_data'+'\n')
        				f.close()
        			else:
        				logger.info('hand_shake. Finished Correctly.')
        				i = 3
        				t = datetime.datetime.now()
        				print t, ' Inicializacion OK'
        				print '----------------------------'
        				f = open(archivo_log, 'a')
        				f.write(str(t)+' Inicializacion OK'+'\n')
        				f.write('----------------------------'+'\n')
        				f.close()		
        		else:
        			logger.error('hand_shake. Failed Reading Acknowledge Address And Data.')
        			t = datetime.datetime.now()
        			print t ,' Checksum error in Read Acknowledge address and data'
        			f = open(archivo_log, 'a')
        			f.write(str(t)+' Checksum error in Read Acknowledge address and data'+'\n')
        			f.close()

    return id_inversor

def connect_v10(args_thread):
    '''
    Obtain data from investors.

    Obtain data from investors every 3/5 minutes (configurable). 
    Then it is written to a .file file and to the tracking file. 
    Then the data obtained in the influxdb database is inserted.
    .

    Parameters
    ----------
    args_thread : Queu
        Vector of parameters

    '''

    idports = args_thread.get() 
    host = args_thread.get()
    port = args_thread.get()
    dbname = args_thread.get()
    user = args_thread.get()
    password = args_thread.get()
    ssl = args_thread.get()

    logger_thread = setup_logger('logger_thread' + str(idports),'thread_' + str(idports) + '_loging.log')

    logger_thread.info('Start Thread Number: %s ', str(idports))

    ser = serial.Serial()
    ser.port = "/dev/ttyUSB" + str(ports[idports])

    logger_thread.info('Port To Connect: /dev/ttyUSB%s', str(idports))

    '''
    port Device name or None.
    baudrate (int) Baud rate such as 9600 or 115200 etc.
    bytesize Number of data bits. Possible values: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
    parity Enable parity checking. Possible values: PARITY_NONE, PARITY_EVEN, PARITY_ODD PARITY_MARK, PARITY_SPACE
    stopbits Number of stop bits. Possible values: STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO
    timeout (float) Set a read timeout value.
    xonxoff (bool) Enable software flow control.
    rtscts (bool) Enable hardware (RTS/CTS) flow control.
    dsrdtr (bool) Enable hardware (DSR/DTR) flow control.
    write_timeout (float) Set a write timeout value.

    '''
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = 1
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 2

    logger_thread.info('Ok. Config Serial Port.')

    shared = memcache.Client(['127.0.0.1:11211'], debug = 0)

    #Inverter sampling time in seconds. 3 minutes.
    t_muestreo = 10

    #Reconnection time. 10 seconds
    t_reconexion = 10	

    while True:

        shared.set('Id', float('nan'))
        shared.set('Temp', float('nan'))
        shared.set('Vdc', float('nan'))
        shared.set('Iac', float('nan'))
        shared.set('Vac', float('nan'))
        shared.set('Freq', float('nan'))
        shared.set('Pinst', float('nan'))
        shared.set('Etot', float('nan'))

        tt = datetime.datetime.now()
        fecha = tt.strftime("%Y-%m-%d")
        tiempo = tt.strftime("%H:%M:%S")
        year = tt.strftime("%Y")
        mes = tt.strftime("%B")

        ts = time.time()

        current_dir = '/home/pi/inverter_data'
        directorio = current_dir+'/'+year+'/'+mes

        archivo_log = directorio+'/'+fecha+'_'+'log.txt'
        archivo_parametros = directorio+'/'+fecha+'_'+'parametros.txt'

        if not os.path.exists(directorio):
        	os.makedirs(directorio)
        try:
        	if ser.isOpen() == 0:
        		ser.open()
        		logger_thread.info('Ok. Serial Port Open Correct.')
        except Exception:
        	logger_thread.warning('Error. Fail Open Serial Port.')
        	t = datetime.datetime.now()
        	s1 = ' Error al abrir el puerto serie'
        	print t,s1
        	f = open(archivo_log, 'a')
        	f.write(str(t)+s1+'\n')
        	f.close()
        	time.sleep(t_reconexion)
        else:
            ser.flushInput()
            ser.flushOutput()

            logger_thread.info('Start Hand Shake.')

            id_inversor = hand_shake(idports,logger_thread)

            logger_thread.info('Finished Hand Shake.')

            tt = datetime.datetime.now()
            fecha = tt.strftime("%Y-%m-%d")
            tiempo = tt.strftime("%H:%M:%S")
            year = tt.strftime("%Y")
            mes = tt.strftime("%B")

            ts = time.time()

            current_dir = '/home/pi/inverter_data'
            directorio = current_dir+'/'+year+'/'+mes

            archivo_log = directorio+'/'+fecha+'_'+'log.txt'
            archivo_parametros = directorio+'/'+fecha+'_'+'parametros.txt'
        	
            if not os.path.exists(directorio):
                os.makedirs(directorio)
            
            while True:  
                try:					
                    #Write Request Magic command.		
                    #magic_cmd = 'AAAA010000010102000159'
                    test_cmd_1 = 'AAAA01000000000000'	
                    		
                    checksum_test = sum(bytearray(test_cmd_1.decode("hex")))			
                    test_cmd_1 = test_cmd_1 + format(checksum_test, '04x')	                
                    test_cmd_1 = test_cmd_1.decode("hex")
                    ser.write(test_cmd_1)

                    test_cmd_2 = 'AAAA01000000000000'
                    		
                    checksum_test = sum(bytearray(test_cmd_2.decode("hex")))			
                    test_cmd_2 = test_cmd_2 + format(checksum_test, '04x')	                
                    test_cmd_2 = test_cmd_2.decode("hex")
                    ser.write(test_cmd_2)

                    test_cmd_3 = 'AAAA01000001010200'
                    		
                    checksum_test = sum(bytearray(test_cmd_3.decode("hex")))			
                    test_cmd_3 = test_cmd_3 + format(checksum_test, '04x')	                
                    #print 'test cmd: ', test_cmd			
                    test_cmd_3 = test_cmd_3.decode("hex")
                    ser.write(test_cmd_3)
                    #print 'magic: ',magic_cmd
                    #ser.write(magic_cmd.decode("hex"))

                    t = datetime.datetime.now()
                    fecha=t.strftime("%Y-%m-%d")
                    tiempo=t.strftime("%H:%M:%S")

                    logger_thread.info('Start Reading Parameters.')

                    #Read data.
                    print '----------- Read Parameters -----------'
                    par_add = ser.read(8)
                    par_add = par_add.encode("hex")
                    par_data_length = ord(ser.read(1))
                    par_data = ser.read(par_data_length)
                    par_data = par_data.encode("hex")
                    par_checksum = ser.read(2)
                    par_checksum = par_checksum.encode("hex")
                    par_checksum = int(par_checksum,16)

                    logger_thread.info('Finished Reading Parameters. Correct.')
                    logger_thread.info('Start To Verify Checksum.')

                    #Verify checksum.
                    answer=par_add + format(par_data_length,'02x') + par_data
                    check_verify=sum(bytearray(answer.decode("hex")))

                    if check_verify==par_checksum:

                        logger_thread.info('Finished To Verify Checksum. Correct.')

                        ### PARAMETERS DECODE ###
                        Temp = float(int(par_data[0:4],16))/10
                        print 'Temp: ', Temp, u"\u00B0"'C'
                        logger_thread.info('Temp %s %s', Temp, u"\u00B0"'C')

                        Vdc1 = float(int(par_data[4:8],16))/10 # sirio
                        print 'Vdc1: ', Vdc1, 'V'
                        logger_thread.info('Vdc1: %s V', Vdc1)

                        Vdc2 = float(int(par_data[8:12],16))/10 # sirio
                        print 'Vdc2: ', Vdc2, 'V'
                        logger_thread.info('Vdc2: %s V', Vdc2)

                        Vdc3 = float(int(par_data[12:16],16))/10 # sirio
                        print 'Vdc3: ', Vdc3, 'V'
                        logger_thread.info('Vdc3: %s V',Vdc3)

                        Wtime = float(int(par_data[28:32],16))/100 #sirio Etotal 
                        print 'Etoday: ', Wtime, 'kWh'
                        logger_thread.info('Etoday: %s KWh', Wtime) 

                        Iac = float(int(par_data[36:40],16))/10 #sirio
                        print 'Iac: ', Iac, 'A'
                        logger_thread.info('Iac: %s A', Iac)  

                        Vac = float(int(par_data[40:44],16))/10 #sirio
                        print 'Vac: ', Vac, 'V'
                        logger_thread.info('Vac: %s V', Vac)

                        Freq = float(int(par_data[44:48],16))/100 #sirio
                        print 'Freq: ', Freq, 'Hz'
                        logger_thread.info('Freq: %s Hz')

                        Pinst = float(int(par_data[48:52],16)) # sirio
                        print 'Pac: ', Pinst, 'W'
                        logger_thread.info('Pac: %s W', Pinst)

                        Etot = float(int(par_data[56:64],16))/10 # sirio Etotal 
                        print 'Etot: ', Etot, 'kWh'
                        logger_thread.info('Etot: %s kWh', Etot)

                        #Modo = float(int(par_data[71:75],16)) 
                        #print 'Modo: ', Modo
                        #logger_thread.info('Modo: ' + Modo)

                        #INVERSOR 4
                        '''
                        if idports == 4 :
                        	etot = get_total_energy_data_influx()
                        	Wtime = etot - Etot
                            print Wtime
                        '''
						
                        logger_thread.info('Start Writing Into DataBase.')

                        #Inser data in influxDB.
                        insert_influxdb(host, port, dbname, user, password, id_inversor, Temp, Vdc1, Vdc2, Vdc3, Iac, Vac, Freq, Pinst, Etot, Wtime, ssl)	

                        logger_thread.info('Finished Writing Into DataBase. Correct.')
                        					
                        #Writing parameters.
                        f = open(archivo_parametros, 'a')
                        f.write(
                        	"{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}".format(
                        		id_inversor,
                        		fecha,
                        		tiempo,
                        		Temp,
                        		Vdc1,
                                Vdc2,
                                Vdc3,
                        		Iac,
                        		Vac,
                        		Freq,
                        		Pinst,
                        		Etot,
                        		str(Wtime) + '\n'
                        		)
                        	)
                        f.close()

                        logger_thread.info('Writing into RAM.')

                        #Send variables to RAM.
                        shared.set('id', id_inversor)	
                        shared.set('t', t)
                        shared.set('Temp', Temp)
                        shared.set('Vdc1', Vdc1)
                        shared.set('Vdc2', Vdc2)
                        shared.set('Vdc3', Vdc3)
                        shared.set('Iac', Iac)
                        shared.set('Vac', Vac)
                        shared.set('Freq', Freq)
                        shared.set('Pinst', Pinst)
                        shared.set('Etot', Etot)
                        shared.set('Etot', Wtime)

                        logger_thread.info('Writing into RAM. Correct')

                        print t

                        time.sleep(t_muestreo)
						
                    else:
                    	logger_thread.warning('Failed Checksum Verify. Checksum Error In Read Parameters.')
                    	f = open(archivo_log, 'a')
                    	f.write(str(t)+' Checksum error in Read Parameters'+'\n')
                    	f.close()
                    	break
				
                except Exception as detail1:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    print(exc_type, fname, exc_tb.tb_lineno)
                    #logger_thread.error('Error: '+ str(e1))
                    t = datetime.datetime.now()
                    s2=' Conexion perdida'
                    print t,s2
                    f = open(archivo_log, 'a')
                    f.write(str(t)+s2+'\n')
                    f.close()
                    ser.close()	
                    time.sleep(t_reconexion)
                    break

# MAIN
if __name__ == "__main__":

    logger_main = setup_logger('main',"main_login.log")

    logger_main.info('Start Program.')

    directory_config = '../../../../usr/local/sirio/'

    logger_main.info('Reading Configuration File.')
    	
    if not os.path.exists(directory_config):
    	logger_main.error('Error: Fail To Find Directory.')
    	exit()

    path_config = directory_config + 'configuration-sirio.cfg'

    Config = ConfigParser.ConfigParser() 
    Config.read(path_config)

    host = config_section_map("InfluxDB",logger_main)['host']
    user = config_section_map("InfluxDB",logger_main)['user']
    password = config_section_map("InfluxDB",logger_main)['password']
    dbname = config_section_map("InfluxDB",logger_main)['dbname']
    port = int(config_section_map("InfluxDB",logger_main)['port'])
    ssl = config_section_map("InfluxDB",logger_main)['ssl']
    amout_threads = int(config_section_map("PyConnect",logger_main)['threads'])

    if ssl == 'True':
        ssl = True
    else:
        ssl = False 


    logger_main.info('Reading Configuration File. Ok.')

    args_thread = Queue()

    idps = commands.getstatusoutput('python -m serial.tools.list_ports | grep "USB" | cut -c 12')	

    if idps[0] == 0:
        ports = str(idps[1]).split('\n')
        if ((len(ports) == 1) or ('No' in ports)):
        	print 'Error: no hay puertos serie RS232 conectados.'
        	logger_main.error('Error: Not Ports Serie RS232 Found.')
        else:
        	print 'Ok: se han reconocidos puertos conectados.'
        	logger_main.info('Ok. Ports Found.')
        	N_THREADS = amout_threads
        	print N_THREADS
        	threads = []
        	for i in range(N_THREADS):
        		args_thread.put(i+1)
        		args_thread.put(host)
        		args_thread.put(port)
        		args_thread.put(dbname)
        		args_thread.put(user)
        		args_thread.put(password)
        		args_thread.put(ssl)
        		
        		t = threading.Thread(target=connect_v10,args=(args_thread,))
        		threads.append(t)
        		t.start()
        	logger_main.info('Ok. Created Threads.')
        	
    else:
    	print "Error: " + str(idps[0]) + ". Hay un error puerto serie"
    	#logger_main.error('Error: Port Serie.' + str(idps[0]))
