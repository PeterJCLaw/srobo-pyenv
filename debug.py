import os.path
import subprocess

class DebugOutput:
    def __init__(self, filename):
        self.file = open(filename, "at")

    def flush(self):
        pass

    def write(self, str):
        try:
            if self.xbeepresent():
                self.send(str)

            self.file.write( str )
        except:
            pass

    def xbeepresent(self):
        return os.path.exists("/tmp/xbee")

    def send(self, str):
        for x in range(0, len(str), 200):
            subprocess.Popen(["./xbeesend", str[x:x+200]])
            subprocess.wait()
