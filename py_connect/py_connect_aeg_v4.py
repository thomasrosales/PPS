#!/usr/bin/python

#######################################################
## Inverters monitorings of the Facultad de Informatica
#######################################################
## Author: Rosales, Tomas
## Copyright: Copyright 2018, MFV
## Version: 4.0 Release
## Mmaintainer: Facultad de Informatica
## Email: trosales@linti.unlp.edu.ar
## Status: production
#######################################################

import sys
import serial, time, struct, array
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

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s') #Format of how the data is stored.

###*
#Obtiene la variable de configuracion
def ConfigSectionMap(section, logger):
    result = {}
    options = Config.options(section)
    for option in options:
        try:
            result[option] = Config.get(section, option)
            if result[option] == -1:
            	logger.debug('ConfigSectionMap: ' + option)
        except Exception as e:
        	logger.error("ConfigSectionMap Exception on %s, " % e)
        	result[option] = None
    return result

###*
# THIS FUNCTION IS FOR LOGS FILES
def setupLogger(name, log_file, level=logging.INFO):
    logger = logging.getLogger(name)	#Create the log file.
    logger.setLevel(level)				#Level of the log file.

    current_dir =  '/home/pi/MFV/py_connect'	#Path this documents.
    directory_logger = current_dir + '/.log/'	#Path of the month folder.
    
    if not os.path.exists(directory_logger):	#Check if the folder exist.
		os.makedirs(directory_logger)

    handler = logging.FileHandler(directory_logger + log_file)	#Create the file handler.
    handler.setLevel(level)		#Level of the handler file.

    handler.setFormatter(formatter)	#Create a logging format.

    logger.addHandler(handler)	#Add the handlers to the logger.
    return logger 	#Return the logger file.

