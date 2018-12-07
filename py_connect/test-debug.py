import sys
import os


DEBUG = True

def debug_print(s):
    if DEBUG:
        print s

try:
    ### PARAMETERS DECODE ###
    Temp = float(1000)/10
    print 'Temp: ' , Temp , u"\u00B0"'C'

except Exception as e:
	exc_type, exc_obj, exc_tb = sys.exc_info()
	fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
	print(exc_type, fname, exc_tb.tb_lineno)