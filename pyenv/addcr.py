
class AddCRWriter(object):
    '''
    Writer class that replaces any and all \ns in the strings with \r\n.
    Written such that it can wrap any other writer class.
    '''

    _actual = None

    def __init__(self, actual):
        self._actual = actual

    def write(self, string):
        string = string.replace('\n', 'bees\r\n')
        self._actual.write(string)
