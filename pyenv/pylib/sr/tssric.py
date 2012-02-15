"pysric but with some threadlocal storage layered ontop"
import pysric, threading

class TSSricDevice(object):
    """A wrapper around a SRIC device that uses a threadlocal sricd connection"""
    def __init__(self, sricman, address, devtype ):
        self._address = address
        self._devtype = devtype

        self._sricman = sricman
        self._tl = threading.local()

        # A lock for transactions on this device
        self.trans_lock = threading.Lock()

    def _pop_myself(self):
        if "dev" not in self._tl.__dict__:
            self._tl.dev = self._sricman.get_addr_nts( self._address )

    def __getattr__(self, name):
        "Provide access to the underlying Sric device"
        self._pop_myself()
        return getattr( self._tl.dev, name )

    def txrx( self, *args, **kw ):
        self._pop_myself()
        return self._tl.dev.txrx( *args, **kw )

class LockableDev(TSSricDevice):
    """A TSSricDevice with a lock for its users to use

    Some devices have transactions that require multiple SRIC
    operations to complete.  The lock that this class provides is
    intended to be used for this purpose."""

    def __init__(self, sricman, address, devtype):
        TSSricDevice.__init__(self, sricman, address, devtype)

        # The lock itself
        self.lock = threading.Lock()

    def txrx(self, *args, **kw):
        """Wrapper around txrx with check that lock is locked

        Note that this check does not assess whether the current
        thread has the lock,  just that it has been locked.  This
        should catch anything attempting to access the device
        elsewhere."""

        assert self.lock.locked()
        return super( LockableDev, self ).txrx( *args, **kw )

class SricCtxMan(object):
    """Class for storing/managing one sric context per thread"""
    def __init__(self):
        self.store = threading.local()
        self._devices_populated = False

    def get(self):
        "Return a pysric context for use in this thread"
        if "ctx" not in self.store.__dict__:
            self.store.ctx = pysric.PySric()

        return self.store.ctx

    def get_addr_nts(self, addr):
        """Return the SricDevice instance for the given address for this thread
        (returned object is not thread-safe)"""

        if "addr" not in self.store.__dict__:
            "Construct a dictionary of the available addresses"
            self.store.addr = {}
            ps = self.get()

            for devs in ps.devices.values():
                for dev in devs:
                    assert dev.address not in self.store.addr
                    self.store.addr[dev.address] = dev

        return self.store.addr[addr]

    @property
    def devices(self):
        "Get the devices dictionary -- dict of TSSricDevices"

        if not self._devices_populated:
            "Populate the device list"
            self._devices = {}

            ps = self.get()
            for devclass, devlist in ps.devices.iteritems():
                self._devices[devclass] = []

                if devclass in ( pysric.SRIC_CLASS_JOINTIO,
                                 pysric.SRIC_CLASS_POWER ):
                    "This type of device requires locking for transactions"
                    wrapper = LockableDev
                else:
                    wrapper = TSSricDevice

                for dev in devlist:
                    d = wrapper( self, dev.address, dev.type )
                    self._devices[devclass].append(d)

        return self._devices
                                     
