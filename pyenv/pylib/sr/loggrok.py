"""Module to modify stdout and stderr to use Windows newlines

This can be run like so:
% python -m sr.loggrok something.py

The result is that something.py is run after importing this module, and hence
with the desired stdout and stderr modifications.
"""
import sys

class AddCRFlusher(object):
    def __init__(self, wrap):
        self.wrap = wrap

    def write(self, s):
        s = s.replace("\n", "\r\n")
        self.wrap.write(s)

        if "\n" in s:
            self.wrap.flush()

    def __getattr__(self, name):
        "Defer attribute look-ups to the wrapped file object"
        return getattr( self.wrap, name )

    def __setattr__(self, name, val):
        "Defer attribute setting to the wrapped file object"
        if name == "wrap":
            self.__dict__[name] = val
            return

        setattr( self.wrap, name, val )

if __name__ == "__main__":
    if not sys.stdout.isatty():
        """tty's don't require this treatment"""

        writer = AddCRFlusher(sys.stdout)
        sys.stderr = sys.stdout = writer

    ### Now pass execution onto the actual thing:
    prog = sys.argv[1]
    # Remove ourselves from the args
    sys.argv = sys.argv[1:]

    execfile(prog, { "__file__": prog })
