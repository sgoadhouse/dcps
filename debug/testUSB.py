
import usb.core
import usb.util
import sys

# got these using the command lsusb -vv
VENDOR_ID = 0x1AB1
PRODUCT_ID = 0x0E11
DATA_SIZE = 1

device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

#@@@#print(device.is_kernel_driver_active(0))

# was it found?
if device is None:
    raise ValueError('USB Device not found')

try:
    # set the active configuration. With no arguments, the first
    # configuration will be the active one
    device.set_configuration()
except usb.core.USBError as e:
    raise Exception("failed to set configuration\n %s" % e)

cfg = device.get_active_configuration()

for cfg in device:
    sys.stdout.write(str(cfg.bConfigurationValue) + '\n')
    
#@@@#device.read(0x81, 255, 1000000)
