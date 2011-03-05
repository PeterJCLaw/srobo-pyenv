from hw.motor import motor
from hw.power import power
from hw.vis import vision
from hw.colours import *

from poll import And, Or, TimePoll

class query:
    timeout = TimePoll

from hw.jointio import io
from addhack import add_coroutine, coroutine

