from hw.motor import motor
from hw.power import power
from hw.vis import vision
from hw.jointio import io, queryio as _queryio
from hw.servo import servo
from hw.colours import *

from poll import And, Or, TimePoll

class query:
    timeout = TimePoll
    io = _queryio

from time_event import timeout
from addhack import add_coroutine, coroutine

