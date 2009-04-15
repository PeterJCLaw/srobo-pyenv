"The coroutines that manage starting their code :-)"
import power
import addhack
from colours import *
from games import *

def button_monitor():
    led_state = 1

    # We have to import the user code here, and catch any new coroutines
    print "Button pressed... loading code"
    import robot
    newc = list(addhack.get_coroutines())
    print "User robot code import succeeded"

    while not power.getbutton():
        power.setleds(0,led_state)
        yield 0.5
        led_state ^= 1

    power.setbutton()
    power.setservopower(1)
    power.setmotorpower(1)

    addhack.add_queued()
    addhack.add_coroutine( robot.main, color = RED, game = GOLF )

def xbee_monitor():
    while True:
        yield 1000
