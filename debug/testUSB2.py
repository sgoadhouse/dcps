
import usb.core
import usb.util
from usb.backend import libusb1
import sys
from fnmatch import fnmatch

VENDOR_ID = 0x1AB1
PRODUCT_ID = 0x0E11
#@@@#SERIAL_NUM = 'DP8B153600499'
SERIAL_NUM = None
DATA_SIZE = 1

def find_devices(
    vendor=None, product=None, serial_number=None, custom_match=None, **kwargs
):
    """Find connected USB devices matching certain keywords.

    Wildcards can be used for vendor, product and serial_number.

    :param vendor: name or id of the vendor (manufacturer)
    :param product: name or id of the product
    :param serial_number: serial number.
    :param custom_match: callable returning True or False that takes a device as only input.
    :param kwargs: other properties to match. See usb.core.find
    :return:
    """
    kwargs = kwargs or {}
    attrs = {}
    if isinstance(vendor, str):
        attrs["manufacturer"] = vendor
    elif vendor is not None:
        kwargs["idVendor"] = vendor

    if isinstance(product, str):
        attrs["product"] = product
    elif product is not None:
        kwargs["idProduct"] = product

    if serial_number:
        attrs["serial_number"] = str(serial_number)

    if attrs:

        def cm(dev):
            if custom_match is not None and not custom_match(dev):
                return False
            for attr, pattern in attrs.items():
                try:
                    value = getattr(dev, attr)
                except (NotImplementedError, ValueError):
                    return False
                if not fnmatch(value.lower(), pattern.lower()):
                    return False
            return True

    else:
        cm = custom_match

    ## ADDED THIS to make sure using libusb in this test example
    be = libusb1.get_backend()

    return usb.core.find(backend=be, find_all=True, custom_match=cm, **kwargs)

#@@@#device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

devices = list(
    find_devices(VENDOR_ID, PRODUCT_ID, SERIAL_NUM, None)
    #@@@#return usb.core.find(find_all=True, custom_match=cm, **kwargs)
)

if not devices:
    raise ValueError("No device found.")
elif len(devices) > 1:
    desc = "\n".join(str(dev) for dev in devices)
    raise ValueError(
        "{} devices found:\n{}\nPlease narrow the search"
        " criteria".format(len(devices), desc)
    )

usb_dev = devices[0]

try:
    if usb_dev.is_kernel_driver_active(0):
        usb_dev.detach_kernel_driver(0)
except (usb.core.USBError, NotImplementedError):
    pass

try:
    usb_dev.set_configuration()
except usb.core.USBError as e:
    raise Exception("failed to set configuration\n %s" % e)

try:
    usb_dev.set_interface_altsetting()
except usb.core.USBError:
    pass

cfg = usb_dev.get_active_configuration()

for cfg in usb_dev:
    sys.stdout.write(str(cfg.bConfigurationValue) + '\n')
    
