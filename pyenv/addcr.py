
class AddCRWriter(object):
    '''
    Writer class that replaces any and all \ns in the strings with \r\n.
    Written such that it can wrap any other writer class.
    '''

    _actual = None

    def __init__(self, actual):
        self._actual = actual

    def write(self, string):
        string = string.replace('\n', '\r\n')
        self._actual.write(string)

    def __getattr__(self, name):
        "Defer attribute look-ups to the wrapped file object"
        return getattr( self._actual, name )

    def __setattr__(self, name, val):
        "Defer attribute setting to the wrapped file object"
        if name == "_actual":
            self.__dict__[name] = val
            return

        setattr( self._actual, name, val )
