import pyudev

def list_usb_devices(model):
    "Create a sorted list of USB devices of the given type"
    def _udev_compare_serial(x, y):
        """Compare two udev serial numbers"""
        return cmp(x["ID_SERIAL_SHORT"],
                   y["ID_SERIAL_SHORT"])

    udev = pyudev.Context()
    devs = list(udev.list_devices( subsystem = "tty",
                                   ID_MODEL = model ))
    # Sort by serial number
    devs.sort( cmp = _udev_compare_serial )
    return devs
