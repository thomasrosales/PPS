from uldaq import (get_daq_device_inventory, DaqDevice, InterfaceType,
                   AiInputMode, Range, AInFlag)
from math import pow
import time

try:
    # Get a list of available DAQ devices
    devices = get_daq_device_inventory(InterfaceType.USB)
    # Create a DaqDevice Object and connect to the device
    daq_device = DaqDevice(devices[0])
    daq_device.connect()
    # Get AiDevice and AiInfo objects for the analog input subsystem
    ai_device = daq_device.get_ai_device()
    ai_info = ai_device.get_info()

    while True:
        data = ai_device.a_in(0, AiInputMode.DIFFERENTIAL, Range.BIP10VOLTS, AInFlag.DEFAULT)
        temp = data*-10
#temp=-3.9257018186617643*-10
        print'Temperatura ', round(temp, 2), "C"

        data = ai_device.a_in(1, AiInputMode.SINGLE_ENDED, Range.BIP10VOLTS, AInFlag.DEFAULT)
        r = data/ (80.86*pow(10, -6))
#r = 0.06733283546054736/ (80.86*(pow(10, -6)))
        print 'Radiacion ', round(r, 2), "W/m2"
        time.sleep(5)

    daq_device.disconnect()
    daq_device.release()

except ULException as e:
    print('\n', e)  # Display any error messages
