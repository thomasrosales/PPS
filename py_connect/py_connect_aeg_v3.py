#!/usr/bin/python

#######################################################
## Inverters monitorings of the Facultad de Informatica
#######################################################
## Author: Rosales, Tomas
## Copyright: Copyright 2018, MFV
## Version: 3.0 Release
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


#initialization and open port
# 1. None: wait forever, block call
# 2. 0: non-blocking mode, return inmediatly
# 3. x, x is bigger than 0, float allowed, timeout block call

def handShake(idports):
	ser = serial.Serial()
	ser.port = "/dev/ttyUSB" + str(ports[idports])
	print "En iniciailizar el puerto es: " + ser.port + "\n"
	ser.baudrate = 9600
	ser.bytesize = serial.EIGHTBITS
	ser.parity = serial.PARITY_NONE
	ser.stopbits = serial.STOPBITS_ONE
	ser.timeout = 1
	ser.xonxoff = False
	ser.rtscts = False
	ser.dsrdtr = False
	ser.writeTimeout = 2

	try:
		if ser.isOpen()==0:
			ser.open()
	except Exception:
		t=datetime.datetime.now()
		s1=' Error al abrir el puerto serie'
		print t,s1
		f = open(archivo_log, 'a')
		f.write(str(t)+s1+'\n')
		f.close()
		time.sleep(t_reconexion) # sleep for xx seconds

	#Tiempo para reintentar el handshake
	t_reconexion = 10

	i=0		
	while i<3:
		
		while i==0:
			
			#Determino el dia para generar las carpetas por anio y mes
			tt = datetime.datetime.now()
			fecha=tt.strftime("%Y-%m-%d")
			tiempo=tt.strftime("%H:%M:%S")
			year=tt.strftime("%Y")
			mes=tt.strftime("%B")
			
			#path de este escript
			current_dir='/home/pi/inverter_data'
			#path de la carpeta por mes
			directorio=current_dir+'/'+year+'/'+mes
			#archivos a generar
			archivo_log=directorio+'/'+fecha+'_'+'log.txt'
			archivo_parametros=directorio+'/'+fecha+'_'+'parametros.txt'
			
			#verifico si existe la carpeta correspondiente
			if not os.path.exists(directorio):
				os.makedirs(directorio)
			
			t=datetime.datetime.now()
			print t, ' Empieza la inicializacion'
			#f = open(archivo_log, 'a')
			#f.write(str(t)+' Empieza la inicializacion'+'\n')
			#f.close()	
			
			#Write Initiate	
			init_data ='AAAA010000000004000159'
			ser.write(init_data.decode("hex"))
			
			#Write Query
			query = 'AAAA010000000000000155'
			ser.write(query.decode("hex"))

			#Read Serial address

			serial_address = ser.read(8)
			serial_address = serial_address.encode("hex")


			#MIRAR TRAMA DE HANDSHAKE --> BYTE 9 PARA ADELANTE ES EL IDENTIFICADOR
			serial_address = ser.read(10)
			serial_address = serial_address.encode("hex")

			id_inversor = serial_address[9:10] #Byte correspondiente al identificador del inversor. (31, 32, 33 y 34 (Hex))
				
			#IMPRIMIR EL IDENTIFICADOR DEL INVERSOR
			id_inversor = id_inversor.encode("hex")
			print "El inversor es el numero: " + id_inversor


			id_inversor = int(id_inversor,16)

			id_inversor = float(int(id_inversor))

			print 'Inversor: ', id_inversor

			##########FIN IDENTIFICAR INVERSOR

			serial_address = serial_address[0:9]


			if len(serial_address)==0:
				t=datetime.datetime.now()
				print t, ' error al leer el serial address'
				f = open(archivo_log, 'a')
				f.write(str(t)+' error al leer el serial address'+'\n')
				f.close()
				time.sleep(t_reconexion)
			else:
				try:
					#Read Serial data  
					data_length1 = ord(ser.read(1))
					serial_data = ser.read(data_length1)
					
					#IDENTIFICAR INVERSOR

					id_inversor = serial_data[0:1].enconde("hex")
					id_inversor = int(id_inversor,16)

					print 'El inversor es el: ', id_inversor

					#FIN IDENTIFICAR INVERSOR

					serial_data = serial_data.encode("hex")

					checksum1=ser.read(2)
					checksum1=checksum1.encode("hex")
					checksum1=int(checksum1,16)
					#verifico checksum
					answer1=serial_address+format(data_length1,'02x')+serial_data
					check1_verify=sum(bytearray(answer1.decode("hex")))
					if check1_verify==checksum1:
						i=1
						t=datetime.datetime.now()
						print t ,' Read Serial address and data OK'
						f = open(archivo_log, 'a')
						f.write(str(t)+' Read Serial address and data OK'+'\n')
						f.close()
					else:
						t=datetime.datetime.now()
						print t ,' Checksum error in Read Serial address and data'
						f = open(archivo_log, 'a')
						f.write(str(t)+' Checksum error in Read Serial address and data'+'\n')
						f.close()
				except Exception as detail:
					print 'Handling chacksum error:', detail
					t=datetime.datetime.now()
					print t ,' Error in Read Serial address and data'
					
			
		while i==1:	
			#Write Serial
			send_register ='AAAA0100000000010B'
			write_serial = send_register + serial_data + '01'
			checksum2 = sum(bytearray(write_serial.decode("hex")))
			write_serial = write_serial + format(checksum2, '04x')
			write_serial = write_serial.decode("hex")
			ser.write(write_serial)
			t=datetime.datetime.now()
			print t, ' Write Serial OK'
			f = open(archivo_log, 'a')
			f.write(str(t)+' Write Serial OK'+'\n')
			f.close()
			
			try:
				# Read Acknowledge address and data
				ack_address=ser.read(8)
				ack_address = ack_address.encode("hex")
				print ack_address
				ack_data_length = ord(ser.read(1))
				ack_data=ser.read(ack_data_length)
				ack_data=ack_data.encode("hex")
				checksum3=ser.read(2)
				checksum3=checksum3.encode("hex")
				checksum3=int(checksum3,16)
			except:
				i=0 #lo mando al inicio de nuevo
				t=datetime.datetime.now()
				print t, ' error al leer el acknowledge address'
				f = open(archivo_log, 'a')
				f.write(str(t)+' error al leer el acknowledge address'+'\n')
				f.close()
			else:					
				#verifico checksum
				answer3=ack_address + format(ack_data_length,'02x') + ack_data
				check3_verify=sum(bytearray(answer3.decode("hex")))
				if check3_verify==checksum3:						
					if ack_data == serial_data:
						i=1 # manda de nuevo el Write Serial
						t=datetime.datetime.now()
						print t, ' ack_data == serial_data'
						f = open(archivo_log, 'a')
						f.write(str(t)+' ack_data == serial_data'+'\n')
						f.close()
					else:
						i=3
						t=datetime.datetime.now()
						print t, ' inicializacion OK'
						print '----------------------------'
						f = open(archivo_log, 'a')
						f.write(str(t)+' inicializacion OK'+'\n')
						f.write('----------------------------'+'\n')
						f.close()							
				else:
					t=datetime.datetime.now()
					print t ,' Checksum error in Read Acknowledge address and data'
					f = open(archivo_log, 'a')
					f.write(str(t)+' Checksum error in Read Acknowledge address and data'+'\n')
					f.close()
	return id_inversor


