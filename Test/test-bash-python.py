#!/usr/bin/python

import commands
from numpy import array

#obtiene los id de los puertos series conectados en la raspebery
idps = commands.getstatusoutput('python -m serial.tools.list_ports | grep "USB" | cut -c 12')

if idps[0] == 0:
    #divide el string de la segunda posicion de la lista en dos posiciones de un arreglo
    ports = str(idps[1]).split('\n')
    if ports[0] == 'no ports found':
    	print 'Error: no hay puertos conectados.'
    else:
    	print 'Ok: se han reconocidos puertos conectados'
else:
    print "Erro: " + str(idps[0]) + "Hay un error puerto serie"




#imprime el contenido del arreglo de puertos
print ports[0]
#print ports[1]
#print ports[2]




    
