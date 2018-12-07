import ConfigParser
import time

###*
#Obtiene la variable de configuracion
def ConfigSectionMap(section):
    result = {}
    #obtiene la seccion
    options = Config.options(section)
    for option in options:
        try:
            result[option] = Config.get(section, option)
            if result[option] == -1:
                DebugPrint("skip: %s" % option) #logger
        except Exception as e:
            print("Exception on %s!" % e) #logger
            result[option] = None
    return result

###*
#Main generar desde el thread
if __name__ == "__main__":
    while True:
        try:
            Config = ConfigParser.ConfigParser() 
            Config.read("configuration-sirio.cfg") #ruta relativa
            host = ConfigSectionMap("InfluxDB")['host']
            threads = ConfigSectionMap("PyConnect")['threads']
            print "InfluxDB Host:  %s. Py Connect Thread: %s" % (host, threads)
        except Exception as e:
            print("Exception on %s!" % e) #logger
            time.sleep(10)