from uldaq import (get_daq_device_inventory, DaqDevice, InterfaceType,
                   AiInputMode, Range, AInFlag)
from math import pow
import time

class ADC:
    def get_temperatura(self):
        # Get a list of available DAQ devices
        devices = get_daq_device_inventory(InterfaceType.USB)
        # Create a DaqDevice Object and connect to the device
        daq_device = DaqDevice(devices[0])
        daq_device.connect()
        # Get AiDevice and AiInfo objects for the analog input subsystem
        ai_device = daq_device.get_ai_device()
        ai_info = ai_device.get_info()
        data = ai_device.a_in(0, AiInputMode.SINGLE_ENDED, Range.BIP10VOLTS, AInFlag.DEFAULT)
        temp = data*-10
        #print'Temperatura ', round(temp, 2), "C"
        daq_device.disconnect()
        daq_device.release()
        return round(temp,2)
    def get_radiacion(self):
        # Get a list of available DAQ devices
        devices = get_daq_device_inventory(InterfaceType.USB)
        # Create a DaqDevice Object and connect to the device
        daq_device = DaqDevice(devices[0])
        daq_device.connect()
        # Get AiDevice and AiInfo objects for the analog input subsystem
        ai_device = daq_device.get_ai_device()
        ai_info = ai_device.get_info()
        data = ai_device.a_in(1, AiInputMode.SINGLE_ENDED, Range.BIP10VOLTS, AInFlag.DEFAULT)
        r = data/ (80.86*pow(10, -6))
        daq_device.disconnect()
        daq_device.release()
        return round(r,2)