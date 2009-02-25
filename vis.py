import select
import os
import time
import subprocess
import logging
from events import Event
from poll import Poll

class VisionEvent(Event):
    class Blob:
        def __init__(self, centrex, centrey, width, height, mass, colour):
            self.centrex = float(centrex) / 3.2
            self.centrey = float(centrey) / 2.4
            self.mass = int(mass)
            self.colour = int(colour)
            self.width = int(width)
            self.height = int(height)
    
    def __init__(self):
        Event.__init__(self)
        self.blobs = []

    def addblob(self, centrex, centrey, width, height, mass, colour):
        self.blobs.append(self.Blob(centrex, centrey, width, height, mass, colour))

class VisProc:
    def __init__(self):
	sp = subprocess.Popen("./hueblobs", stdout=subprocess.PIPE,
            stdin=subprocess.PIPE)
	self.fifo = sp.stdout.fileno()
	self.command = sp.stdin
	self.reqnum = 0
	self.text = ""
	self.reqlist = []

    def make_req(self):

	#commands queued to hueblobs as it waits on stdin. If we add
	#multiple lines, multiple requests

	self.command.write(str(self.reqnum) + "\n")
	self.ournum = self.reqnum
	self.reqnum += 1
	return self.ournum


    def poll_req(self, num):
	#Have we had a response for req 'num'?
	for req in self.reqlist:
	    if req.num == num:
		return req

	#No; so read more data from hueblobs

        while True:
            if select.select([self.fifo], [], [], 0) == ([], [], []):
		#No more data right now
		break;
                    
            self.text += os.read(self.fifo, 1)

	if self.text.find("BLOBS\n") == -1 :
	    #Not at the end yet
	    return None

	strlist = self.text.split("BLOBS\n", 1)
	self.text = strlist[1]
        lines = strlist[0].strip().split('\n')
     
        if len(lines) == 0:
            logging.error("hueblobs returned nothing")
        else:
	    reqtext = lines.pop()
	    reqtext.rstrip('\n')

            event = VisionEvent()
	    event.num = int(reqtext)
            for line in lines:
                if line != "":
                    info = line.split(",")
                    event.addblob(info[0], info[1], info[2], info[3], info[4],
                            info[5])

	    self.text = ""
	    if num == event.num:
		return event
	    else:
		self.reqlist.append(event)
		return None

print "Starting vision system"
vis_proc = VisProc()

class vision(Poll):
    def __init__(self):
	Poll.__init__(self)
	self.our_req_num = vis_proc.make_req()

    def eval(self):
	return vis_proc.poll_req(self.our_req_num)

