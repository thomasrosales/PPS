import logging
import os

formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

logger = logging.getLogger("test.log")
logger.setLevel(logging.INFO)

current_dir = '/.log/'
directory_logger = current_dir

if not os.path.exists(directory_logger):
    os.makedirs(directory_logger)

handler = logging.FileHandler(".log/test.log")
handler.setLevel(logging.INFO)

handler.setFormatter(formatter)

logger.addHandler(handler)

Freq = float(int(10000))/100 #sirio
print 'Freq: ', Freq, 'Hz'
logger.info('Freq: %s Hz', Freq)

Pinst = float(int(10000)) # sirio
print 'Pac: ', Pinst, 'W'
logger.info('Pac: %s W', Pinst)

Etot = float(int(10000))/10 # sirio Etotal 
print 'Etot: ', Etot, 'kWh'
logger.info('Etot: %s kWh', Etot)


logger2 = logging.getLogger('test.log')

logger2.info('TODO BIE')

