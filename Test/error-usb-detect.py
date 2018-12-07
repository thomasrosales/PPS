import sys
import serial, time, struct, array
import os
import threading
import commands
from numpy import array


idps = commands.getstatusoutput('python -m serial.tools.list_ports | grep "USB" | cut -c 12')
if idps[0] == 0:
	    ports = str(idps[1]).split('\n')
	    if (len(ports) <= 18) or ('No' in ports):
	    	print 'Error: no hay puertos serie RS232 conectados.'
	    else:
	    	print 'Ok: se han reconocidos puertos serie RS232 conectados.'
	    	
	    	'''
	    	N_THREADS = int(sys.argv[1])	#N_THREADS is a parameter of the program.
	    	print N_THREADS	#Print thread nums.
	    	
	    	threads = []	#Array of threads.
	    	for i in range(N_THREADS):
	    		t = threading.Thread(target=connect_v10,args=(i+1,))	#Create a thread.
	    		threads.append(t)	#Wait for all the threads to be created.
	    		t.start()	#Threads are starts.
	    	'''
else:
	print "Erro: " + str(idps[0]) + "Hay un error puerto serie"