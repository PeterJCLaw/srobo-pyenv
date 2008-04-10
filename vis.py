import select
import os
import time
import subprocess
import logging
from events import Event

class VISEvent(Event):
    class Blob:
        def __init__(self, centrex, centrey, width, height, mass, colour):
            self.centrex = float(centrex) / 3.2
            self.centrey = float(centrey) / 2.4
            self.mass = int(mass)
            self.colour = int(colour)
            self.width = int(width)
            self.height = int(height)
    
    def __init__(self):
        Event.__init__(self, vispoll)
        self.blobs = []

    def addblob(self, centrex, centrey, width, height, mass, colour):
        self.blobs.append(self.Blob(centrex, centrey, width, height, mass, colour))

def vispoll():
    sp = subprocess.Popen("./hueblobs", stdout=subprocess.PIPE,
            stdin=subprocess.PIPE)
    fifo = sp.stdout.fileno()
    command = sp.stdin

    yield None #End of setup

    event = VISEvent()

    while True:
        if sp.poll() != None:
            logging.error("Camera failed")
            while True:
                yield None

        command.write("\n")
        text = ""
        while True:
            if select.select([fifo], [], [], 0) == ([], [], []):
                if text[-6:] == "BLOBS\n":
                    text = text[:-6]
                    break

                if sp.poll() != None:
                    logging.error("Camera failed")
                    while True:
                        yield None
                    
            text += os.read(fifo, 1)

        lines = text.strip().split('\n')
     
        if len(lines) == 0:
            yield None
        else:
            event = VISEvent()
            for line in lines:
                if line != "":
                    info = line.split(",")
                    event.addblob(info[0], info[1], info[2], info[3], info[4],
                            info[5])
            yield event