###*
#Funcion que ejecuta cada thread, cada thread representa un inversor
def connect_v10(idports):
    
    print 'hilo n: %s' % idports
    ser = serial.Serial()
    ser.port = "/dev/ttyUSB" + str(ports[idports])
    #imprimir serial port
    print "En el connect el puerto es: " + ser.port + "\n"
    ser.baudrate = 9600
    ser.bytesize = serial.EIGHTBITS #number of bits per bytes
    ser.parity = serial.PARITY_NONE #set parity check: no parity
    ser.stopbits = serial.STOPBITS_ONE #number of stop bits
    ser.timeout = 1		#non-block read
    ser.xonxoff = False 	#disable software flow control
    ser.rtscts = False 	#disable hardware (RTS/CTS) flow control
    ser.dsrdtr = False	#disable hardware (DSR/DTR) flow control
    ser.writeTimeout =2	#timeout for write

    shared = memcache.Client(['127.0.0.1:11211'], debug=0)

    t_muestreo=5 #tiempo de muestreo del inversor en segundos
    t_reconexion=10

    while True:  # This constructs an infinite loop
	
	#inicializo los parametros
	##############################
	##########CONFIGURACION#######
	##############################
	shared.set('Id', float('nan'))
	shared.set('Temp', float('nan'))
	shared.set('Vdc', float('nan'))
	shared.set('Iac', float('nan'))
	shared.set('Vac', float('nan'))
	shared.set('Freq', float('nan'))
	shared.set('Pinst', float('nan'))
	shared.set('Etot', float('nan'))
	
	#Determino el dia para generar las carpetas por anio y mes
	tt = datetime.datetime.now()
	fecha=tt.strftime("%Y-%m-%d")
	tiempo=tt.strftime("%H:%M:%S")
	year=tt.strftime("%Y")
	mes=tt.strftime("%B")

	#Epoch timestamp, me facilita a mi para algunas cosas.
	ts = time.time()
	
	#path de este escript
	current_dir='/home/pi/inverter_data'
	#path de la carpeta por mes
	directorio=current_dir+'/'+year+'/'+mes
	#archivos a generar
	archivo_log=directorio+'/'+fecha+'_'+'log.txt'
	archivo_parametros=directorio+'/'+fecha+'_'+'parametros.txt'
	
	#verifico si existe la carpeta correspondiente
	if not os.path.exists(directorio):
		os.makedirs(directorio)
		
	try:
		if ser.isOpen()==0:
				ser.open()
	except Exception:
		t=datetime.datetime.now()
		s1=' Error al abrir el puerto serie'
		print t,s1
		f = open(archivo_log, 'a')
		f.write(str(t)+s1+'\n')
		f.close()
		time.sleep(t_reconexion) # sleep for xx seconds
	else:
		
		ser.flushInput()
		ser.flushOutput()

		id_inversor = handShake(idports)
		
		#Determino el dia para generar las carpetas por anio y mes
		tt = datetime.datetime.now()
		fecha=tt.strftime("%Y-%m-%d")
		tiempo=tt.strftime("%H:%M:%S")
		year=tt.strftime("%Y")
		mes=tt.strftime("%B")

		#Epoch timestamp, me facilita a mi para algunas cosas.
		#Lo pongo de nuevo porque el resto de las cosas tambien aparecen repetidos aca
		ts = time.time()
		
		#path de este escript
		current_dir='/home/pi/inverter_data'
		#path de la carpeta por mes
		directorio=current_dir+'/'+year+'/'+mes
		#archivos a generar
		archivo_log=directorio+'/'+fecha+'_'+'log.txt'
		archivo_parametros=directorio+'/'+fecha+'_'+'parametros.txt'
		
		#verifico si existe la carpeta correspondiente
		if not os.path.exists(directorio):
			os.makedirs(directorio)

		
		while True:  
			try:
								
				# Write Request Magic command			
				#magic_cmd = 'AAAA010000010102000159'
				test_cmd_1 = 'AAAA01000000000000'	
						
				checksum_test = sum(bytearray(test_cmd_1.decode("hex")))			
				test_cmd_1 = test_cmd_1 + format(checksum_test, '04x')	                
				test_cmd_1 = test_cmd_1.decode("hex")
				ser.write(test_cmd_1)
				
				test_cmd_2 = 'AAAA01000000000000'	#original
						
				checksum_test = sum(bytearray(test_cmd_2.decode("hex")))			
				test_cmd_2 = test_cmd_2 + format(checksum_test, '04x')	                
				test_cmd_2 = test_cmd_2.decode("hex")
				ser.write(test_cmd_2)
				
				test_cmd_3 = 'AAAA01000001010200'	#original
						
				checksum_test = sum(bytearray(test_cmd_3.decode("hex")))			
				test_cmd_3 = test_cmd_3 + format(checksum_test, '04x')	                
				#print 'test cmd: ', test_cmd			
				test_cmd_3 = test_cmd_3.decode("hex")
				ser.write(test_cmd_3)
				#print 'magic: ',magic_cmd			
				#ser.write(magic_cmd.decode("hex"))
				
				# Time
				t = datetime.datetime.now()
				fecha=t.strftime("%Y-%m-%d")
				tiempo=t.strftime("%H:%M:%S")
		
				# Read data
				print '----------- Read Parameters -----------'
				par_add=ser.read(8) # parameters address
				par_add=par_add.encode("hex")
				
				par_data_length = ord(ser.read(1)) #parameter data length
				par_data=ser.read(par_data_length) #read parameter data
				par_data=par_data.encode("hex")
				par_checksum=ser.read(2)
				par_checksum=par_checksum.encode("hex")
				par_checksum=int(par_checksum,16)
				#verifico checksum
				answer=par_add + format(par_data_length,'02x') + par_data
				check_verify=sum(bytearray(answer.decode("hex")))
				if check_verify==par_checksum:
				
					
					# Parameters decode
					

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
					
					
										
					# Writing parameters
					
					#################################################
					########TERCERA PRUEBA###########################
					#################################################
					f = open(archivo_parametros, 'a')
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
						)
					f.close()
					
					# Send variables to RAM	
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
					
					time.sleep(t_muestreo) # sleep for xx seconds
					
				else:
					#poner NaN a los parametros
					f = open(archivo_log, 'a')
					f.write(str(t)+' Checksum error in Read Parameters'+'\n')
					f.close()
					break
			
			except Exception:
				t=datetime.datetime.now()
				s2=' Conexion perdida'
				print t,s2
				f = open(archivo_log, 'a')
				f.write(str(t)+s2+'\n')
				f.close()
				ser.close()
				time.sleep(t_reconexion)
				break

        
if len(sys.argv[1:]) == 0:
	print 'Error de parametros. Falta cantidad de threads.'
else:

	idps = commands.getstatusoutput('python -m serial.tools.list_ports | grep "USB" | cut -c 12')

	if idps[0] == 0:
	    ports = str(idps[1]).split('\n')
	    if ports[0] == 'no ports found':
	    	print 'Error: no hay puertos conectados.'
	    else:
	    	print 'Ok: se han reconocidos puertos conectados.'
	    	N_THREADS = int(sys.argv[1])
	    	print N_THREADS
	    	threads = []
	    	for i in range(N_THREADS):
	    		t = threading.Thread(target=connect_v10,args=(i+1,))
	    		threads.append(t)
	    		t.start()
	else:
		print "Error: - " + str(idps[0]) + " - Hay un error puerto serie."
