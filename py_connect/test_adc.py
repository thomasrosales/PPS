from ADC import ADC

def adc():
    '''
    Summary line.

    Extended description of function.

    Parameters
    ----------
    arg1 : int
        Description of arg1
    arg2 : str
        Description of arg2

    Returns
    -------
    int
        Description of return value

    '''

    CONN = False

    while CONN == False:
        try:
            adc=ADC()
            print 'OK ADC INSTANCE.s'
            CONN = True
            sampling_period = 10
            while True:
                try:
                    temp_panels = adc.get_temperatura()
                    rad_panels = adc.get_radiacion()
                    time.sleep(sampling_period)
                except Exception as e:
                    print 'ADC ERROR: ', e
        except Exception as e:
            print 'EROOOOOORORROR: ', e
# MAIN
if __name__ == "__main__":
    adc()