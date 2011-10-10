from hw.motor import motor
from hw.power import power
from hw.vis import vision, VISION_HEIGHT, VISION_WIDTH
from hw.jointio import io, queryio as _queryio
from hw.servo import servo
from hw.colours import *

from poll import And, Or

class query:
    io = _queryio

