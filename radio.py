import subprocess, select, os, re, time
import power

lpath = "/usr/local/lib:."
if os.getenv("LD_LIBRARY_PATH") != None:
    lpath = os.getenv("LD_LIBRARY_PATH") + ":" + lpath
os.putenv("LD_LIBRARY_PATH", lpath)

def decode_str(s):
    r = re.compile("([^= ]+)=([^=, ]+)")
    matches = r.findall(s)

    settings = {}

    for match in matches:
        vname = match[0]
        val = match[1]

        settings[vname] = val

    return settings

def wait_start():
    # Wait for xbd to start:
    while not os.path.exists("/tmp/xbee"):
        time.sleep(0.1)

    xbout = subprocess.Popen(["./xbout"],
                             stdout = subprocess.PIPE)
    fifo = xbout.stdout.fileno()
    lstate = 0
    text = ""
    start_found = False

    # Wait for the START signal
    while True:
        if select.select([fifo], [], [], 0.5) == ([],[],[]):
            # Flash the LED to indicate we're waiting
            lstate = lstate ^ 8
            power.setleds(lstate)
        else:
            # Read the output
            text += os.read(fifo, 1)

            if start_found and text[-1] == "\n":
                text = text[6:-1]
                print "Received START:", text
                return decode_str(text)
            else:
                if text[0:6] != "START:"[0:len(text)]:
                    text = ""
                elif text[0:6] == "START:":
                    start_found = True
