import subprocess, select, os, re
import power

def decode_str(s):
    r = re.compile("([^= ]+)=([^= ]+)")
    matches = r.findall(s)

    settings = {}

    for match in matches:
        vname = match[0]
        val = match[1]

        settings[vname] = val

    return settings

def wait_start():
        xbout = subprocess.Popen(["./xbout"],
                                 stdout = subprocess.PIPE)
        fifo = xbout.stdout.fileno()
        lstate = 0
        text = ""
        start_found = True

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
                    text = text[7:-1]
                    return decode_str(text)
                else:
                    if text[-6:] == "START:":
                        start_found = True
