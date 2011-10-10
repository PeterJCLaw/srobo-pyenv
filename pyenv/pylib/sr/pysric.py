import os
from ctypes import *

# Magic device addresses
SRIC_MASTER_DEVICE = 0
SRIC_BROADCAST = -2
SRIC_NO_DEVICE = -1

# Device classes
SRIC_CLASS_POWER = 1
SRIC_CLASS_MOTOR = 2
SRIC_CLASS_JOINTIO = 3
SRIC_CLASS_SERVO = 4
SRIC_CLASS_PCSRIC = 5

sric_class_strings = { SRIC_CLASS_POWER: "POWER",
                       SRIC_CLASS_MOTOR: "MOTOR",
                       SRIC_CLASS_JOINTIO: "JOINTIO",
                       SRIC_CLASS_SERVO: "SERVO",
                       SRIC_CLASS_PCSRIC: "PCSRIC",
                       SRIC_MASTER_DEVICE: "MASTER_DEVICE",
                       SRIC_BROADCAST: "BROADCAST",
                       SRIC_NO_DEVICE: "NO_DEVICE" }

class SricErrorNoSuchAddress(Exception):
    "No such remote address"
    pass

class SricErrorNoSendNote(Exception):
    "Cannot send notifications"
    pass

class SricErrorBadPayload(Exception):
    "Payload length is greater than SRIC_MAX_PAYLOAD_SIZE"
    pass

class SricErrorSricd(Exception):
    "Could not connect to sricd"
    pass

class SricErrorLoop(Exception):
    "Cannot send to self"
    pass

class SricErrorTimeout(Exception):
    "Request timed out"
    pass

class SricErrorBroadcast(Exception):
    "Cannot listen on broadcast address"
    pass

# Lookup table for SRIC error codes
sric_errors = [ None,           # SRIC_ERROR_NONE
                SricErrorNoSuchAddress,
                SricErrorNoSendNote,
                SricErrorBadPayload,
                SricErrorSricd,
                SricErrorLoop,
                SricErrorTimeout,
                SricErrorBroadcast ]

class SricDevice(Structure):
    _fields_ = [("address", c_int), ("type", c_int)]

    def __repr__(self):
        if self.type in sric_class_strings:
            t = sric_class_strings[self.type]
        else:
            t = str(self.type)

        return "SricDevice( address=%i, type=%s )" % (self.address, t)

    def txrx(self, data, timeout = -1):
        "Transmit the given data"
        return self.pysric.txrx( self.address, data, timeout )

class SricFrame(Structure):
    _fields_ = [("address", c_int), ("note", c_int),
            ("payload_length", c_int),
            ("payload", c_ubyte * 64)]

    def __repr__(self):
        if self.payload_length:
            d = "data: " + "".join(["%2.2x" % s for s in self.payload[:self.payload_length]])
        else:
            d = "No data payload"
        return "SricFrame( addr=%i, %s )" % (self.address, d)

class PySric(object):
    def __init__(self):
        self._load_lib()
        self.sric_ctx = self.libsric.sric_init()

        # Indexes are device classes
        self.devices = {}
        tmpdev = None
        while True:
            tmpdev = self.libsric.sric_enumerate_devices(self.sric_ctx, tmpdev)
            if cast(tmpdev, c_void_p).value == None:
                break

            dev = tmpdev[0]
            if dev.type not in self.devices:
                self.devices[dev.type] = []

            dev.pysric = self
            self.devices[dev.type].append(dev)

    def _load_lib(self):
        "Load the library and set up how to use it"

        libsric = None
        # Look in our directory first, then the specified search path
        # Ideally, this would ask the dynamic linker where to find it
        # (and allow override with an environment variable)
        for d in [ os.getenv( "PYSRIC_LIBDIR", "" ),
                   os.path.dirname( __file__ ),
                   "./" ]:
            if d == "":
                continue

            p = os.path.join( d, "libsric.so" )
            if os.path.exists(p):
                libsric = cdll.LoadLibrary(p)
                break

        if libsric == None:
            raise Exception( "pysric: libsric.so not found" )

        # sric_context sric_init( void )
        libsric.sric_init.argtypes = []
        libsric.sric_init.restype = c_void_p

        # void sric_quit( sric_context ctx )
        libsric.sric_quit.argtypes = [c_void_p]
        libsric.sric_quit.restype = None

        # const sric_device* sric_enumerate_devices( sric_context ctx,
        #                                            const sric_device* device )
        libsric.sric_enumerate_devices.argtypes = [c_void_p, c_void_p]
        libsric.sric_enumerate_devices.restype = POINTER(SricDevice)

        # int sric_tx( sric_context ctx, const sric_frame* frame )
        libsric.sric_tx.argtypes = [c_void_p, POINTER(SricFrame)]
        libsric.sric_tx.restype = c_int

        # int sric_poll_rx( sric_context ctx,
        #                   sric_frame* frame,
        #                   int timeout )
        libsric.sric_poll_rx.argtypes = [c_void_p, POINTER(SricFrame), c_int]
        libsric.sric_poll_rx.restype = c_int

        # sric_error sric_get_error(sric_context ctx)
        libsric.sric_get_error.argtypes = [c_void_p]
        libsric.sric_get_error.restype = c_int

        self.libsric = libsric

    def __del__(self):
        self.libsric.sric_quit(self.sric_ctx)

    def txrx(self, address, data, timeout=-1):
        txframe = SricFrame()
        txframe.address = address
        # This should always be -1
        txframe.note = -1

        assert len(data) < 64
        txframe.payload_length = len(data)

        for i in range(0, len(data)):
            "Fill the data in"
            txframe.payload[i] = c_ubyte(data[i])

        rxframe = SricFrame()

        r = self.libsric.sric_tx(self.sric_ctx, txframe)
        if r:
            raise sric_errors[ self.libsric.sric_get_error(self.sric_ctx) ]

        r = self.libsric.sric_poll_rx(self.sric_ctx, rxframe, -1)
        if r:
            raise sric_errors[ self.libsric.sric_get_error(self.sric_ctx) ]

        resp = [int(rxframe.payload[i]) for i in range(0,rxframe.payload_length)]
        return resp