###*
# THIS FUNCTION IS FOR INSERT DATA IN INFLUX DATABASE
def insertIntoInfluxDB(host, port, dbname, user, password, id, temp, vdc, iac, vac, freq, pinst, etot, wtime, modo, ssl):

	logger_influxdb = setupLogger("influxdb_logger","influxdb_login.log")	#Create a log file of InfluxDB.

	try:
				
		client = InfluxDBClient(host, port, user, password, dbname, ssl)	#Influx client where database is stored.

		logger_influxdb.info('Start Connect To DataBase') #Write in the log file that the BD start.

		#Start of the json_body to insert the database.
		json_body = [
	    {
	        "measurement": "InverterDev",
	        "tags": {
	            "id": id,
	        },
	        "fields":  {
	            "temp": temp,
	            "vdc": vdc,
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
	    #End of the json_body to insert the database.

   		client.write_points(json_body)

		logger_influxdb.info('Finish inserting data')	#Write in the log file that write data finish.
	    
	except Exception as e:
		logger_influxdb.error('Error: Failed to connect to database: %s', e, exc_info=False)	#Write in the log file that connect to DB fail.

### THIS FUNCTION IS FOR CONNECT TO THE INVERTER
def handShake(idports, logger):

	logger.info('Init Hand Shake For Inverter: ' + str(idports))	#Write in the log file that init handshake.
	#This log file corresponds to the handshake of each thread.

	### SERIAL PORT CONFIGURATION FOR FIRST HANDSHAKE ###
	ser = serial.Serial()
	ser.port = "/dev/ttyUSB" + str(ports[idports])
	print "El puerto a inicializar es: " + ser.port + "\n"
	ser.baudrate = 9600					#Number of boud rate in bps.
	ser.bytesize = serial.EIGHTBITS		#Number of bits per bytes.
	ser.parity = serial.PARITY_NONE		#Set parity check: no parity.
	ser.stopbits = serial.STOPBITS_ONE	#Number of stop bits.
	ser.timeout = 1						#Non-block read.
	ser.xonxoff = False					#Disable software flow control.
	ser.rtscts = False					#Disable hardware (RTS/CTS) flow control.
	ser.dsrdtr = False					#Disable hardware (DSR/DTR) flow control.
	ser.writeTimeout = 2				#Timeout for write.
	### END SERIAL PORT CONFIGURATION ###
	
	#Check that the serial port is open.
	try:
		if ser.isOpen() == 0:	#If port serial is not open, open it.
			ser.open()	#Open port serial.
			logger.info('Hand Shake. Serial Port Open Correct.')	#Write the log file that serial port is ok.
	except Exception:
		logger.warning('Hand Shake. Fail Open Serial Port.')	#Write the log file that serial port is not ok.
		t = datetime.datetime.now()	#Date and time of the computer.
		s1 = ' Error al abrir el puerto serie'
		print t,s1
		f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
		f.write(str(t)+s1+'\n')		#Write the archivo_log.
		f.close()					#Close the archvio_log.
		time.sleep(t_reconexion)	#Sleep for x seconds.

	t_reconexion = 10	#Time for retry the handshake.

	i = 0

	while i < 3:
		
		while i == 0:
			
			logger.info('Hand Shake. Start Reading Serial Address.')	#Write the log file that read serial address start.

			#Determinate the day to generate folders per year and month.
			tt = datetime.datetime.now()	#Date and time of the computer.
			fecha = tt.strftime("%Y-%m-%d")
			tiempo = tt.strftime("%H:%M:%S")
			year = tt.strftime("%Y")
			mes = tt.strftime("%B")
			
			current_dir = '/home/pi/inverter_data'	#Path of this script.
			directorio = current_dir+'/'+year+'/'+mes 	#Path of the folder.
			
			#Files to generate.
			archivo_log = directorio+'/'+fecha+'_'+'log.txt'	#Archivo_log similar to the log file.
			archivo_parametros = directorio+'/'+fecha+'_'+'parametros.txt'	#Archivo_parametros data file.
			
			#Verify if exist that folder. If not, to creted.
			if not os.path.exists(directorio):
				os.makedirs(directorio)
			
			t = datetime.datetime.now()	#Date and time of the computer.
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
				logger.warning('Hand Shake. Failed To Read Serial Address.')	#Write the log file that read serial addres fail.
				t = datetime.datetime.now()	#Date and time of the computer.
				print t, ' Error al leer el serial address'
				f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
				f.write(str(t)+' Error al leer el serial address'+'\n')	#Write the archivo_log.
				f.close()	#Close the archivo_log.
				time.sleep(t_reconexion)	#Sleep for x seconds.
			else:
				try:
					#Read Serial data.
					data_length1 = ord(ser.read(1))
					serial_data = ser.read(data_length1)

					### INVERTER IDENTIFICATION ###
					id_inversor = serial_data[0:1]
					id_inversor = int(id_inversor,16)
					print 'El inversor es el: ', id_inversor	#Print inversor ID.
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
						t = datetime.datetime.now()	#Date and time of the computer.
						print t ,' Read Serial address and data OK'
						f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
						f.write(str(t)+' Read Serial address and data OK'+'\n')	#Write the archivo_log.
						f.close()	#Close the archivo_log.
					else:
						t = datetime.datetime.now()	#Date and time of the computer.
						print t ,' Checksum error in Read Serial address and data'
						f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
						f.write(str(t)+' Checksum error in Read Serial address and data'+'\n')	#Write the archivo_log.
						f.close()	#Close the archivo_log.
				except Exception as detail:
					print 'Handling chacksum error:', detail
					t = datetime.datetime.now()	#Date and time of the computer.
					print t ,' Error in Read Serial address and data'
			
		while i == 1:	
			#Write Serial.
			send_register ='AAAA0100000000010B'
			write_serial = send_register + serial_data + '01'
			checksum2 = sum(bytearray(write_serial.decode("hex")))
			write_serial = write_serial + format(checksum2, '04x')
			write_serial = write_serial.decode("hex")
			ser.write(write_serial)
			t = datetime.datetime.now() #Date and time of the computer.
			print t, ' Write Serial OK'
			f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
			f.write(str(t)+' Write Serial OK'+'\n')	#Write the archivo_log.
			f.close()	#Close the archivo_log.
			
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
				t = datetime.datetime.now()	#Date and time of the computer.
				print t, ' Error al leer el acknowledge address'
				f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
				f.write(str(t)+' Error al leer el acknowledge address'+'\n')	#Write the archivo_log.
				f.close()	#Close the archivo_log.
			else:					
				#Verify checksum.
				answer3 = ack_address + format(ack_data_length,'02x') + ack_data
				check3_verify = sum(bytearray(answer3.decode("hex")))
				if check3_verify == checksum3:						
					if ack_data == serial_data:
						i = 1 #Send back the Write Serial.
						t = datetime.datetime.now() #Date and time of the computer.
						print t, ' ack_data == serial_data'
						f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
						f.write(str(t)+' ack_data == serial_data'+'\n')	#Write the archivo_log.
						f.close()	#Close the archivo_log.
					else:
						logger.info('HandShake. Finished Correctly.')	#Write the log file that hanshake finish ok.
						i = 3
						t = datetime.datetime.now() #Date and time of the computer.
						print t, ' Inicializacion OK'
						print '----------------------------'
						f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
						f.write(str(t)+' Inicializacion OK'+'\n')	#Write the archivo_log.
						f.write('----------------------------'+'\n')	#Write the archivo_log.
						f.close()	#Close the archivo_log.			
				else:
					logger.error('HandShake. Failed Reading Acknowledge Address And Data.')	#Write the log file that read ACK address and data filed.
					t = datetime.datetime.now()	#Date and time of the computer.
					print t ,' Checksum error in Read Acknowledge address and data'
					f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
					f.write(str(t)+' Checksum error in Read Acknowledge address and data'+'\n')	#Write the archivo_log.
					f.close()	#Close the archivo_log.

	return id_inversor	#This fuction return the inverter ID.

###*
# FUNCTION RUNNING EACH THREAD, EACH THREAD REPRESENTS AN INVERTER
def connect_v10(args_thread):

	idports = args_thread.get() 
	host = args_thread.get()
	port = args_thread.get()
	dbname = args_thread.get()
	user = args_thread.get()
	password = args_thread.get()

	logger_thread = setupLogger('logger_thread' + str(idports),'thread_' + str(idports) + '_loging.log')	#Create a log file of each thread.

	logger_thread.info('Start Thread Number: ' + str(idports))	#Write the log file thread the number of thread.

	print 'Thread: %s' % idports	#Print the thread num.
	ser = serial.Serial()
	ser.port = "/dev/ttyUSB" + str(ports[idports])
    
    #Print the serial port.
	logger_thread.info('Port To Connect: ' + ser.port)	#Write the log file thread that port is to connect.
	print "En el connect el puerto es: " + ser.port + "\n"

	### SERIAL PORT CONFIGURATION FOR EACH THREAD ###
	ser.baudrate = 9600					#Number of boud rate in bps.
	ser.bytesize = serial.EIGHTBITS		#Number of bits per bytes.
	ser.parity = serial.PARITY_NONE 	#Set parity check: no parity.
	ser.stopbits = serial.STOPBITS_ONE 	#Number of stop bits.
	ser.timeout = 1						#Non-block read.
	ser.xonxoff = False 				#Disable software flow control.
	ser.rtscts = False 					#Disable hardware (RTS/CTS) flow control.
	ser.dsrdtr = False					#Disable hardware (DSR/DTR) flow control.
	ser.writeTimeout = 2				#Timeout for write.
	### END SERIAL PORT CONFIGURATION ###

	logger_thread.info('Ok. Config Serial Port.')	#Write the log file thread that config serial port is ok.

	shared = memcache.Client(['127.0.0.1:11211'], debug = 0)

	t_muestreo = 5 		#Inverter sampling time in seconds.
	t_reconexion = 10	#Reconnection time.

	while True:  #This constructs an infinite loop.

		#Parametros initialization.
		### CONFIGURATION ###
		shared.set('Id', float('nan'))
		shared.set('Temp', float('nan'))
		shared.set('Vdc', float('nan'))
		shared.set('Iac', float('nan'))
		shared.set('Vac', float('nan'))
		shared.set('Freq', float('nan'))
		shared.set('Pinst', float('nan'))
		shared.set('Etot', float('nan'))

		#Determinate the day to generate folders per year and month.
		tt = datetime.datetime.now()	#Date and time of the computer.
		fecha = tt.strftime("%Y-%m-%d")
		tiempo = tt.strftime("%H:%M:%S")
		year = tt.strftime("%Y")
		mes = tt.strftime("%B")

		ts = time.time()

		current_dir = '/home/pi/inverter_data'	#Path of this script.
		directorio = current_dir+'/'+year+'/'+mes 	#Path of the folder.

		#Files to generate.
		archivo_log = directorio+'/'+fecha+'_'+'log.txt'	#Archivo_log similar to the log file.
		archivo_parametros = directorio+'/'+fecha+'_'+'parametros.txt'	#Archivo_parametros data file.
		
		#Verify if exist that folder. If not, create it.
		if not os.path.exists(directorio):
			os.makedirs(directorio)
		try:
			if ser.isOpen() == 0:	#If port serial is not open, open it.
				ser.open()	#Open port serial.
				logger_thread.info('Ok. Serial Port Open Correct.')	#Write the log file thread that serial port open is ok.
		except Exception:
			logger_thread.warning('Error. Fail Open Serial Port.')	#Write the log file thread that serial port open is fail.
			t = datetime.datetime.now()	#Date and time of the computer.
			s1 = ' Error al abrir el puerto serie'
			print t,s1
			f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
			f.write(str(t)+s1+'\n')	#Write the archivo_log.
			f.close()	#Close the archivo_log.
			time.sleep(t_reconexion) #Sleep for x seconds.
		else:
			ser.flushInput()
			ser.flushOutput()

			logger_thread.info('Start Hand Shake.')	#Write the log file thread that handshake start.

			id_inversor = handShake(idports,logger_thread)	#For eahc inversor make the handshake.

			logger_thread.info('Finished Hand Shake.')	#Write the log file thread that handshake finish.
			
			#Determinate the day to generate folders per year and month.
			tt = datetime.datetime.now()	#Date and time of the computer.
			fecha = tt.strftime("%Y-%m-%d")
			tiempo = tt.strftime("%H:%M:%S")
			year = tt.strftime("%Y")
			mes = tt.strftime("%B")

			ts = time.time()
			
			current_dir = '/home/pi/inverter_data'	#Path of this script.
			directorio = current_dir+'/'+year+'/'+mes 	#Path of the folder.
			
			#Files to generate.
			archivo_log = directorio+'/'+fecha+'_'+'log.txt'	#Archivo_log similar to the log file.
			archivo_parametros = directorio+'/'+fecha+'_'+'parametros.txt'	#Archivo_parametros data file.
			
			#Verify if exist that folder. If not, create it.
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
					
					test_cmd_2 = 'AAAA01000000000000'	#Original
							
					checksum_test = sum(bytearray(test_cmd_2.decode("hex")))			
					test_cmd_2 = test_cmd_2 + format(checksum_test, '04x')	                
					test_cmd_2 = test_cmd_2.decode("hex")
					ser.write(test_cmd_2)
					
					test_cmd_3 = 'AAAA01000001010200'	#Original
							
					checksum_test = sum(bytearray(test_cmd_3.decode("hex")))			
					test_cmd_3 = test_cmd_3 + format(checksum_test, '04x')	                
					#print 'test cmd: ', test_cmd			
					test_cmd_3 = test_cmd_3.decode("hex")
					ser.write(test_cmd_3)
					#print 'magic: ',magic_cmd
					#ser.write(magic_cmd.decode("hex"))
					
					#Time.
					t = datetime.datetime.now()	#Date and time of the computer.
					fecha=t.strftime("%Y-%m-%d")
					tiempo=t.strftime("%H:%M:%S")

					logger_thread.info('Start Reading Parameters.')	#Write the log file thread that read parameters start.
			
					#Read data.
					print '----------- Read Parameters -----------'
					par_add = ser.read(8) #Parameters address.
					par_add = par_add.encode("hex")
					par_data_length = ord(ser.read(1)) #Parameter data length.
					par_data = ser.read(par_data_length) #Read parameter data.
					par_data = par_data.encode("hex")
					par_checksum = ser.read(2)
					par_checksum = par_checksum.encode("hex")
					par_checksum = int(par_checksum,16)

					logger_thread.info('Finished Reading Parameters. Correct.')	#Write the log file thread that read parameters finish.
					logger_thread.info('Start To Verify Checksum.')				#Write the log file thread that verify checksum start.

					#Verify checksum.
					answer=par_add + format(par_data_length,'02x') + par_data
					check_verify=sum(bytearray(answer.decode("hex")))

					if check_verify==par_checksum:

						logger_thread.info('Finished To Verify Checksum. Correct.')	#Write the log file thread that verify checksum finish.
					
						
						### PARAMETERS DECODE ###
						Temp = float(int(par_data[0:4],16))/10
						print 'Temp: ', Temp, u"\u00B0"'C'
						
						Vdc = float(int(par_data[8:12],16))/10 # sirio
						print 'Vdc: ', Vdc, 'V'
				
						Iac = float(int(par_data[12:16],16))/10 #sirio
						print 'Iac: ', Iac, 'A'
				
						Vac = float(int(par_data[16:20],16))/10 #sirio
						print 'Vac: ', Vac, 'V'
				
						Freq = float(int(par_data[20:24],16))/100 #sirio
						print 'Freq: ', Freq, 'Hz'
				
						Pinst = float(int(par_data[24:28],16)) # sirio
						print 'Pac: ', Pinst, 'W'
				
						par1 = int(par_data[28:32],16)
						#print 'par1: ', par1, '(not used, always 0xFFFF)'
						
						Etot = float(int(par_data[32:40],16))/10 # sirio Etotal 
						print 'Etot: ', Etot, 'kWh'

						#INVERSOR 4
				
						Wtime = float(int(par_data[4:8],16))/100 #sirio Etotal 
						print 'Etoday: ', Wtime, 'kWh' 
				
						Modo = float(int(par_data[48:52],16)) 
						print 'Modo: ', Modo
				
						Faults = par_data[52:84]
						print 'Faults: ', Faults
						
						Par2 = par_data[44:48]
						print '44:48: ', Par2
						
						Par3 = par_data[40:44]
						print '40:44: ', Par3
						
						Par4 = par_data[32:36]
						print '44:48: ', Par4
						
						logger_thread.info('Start Writing Into DataBase.')	#Write the log file thread that insert in database start.

						#Inser data in influxDB.
						insertIntoInfluxDB(host, port, dbname, user, password, id_inversor, Temp, Vdc, Iac, Vac, Freq, Pinst, Etot, Wtime, Modo, True)	

						logger_thread.info('Finished Writing Into DataBase. Correct.')	#Write the log file thread that insert in database finish.
											
						#Writing parameters.
						### TERCERA PRUEBA ###
						f = open(archivo_parametros, 'a')	#This file is another log file but for parameters (If not exist, crate it).
						f.write(
							"{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10},{11},{12}".format(
								id_inversor,
								fecha,
								tiempo,
								Temp,
								Vdc,
								Iac,
								Vac,
								Freq,
								Pinst,
								Etot,
								Wtime,
								Modo,
								str(Faults)+'\n'
								)
							)	#Write the archivo_parametros.
						f.close()	#Close the archivo_parametros.
						
						#Send variables to RAM.
						shared.set('id', id_inversor)	
						shared.set('t', t)
						shared.set('Temp', Temp)
						shared.set('Vdc', Vdc)
						shared.set('Iac', Iac)
						shared.set('Vac', Vac)
						shared.set('Freq', Freq)
						shared.set('Pinst', Pinst)
						shared.set('Etot', Etot)
						shared.set('Modo', Modo)
						
						print t
						
						time.sleep(t_muestreo) #Sleep for x seconds.
						
					else:
						logger_thread.warning('Failed Checksum Verify. Checksum Error In Read Parameters.')	#Write the log file thread that checksum fail.
						f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
						f.write(str(t)+' Checksum error in Read Parameters'+'\n')	#Write the archivo_log.
						f.close()	#Close the archivo_log.
						break
				
				except Exception as e1:
                                        print 'Error', str(e1)
					t = datetime.datetime.now()	#Date and time of the computer.
					s2=' Conexion perdida'
					print t,s2
					f = open(archivo_log, 'a')	#This file is another log file (If not exist, crate it).
					f.write(str(t)+s2+'\n')	#Write the archivo_log.
					f.close()	#Close the archivo_log.
					ser.close()	
					time.sleep(t_reconexion)	#Sleep for x seconds.
					break

###*
# MAIN
if __name__ == "__main__":

	logger_main = setupLogger('main',"main_login.log")	#Create a log file of main.

	logger_main.info('Start Program.')	#Write the log file main that program start.

	directory_config = '../../../../usr/local/sirio/'
		
	if not os.path.exists(directory_config):
		logger_main.error('Error: Fail To Find Directory.')
		exit()

	path_config = directory_config + 'configuration-sirio.cfg'

	Config = ConfigParser.ConfigParser() 
	Config.read(path_config) #ruta relativa /usr/lib 

	host = ConfigSectionMap("InfluxDB",logger_main)['host']
	user = ConfigSectionMap("InfluxDB",logger_main)['user']
	password = ConfigSectionMap("InfluxDB",logger_main)['password']
	dbname = ConfigSectionMap("InfluxDB",logger_main)['dbname']
	port = int(ConfigSectionMap("InfluxDB",logger_main)['port'])
	ssl = ConfigSectionMap("InfluxDB",logger_main)['ssl']
	amout_threads = ConfigSectionMap("PyConnect",logger_main)['threads']

	
	if ssl == 'True':
		ssl = True
	else:
		ssl = False 

	args_thread = Queue()

	idps = commands.getstatusoutput('python -m serial.tools.list_ports | grep "USB" | cut -c 12')	
	#This line executes a command line statement to obtain all connected serial ports.

	if idps[0] == 0:
	    ports = str(idps[1]).split('\n')
	    if ((len(ports) == 1) or ('No' in ports)):
	    	print 'Error: no hay puertos serie RS232 conectados.'
	    	logger_main.error('Error: Not Ports Serie RS232 Found.')	#Write the log file main that the ports not found.
	    else:
	    	print 'Ok: se han reconocidos puertos conectados.'
	    	logger_main.info('Ok. Ports Found.')	#Write the log file main that the ports founds.
	    	N_THREADS = int(amout_threads) #N_THREADS is a parameter of the program.
	    	print N_THREADS	#Print thread nums.
	    	threads = []	#Array of threads.
	    	for i in range(N_THREADS):
	    		args_thread.put(i+1)
	    		args_thread.put(host)
	    		args_thread.put(port)
	    		args_thread.put(dbname)
	    		args_thread.put(user)
	    		args_thread.put(password)
	    		args_thread.put(ssl)
	    		
	    		t = threading.Thread(target=connect_v10,args=(args_thread,))	#Create a thread.
	    		threads.append(t)	#Wait for all the threads to be created.
	    		t.start()	#Threads are starts.
	    	logger_main.info('Ok. Created Threads.')	#Write the log file main that the threads were created ok.
	    	
	else:
		print "Error: " + str(idps[0]) + ". Hay un error puerto serie"
		logger_main.error('Error: Port Serie.' + str(idps[0]))	#Write the log file main that port serial is not ok.
